# backend/check_history.py
from database import DatabaseManager
from datetime import datetime, timedelta

db = DatabaseManager()
user = db.find_user_by_email("demo@test.com")

if not user:
    print("No user found.")
    exit()

user_id = str(user['_id'])
print(f"User: {user['username']}  (id: {user_id})\n")

# SESSIONS collection
print("=" * 60)
print("SESSIONS collection (what /api/session/history reads):")
print("=" * 60)
sess_count = db.sessions.count_documents({'user_id': user_id})
print(f"Total sessions: {sess_count}")
for s in db.sessions.find({'user_id': user_id}).sort('created_at', -1).limit(10):
    print(f"  • {s.get('created_at')}  →  {s.get('summary')}")

# MESSAGES collection
print()
print("=" * 60)
print("MESSAGES collection (raw chat messages):")
print("=" * 60)
msg_count = db.messages.count_documents({'user_id': user_id})
print(f"Total messages: {msg_count}")

yesterday = datetime.utcnow() - timedelta(days=1)
recent = list(db.messages.find({
    'user_id': user_id,
    'timestamp': {'$gte': yesterday}
}).sort('timestamp', -1))
print(f"In the last 24 hours: {len(recent)}")
for m in recent[:10]:
    content = (m.get('content') or '')[:60]
    print(f"  • {m.get('timestamp')}  [{m.get('role')}]  '{content}'  score={m.get('score')}")