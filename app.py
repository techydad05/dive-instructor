"""
Deep Dive Instruction — Flask Application
Freelance Diving Instructor Website
"""

import os
import json
import uuid
from datetime import datetime
from pathlib import Path

from flask import (
    Flask, render_template, request, jsonify,
    send_from_directory, url_for, session, redirect
)
from werkzeug.utils import secure_filename

# --- Configuration ---
BASE_DIR = Path(__file__).resolve().parent

UPLOAD_FOLDER = BASE_DIR / 'uploads'
IMAGE_FOLDER = UPLOAD_FOLDER / 'images'
VIDEO_FOLDER = UPLOAD_FOLDER / 'videos'
CONTACT_FILE = BASE_DIR / 'messages.json'

ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.heic', '.heif'}
ALLOWED_VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v'}
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB

ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'divedeep2026')

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', uuid.uuid4().hex)

# Ensure upload dirs exist
IMAGE_FOLDER.mkdir(parents=True, exist_ok=True)
VIDEO_FOLDER.mkdir(parents=True, exist_ok=True)


def allowed_file(filename: str) -> bool:
    """Check if a filename has an allowed extension (image or video)."""
    ext = Path(filename).suffix.lower()
    return ext in ALLOWED_IMAGE_EXTENSIONS or ext in ALLOWED_VIDEO_EXTENSIONS


def get_destination(filename: str) -> Path:
    """Return the destination folder for a given filename based on type."""
    ext = Path(filename).suffix.lower()
    if ext in ALLOWED_IMAGE_EXTENSIONS:
        return IMAGE_FOLDER
    return VIDEO_FOLDER


def get_media_list() -> list[dict]:
    """Return sorted list of uploaded media, newest first."""
    media = []
    for folder in [IMAGE_FOLDER, VIDEO_FOLDER]:
        for f in sorted(folder.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
            if f.is_file() and f.suffix.lower() in ALLOWED_IMAGE_EXTENSIONS | ALLOWED_VIDEO_EXTENSIONS:
                media.append({
                    'filename': f.name,
                    'type': 'image' if folder == IMAGE_FOLDER else 'video',
                    'folder': 'images' if folder == IMAGE_FOLDER else 'videos',
                })
    return media


def get_messages() -> list[dict]:
    """Return list of contact messages."""
    if not CONTACT_FILE.exists():
        return []
    try:
        msgs = json.loads(CONTACT_FILE.read_text(encoding='utf-8'))
        return msgs if isinstance(msgs, list) else []
    except (json.JSONDecodeError, ValueError):
        return []


# --- Auth helpers ---

def login_required(f):
    """Decorator to protect routes behind admin login."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin'))
        return f(*args, **kwargs)
    return decorated


# --- Public Routes ---

@app.route('/')
def index():
    """Render the main landing page."""
    media = get_media_list()
    return render_template('index.html', media=media)


@app.route('/uploads/<folder>/<filename>')
def uploaded_file(folder: str, filename: str):
    """Serve uploaded files."""
    directory = IMAGE_FOLDER if folder == 'images' else VIDEO_FOLDER
    return send_from_directory(directory, filename)


@app.route('/contact', methods=['POST'])
def contact_form():
    """Handle contact form submissions."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'success': False, 'message': 'Invalid request.'}), 400

    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()
    interest = data.get('interest', '').strip()
    message = data.get('message', '').strip()

    if not name or not email or not message:
        return jsonify({'success': False, 'message': 'Name, email, and message are required.'}), 400

    entry = {
        'id': uuid.uuid4().hex[:12],
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'name': name,
        'email': email,
        'phone': phone,
        'interest': interest,
        'message': message,
    }

    messages = get_messages()
    messages.append(entry)
    CONTACT_FILE.write_text(
        json.dumps(messages, indent=2, ensure_ascii=False),
        encoding='utf-8'
    )

    return jsonify({'success': True, 'message': f'Thanks {name}! I\'ll get back to you within 24 hours.'})


# --- Admin Routes ---

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    """Admin login page + post handler."""
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard'))

    error = None
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            error = 'Incorrect password.'

    return render_template('admin.html', error=error)


@app.route('/admin/login', methods=['POST'])
def admin_login():
    """POST handler for login form."""
    password = request.form.get('password', '')
    if password == ADMIN_PASSWORD:
        session['admin_logged_in'] = True
        return redirect(url_for('admin_dashboard'))
    else:
        return render_template('admin.html', error='Incorrect password.')


@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """Admin dashboard with upload, gallery management, and messages."""
    media = get_media_list()
    messages = get_messages()
    return render_template('admin.html', media=media, messages=messages)


@app.route('/upload', methods=['POST'])
@login_required
def upload_files():
    """Handle file uploads (images and videos) — admin only."""
    if 'files' not in request.files:
        return jsonify({'success': False, 'message': 'No files provided.'}), 400

    files = request.files.getlist('files')
    uploaded = []
    errors = []

    for file in files:
        if not file.filename:
            continue
        if not allowed_file(file.filename):
            errors.append(f'{file.filename}: unsupported format')
            continue

        original_name = Path(secure_filename(file.filename))
        unique_name = f"{uuid.uuid4().hex[:12]}_{original_name.stem}{original_name.suffix}"

        dest_folder = get_destination(unique_name)
        filepath = dest_folder / unique_name
        file.save(str(filepath))
        uploaded.append(unique_name)

    if uploaded:
        msg = f"{len(uploaded)} file(s) uploaded successfully."
        if errors:
            msg += f" {len(errors)} file(s) skipped: {'; '.join(errors)}"
        return jsonify({'success': True, 'message': msg, 'files': uploaded})

    if errors:
        return jsonify({'success': False, 'message': f"No valid files. {'; '.join(errors)}"}), 400

    return jsonify({'success': False, 'message': 'No valid files received.'}), 400


@app.route('/admin/delete/<folder>/<filename>', methods=['DELETE'])
@login_required
def delete_media(folder: str, filename: str):
    """Delete a media file."""
    if folder not in ('images', 'videos'):
        return jsonify({'success': False, 'message': 'Invalid folder.'}), 400

    directory = IMAGE_FOLDER if folder == 'images' else VIDEO_FOLDER
    filepath = directory / filename

    if not filepath.exists():
        return jsonify({'success': False, 'message': 'File not found.'}), 404

    filepath.unlink()
    return jsonify({'success': True, 'message': 'Deleted.'})


@app.route('/admin/logout')
def admin_logout():
    """Log out of admin."""
    session.pop('admin_logged_in', None)
    return redirect(url_for('index'))


# --- Error Handlers ---

@app.errorhandler(413)
def too_large(_e):
    """Handle file too large errors gracefully."""
    return jsonify({'success': False, 'message': 'File too large. Maximum size is 50MB.'}), 413


# --- Entry Point ---
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🌊 Deep Dive Instruction — http://localhost:{port}")
    print(f"🔐 Admin: http://localhost:{port}/admin  (password: {ADMIN_PASSWORD})")
    app.run(host='0.0.0.0', port=port, debug=False)
