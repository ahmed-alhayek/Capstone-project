# mental_health_companion/backend/app.py
"""
Flask Backend API — Mental Health Companion
===========================================

"""


import os
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"

import sys
import jwt
import bcrypt
import secrets
import hashlib
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from audio_v2_route import audio_v2_bp
from text_v2_route import text_v2_bp
from face_route import face_bp

# ── Load environment variables ────────────────────────────────────────────────
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# ── Add project root to path ──────────────────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# ── Import our custom modules ─────────────────────────────────────────────────
from chatbot import MentalHealthChatbot
from database import DatabaseManager
from email_service import send_password_reset_email

# ── Load config from .env ─────────────────────────────────────────────────────
JWT_SECRET               = os.getenv("JWT_SECRET")
JWT_EXPIRY_HOURS         = int(os.getenv("JWT_EXPIRY_HOURS", 24))
CRISIS_THRESHOLD         = int(os.getenv("CRISIS_THRESHOLD", 40))
FLASK_PORT               = int(os.getenv("FLASK_PORT", 5000))
RESET_TOKEN_EXPIRY_HOURS = int(os.getenv("RESET_TOKEN_EXPIRY_HOURS", 1))
FRONTEND_URL             = os.getenv("FRONTEND_URL", "http://localhost:8080")

if not JWT_SECRET:
    raise ValueError("❌ JWT_SECRET not found in .env file")

# ── Flask App Setup ───────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:5173", "http://localhost:3000", "http://localhost:8080"]}}, supports_credentials=True)
app.register_blueprint(audio_v2_bp)
app.register_blueprint(text_v2_bp)
app.register_blueprint(face_bp)

# ── Initialize database ───────────────────────────────────────────────────────
db = DatabaseManager()

# ── Active chatbot sessions (one per logged-in user) ─────────────────────────
active_sessions = {}


