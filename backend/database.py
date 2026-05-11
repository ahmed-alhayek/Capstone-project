
"""
Database Manager — MongoDB Operations

=============================================
Handles all database operations:
- User accounts (register/login)
- Chat messages with emotion data
- Session summaries
- Emotion history per user
- Password reset tokens
"""

import os
from datetime import datetime, timedelta
from pymongo import MongoClient, DESCENDING
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))


class DatabaseManager:
    """
    Manages all MongoDB collections for the Mental Health Companion.

    Collections:
    ├── users           → registered accounts
    ├── messages        → every chat message + emotion data
    ├── sessions        → session summaries per user
    └── password_resets → one-time password reset tokens
    """

    def __init__(self):
        mongo_url = os.getenv("MONGO_URL")
        if not mongo_url:
            raise ValueError("❌ MONGO_URL not found in .env file")

        try:
            self.client = MongoClient(mongo_url, serverSelectionTimeoutMS=5000)
            self.client.admin.command('ping')
        except ConnectionFailure:
            raise ConnectionError("❌ Cannot connect to MongoDB. Is it running?")

        self.db              = self.client['mental_health_companion']
        self.users           = self.db['users']
        self.messages        = self.db['messages']
        self.sessions        = self.db['sessions']
        self.password_resets = self.db['password_resets']

        # Create indexes for faster queries
        self.users.create_index('email',    unique=True)
        self.users.create_index('username', unique=True)
        self.messages.create_index('user_id')
        self.sessions.create_index('user_id')
        self.password_resets.create_index('token_hash', unique=True)
        # TTL index — MongoDB auto-deletes documents whose expires_at < now
        self.password_resets.create_index('expires_at', expireAfterSeconds=0)

        print("✅ MongoDB connected!")

    # ── USER OPERATIONS ───────────────────────────────────────────────────────

    def create_user(self, username: str, email: str, hashed_password: bytes) -> str:
        """Creates a new user account. Returns the new user's ID as a string."""
        user = {
            'username':   username,
            'email':      email,
            'password':   hashed_password,
            'created_at': datetime.utcnow()
        }
        result = self.users.insert_one(user)
        return str(result.inserted_id)

    def find_user_by_email(self, email: str) -> dict:
        """Finds and returns a user document by email. Returns None if not found."""
        return self.users.find_one({'email': email})

    def find_user_by_username(self, username: str) -> dict:
        """Finds and returns a user document by username. Returns None if not found."""
        return self.users.find_one({'username': username})

    def find_user_by_id(self, user_id: str) -> dict:
        """Finds a user by their ObjectId string. Returns None if not found."""
        from bson import ObjectId
        try:
            return self.users.find_one({'_id': ObjectId(user_id)})
        except Exception:
            return None

    # ── MESSAGE OPERATIONS ────────────────────────────────────────────────────

    def save_message(self, user_id: str, role: str,
                     content: str, emotions: dict = None,
                     score: float = None) -> None:
        """
        Saves a single chat message to the database.

        Parameters:
        - user_id  : logged-in user's ID string
        - role     : 'user' or 'assistant'
        - content  : message text
        - emotions : emotion probabilities dict (user messages only)
        - score    : mental health score 0-100 (user messages only)
        """
        message = {
            'user_id':   user_id,
            'role':      role,
            'content':   content,
            'emotions':  emotions,
            'score':     score,
            'timestamp': datetime.utcnow()
        }
        self.messages.insert_one(message)

    def get_user_messages(self, user_id: str, limit: int = 50) -> list:
        """Returns the most recent messages for a user."""
        cursor = self.messages.find(
            {'user_id': user_id},
            {'_id': 0, 'role': 1, 'content': 1,
             'emotions': 1, 'score': 1, 'timestamp': 1}
        ).sort('timestamp', DESCENDING).limit(limit)

        return list(reversed(list(cursor)))

    def get_messages_by_date(self, user_id: str, date_str: str) -> list:
        """
        Returns all messages for a user on a specific date (YYYY-MM-DD, UTC),
        sorted chronologically. Used to load past sessions in the UI.
        """
        try:
            day_start = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return []

        day_end = day_start + timedelta(days=1)

        cursor = self.messages.find(
            {
                'user_id':   user_id,
                'timestamp': {'$gte': day_start, '$lt': day_end}
            },
            {'_id': 0, 'role': 1, 'content': 1,
             'emotions': 1, 'score': 1, 'timestamp': 1}
        ).sort('timestamp', 1)

        out = []
        for doc in cursor:
            ts = doc.get('timestamp')
            out.append({
                'role':      doc.get('role'),
                'content':   doc.get('content'),
                'emotions':  doc.get('emotions'),
                'score':     doc.get('score'),
                'timestamp': ts.isoformat() if ts else None
            })
        return out

    # ── SESSION OPERATIONS ────────────────────────────────────────────────────

    def save_session_summary(self, user_id: str, summary: dict) -> None:
        """Saves a full session summary at the end of a conversation."""
        session = {
            'user_id':    user_id,
            'summary':    summary,
            'created_at': datetime.utcnow()
        }
        self.sessions.insert_one(session)

    def get_user_history(self, user_id: str, limit: int = 30) -> list:
        """
        Returns daily aggregated wellness history for a user.

        Groups user messages by day (UTC), computes average score,
        dominant emotion, and message count per day. History populates
        automatically as the user chats — no manual "end session" needed.
        """
        pipeline = [
            {'$match': {
                'user_id': user_id,
                'role':    'user',
                'score':   {'$exists': True, '$ne': None}
            }},
            {'$group': {
                '_id': {
                    '$dateToString': {'format': '%Y-%m-%d', 'date': '$timestamp'}
                },
                'average_score':  {'$avg':  '$score'},
                'total_messages': {'$sum':  1},
                'all_emotions':   {'$push': '$emotions'}
            }},
            {'$sort':  {'_id': DESCENDING}},
            {'$limit': limit}
        ]

        results = list(self.messages.aggregate(pipeline))

        history = []
        for doc in results:
            # Sum emotion probabilities across all messages that day
            totals = {}
            for emo_dict in doc.get('all_emotions', []):
                if emo_dict:
                    for emo, prob in emo_dict.items():
                        totals[emo] = totals.get(emo, 0) + prob

            dominant = (
                max(totals.items(), key=lambda x: x[1])[0]
                if totals else 'neutral'
            )

            history.append({
                'date':             doc['_id'],
                'average_score':    round(doc['average_score'], 2),
                'dominant_emotion': dominant,
                'total_messages':   doc['total_messages']
            })

        return list(reversed(history))  # oldest first for the chart

    # ── PASSWORD RESET OPERATIONS ─────────────────────────────────────────────

    def create_password_reset_token(self, user_id: str, token_hash: str,
                                    expires_at: datetime) -> None:
        """
        Stores a password reset token hash.
        Any previous unused tokens for this user are removed first
        (one active reset link per user at a time).
        """
        self.password_resets.delete_many({'user_id': user_id})
        self.password_resets.insert_one({
            'user_id':    user_id,
            'token_hash': token_hash,
            'expires_at': expires_at,
            'used':       False,
            'created_at': datetime.utcnow()
        })

    def find_password_reset_token(self, token_hash: str) -> dict:
        """Finds a reset token by its SHA-256 hash. Returns None if not found."""
        return self.password_resets.find_one({'token_hash': token_hash})

    def mark_reset_token_used(self, token_hash: str) -> None:
        """Marks a reset token as used so it cannot be reused."""
        self.password_resets.update_one(
            {'token_hash': token_hash},
            {'$set': {'used': True, 'used_at': datetime.utcnow()}}
        )

    def update_user_password(self, user_id: str, hashed_password: bytes) -> None:
        """Updates a user's password (after a successful reset)."""
        from bson import ObjectId
        self.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {
                'password':            hashed_password,
                'password_updated_at': datetime.utcnow()
            }}
        )