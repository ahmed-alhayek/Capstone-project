# mental_health_companion/backend/database.py
"""
Database Manager — MongoDB Operations
AI Mental Health Companion | Capstone Project
=============================================
Handles all database operations:
- User accounts (register/login)
- Chat messages with emotion data
- Session summaries
- Emotion history per user
"""

import os
from datetime import datetime
from pymongo import MongoClient, DESCENDING
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))


class DatabaseManager:
    """
    Manages all MongoDB collections for the Mental Health Companion.

    Collections:
    ├── users    → registered accounts
    ├── messages → every chat message + emotion data
    └── sessions → session summaries per user
    """

    def __init__(self):
        mongo_url = os.getenv("MONGO_URL") or "mongodb://localhost:27017"

        try:
            self.client = MongoClient(mongo_url, serverSelectionTimeoutMS=2000)
            self.client.admin.command('ping')
            
            self.db       = self.client['mental_health_companion']
            self.users    = self.db['users']
            self.messages = self.db['messages']
            self.sessions = self.db['sessions']

            # Create standard indices
            self.users.create_index('email',    unique=True)
            self.users.create_index('username', unique=True)
            self.messages.create_index([('timestamp', DESCENDING)])
            self.sessions.create_index([('date', DESCENDING)])
        except Exception as e:
            print(f"⚠️ WARNING: Cannot connect to MongoDB: {e}")
            self.db, self.users, self.messages, self.sessions = None, None, None, None

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

    # ── SESSION OPERATIONS ────────────────────────────────────────────────────

    def save_session_summary(self, user_id: str, summary: dict) -> None:
        """Saves a full session summary at the end of a conversation."""
        session = {
            'user_id':    user_id,
            'summary':    summary,
            'created_at': datetime.utcnow()
        }
        self.sessions.insert_one(session)

    def get_user_history(self, user_id: str, limit: int = 10) -> list:
        """
        Returns the last N session summaries for a user.
        Used to build the emotion history chart in the frontend.
        """
        cursor = self.sessions.find(
            {'user_id': user_id},
            {'_id': 0, 'summary': 1, 'created_at': 1}
        ).sort('created_at', DESCENDING).limit(limit)

        history = []
        for doc in cursor:
            history.append({
                'date':             doc['created_at'].strftime('%Y-%m-%d %H:%M'),
                'average_score':    doc['summary'].get('average_score', 0),
                'dominant_emotion': doc['summary'].get('dominant_emotion', 'neutral'),
                'total_messages':   doc['summary'].get('total_messages', 0)
            })

        return list(reversed(history))