# ─────────────────────────────────────────────────────────────────────────────
# JWT HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def generate_token(user_id: str, username: str) -> str:
    """
    Generates a JWT token for an authenticated user.
    Token expires after JWT_EXPIRY_HOURS hours (set in .env).
    """
    payload = {
        'user_id':  user_id,
        'username': username,
        'exp':      datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')


def verify_token(token: str) -> dict:
    """
    Decodes and verifies a JWT token.
    Returns the payload dict if valid, None if expired or invalid.
    """
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def require_auth(f):
    """
    Decorator that protects endpoints — requires a valid JWT token.
    Frontend must send: Authorization: Bearer <token>
    If valid   → passes user_data to the endpoint function.
    If invalid → returns 401 Unauthorized.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization token required'}), 401

        token     = auth_header.split(' ')[1]
        user_data = verify_token(token)

        if not user_data:
            return jsonify({'error': 'Token is invalid or has expired'}), 401

        return f(user_data, *args, **kwargs)
    return decorated


def hash_token(token: str) -> str:
    """SHA-256 hash a raw token so we never store the raw value in the DB."""
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


# ─────────────────────────────────────────────────────────────────────────────
# AUTH ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/api/register', methods=['POST'])
def register():
    """
    POST /api/register
    Request : { "username": "...", "email": "...", "password": "..." }
    Response: { "message": "...", "token": "...", "username": "..." }
    """
    data = request.get_json()

    if not data or not all(f in data for f in ['username', 'email', 'password']):
        return jsonify({'error': 'Username, email and password are required'}), 400

    username = data['username'].strip()
    email    = data['email'].strip().lower()
    password = data['password']

    if len(username) < 3:
        return jsonify({'error': 'Username must be at least 3 characters'}), 400
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400

    if db.find_user_by_email(email):
        return jsonify({'error': 'This email is already registered'}), 409
    if db.find_user_by_username(username):
        return jsonify({'error': 'This username is already taken'}), 409

    hashed  = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    user_id = db.create_user(username, email, hashed)
    token   = generate_token(user_id, username)

    return jsonify({
        'message':  'Account created successfully!',
        'token':    token,
        'username': username
    }), 201


@app.route('/api/login', methods=['POST'])
def login():
    """
    POST /api/login
    Request : { "email": "...", "password": "..." }
    Response: { "message": "...", "token": "...", "username": "..." }
    """
    data = request.get_json()

    if not data or not all(f in data for f in ['email', 'password']):
        return jsonify({'error': 'Email and password are required'}), 400

    email    = data['email'].strip().lower()
    password = data['password']

    user = db.find_user_by_email(email)
    if not user:
        return jsonify({'error': 'Invalid email or password'}), 401

    if not bcrypt.checkpw(password.encode('utf-8'), user['password']):
        return jsonify({'error': 'Invalid email or password'}), 401

    token = generate_token(str(user['_id']), user['username'])

    return jsonify({
        'message':  f"Welcome back, {user['username']}!",
        'token':    token,
        'username': user['username']
    }), 200


@app.route('/api/forgot-password', methods=['POST'])
def forgot_password():
    """
    POST /api/forgot-password
    Request : { "email": "..." }
    Response: { "message": "..." }

    Always returns success, even if the email doesn't exist, to prevent
    attackers from using this endpoint to enumerate accounts.
    """
    data = request.get_json()

    if not data or 'email' not in data:
        return jsonify({'error': 'Email is required'}), 400

    email = data['email'].strip().lower()
    user  = db.find_user_by_email(email)

    if user:
        raw_token  = secrets.token_urlsafe(32)
        token_hash = hash_token(raw_token)
        expires_at = datetime.utcnow() + timedelta(hours=RESET_TOKEN_EXPIRY_HOURS)

        db.create_password_reset_token(
            user_id    = str(user['_id']),
            token_hash = token_hash,
            expires_at = expires_at
        )

        reset_link = f"{FRONTEND_URL}/reset-password?token={raw_token}"
        send_password_reset_email(
            to_email   = email,
            reset_link = reset_link,
            username   = user['username']
        )

    # Same response whether or not the email existed
    return jsonify({
        'message': "If an account exists with that email, a reset link has been sent."
    }), 200


@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    """
    POST /api/reset-password
    Request : { "token": "...", "password": "new_password" }
    Response: { "message": "Password updated successfully" }
    """
    data = request.get_json()

    if not data or 'token' not in data or 'password' not in data:
        return jsonify({'error': 'Token and new password are required'}), 400

    raw_token    = data['token']
    new_password = data['password']

    if len(new_password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400

    token_hash = hash_token(raw_token)
    token_doc  = db.find_password_reset_token(token_hash)

    if not token_doc:
        return jsonify({'error': 'Invalid or expired reset link'}), 400
    if token_doc.get('used'):
        return jsonify({'error': 'This reset link has already been used'}), 400
    if token_doc.get('expires_at') < datetime.utcnow():
        return jsonify({'error': 'This reset link has expired'}), 400

    hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
    db.update_user_password(token_doc['user_id'], hashed)
    db.mark_reset_token_used(token_hash)

    return jsonify({
        'message': 'Password updated successfully. You can now sign in.'
    }), 200


# ─────────────────────────────────────────────────────────────────────────────
# CHAT ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/api/chat', methods=['POST'])
@require_auth
def chat(user_data):
    """
    POST /api/chat
    Request : { "message": "...", "audio_emotions": {...} (optional) }
    Response: {
        "response": "...",
        "fused_emotions": {...},
        "mental_health_score": 72.5,
        "crisis_detected": false,
        "session_summary": {...}
    }
    """
    data = request.get_json()

    if not data or 'message' not in data:
        return jsonify({'error': 'Message field is required'}), 400

    user_message = data['message'].strip()
    if not user_message:
        return jsonify({'error': 'Message cannot be empty'}), 400

    user_id        = user_data['user_id']
    audio_emotions = data.get('audio_emotions', None)

    if user_id not in active_sessions:
        active_sessions[user_id] = MentalHealthChatbot()

    result          = active_sessions[user_id].chat(user_message, audio_emotions)
    crisis_detected = result['mental_health_score'] < CRISIS_THRESHOLD

    db.save_message(
        user_id  = user_id,
        role     = 'user',
        content  = user_message,
        emotions = result['fused_emotions'],
        score    = result['mental_health_score']
    )
    db.save_message(
        user_id = user_id,
        role    = 'assistant',
        content = result['response']
    )

    return jsonify({
        'response':            result['response'],
        'fused_emotions':      result['fused_emotions'],
        'mental_health_score': result['mental_health_score'],
        'crisis_detected':     crisis_detected,
        'session_summary':     result['session_summary']
    }), 200


@app.route('/api/analyze-audio', methods=['POST'])
@require_auth
def analyze_audio(user_data):
    """
    POST /api/analyze-audio
    Request : multipart/form-data with field 'audio'
    Response: { "audio_emotions": { "sad": 0.7, ... } }
    """
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400

    audio_file = request.files['audio']
    temp_path  = os.path.join(os.path.dirname(__file__), '..', 'temp_audio.wav')
    audio_file.save(temp_path)

    try:
        from audio_model.predict_audio import predict_audio_emotions
        audio_emotions = predict_audio_emotions(temp_path)
        return jsonify({'audio_emotions': audio_emotions}), 200

    except Exception as e:
        return jsonify({'error': f'Audio analysis failed: {str(e)}'}), 500

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@app.route('/api/session/end', methods=['POST'])
@require_auth
def end_session(user_data):
    """
    POST /api/session/end
    Response: { "summary": { ... } }
    """
    user_id = user_data['user_id']

    if user_id not in active_sessions:
        return jsonify({'error': 'No active session found'}), 404

    summary = active_sessions[user_id].end_session()
    db.save_session_summary(user_id, summary)
    del active_sessions[user_id]

    return jsonify({'summary': summary}), 200


@app.route('/api/session/history', methods=['GET'])
@require_auth
def get_history(user_data):
    """
    GET /api/session/history
    Response: { "history": [ { date, average_score, dominant_emotion, total_messages }, ... ] }
    """
    history = db.get_user_history(user_data['user_id'])
    return jsonify({'history': history}), 200


@app.route('/api/messages', methods=['GET'])
@require_auth
def get_messages_by_date(user_data):
    """
    GET /api/messages?date=YYYY-MM-DD
    Returns all messages for the authenticated user on the given date.
    Response: { "messages": [ { role, content, emotions, score, timestamp }, ... ], "date": "YYYY-MM-DD" }
    """
    date_str = request.args.get('date', '').strip()
    if not date_str:
        return jsonify({'error': 'date query parameter required (YYYY-MM-DD)'}), 400

    messages = db.get_messages_by_date(user_data['user_id'], date_str)
    return jsonify({'messages': messages, 'date': date_str}), 200


# ─────────────────────────────────────────────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/api/health', methods=['GET'])
def health_check():
    """GET /api/health — confirms the server is running."""
    return jsonify({
        'status':  'ok',
        'message': 'Mental Health Companion API is running!'
    }), 200


# ─────────────────────────────────────────────────────────────────────────────
# START SERVER
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print(" Starting Mental Health Companion API...")
    print(f" Server running at http://localhost:{FLASK_PORT}")
    app.run(debug=True, host='0.0.0.0', port=FLASK_PORT)