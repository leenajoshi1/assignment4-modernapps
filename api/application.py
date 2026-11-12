"""Photo Portal REST API. Run `python application.py` to initialize and serve."""
from datetime import date
from functools import wraps
from pathlib import Path
import os
from io import BytesIO

from flask import Flask, jsonify, request, session, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from PIL import Image, UnidentifiedImageError
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder=None)
app.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY', 'assignment4-local-development-only'),
    SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL', 'sqlite:///photos.db'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    MAX_CONTENT_LENGTH=10 * 1024 * 1024,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    UPLOAD_FOLDER=str(Path(__file__).parent / 'static/images/photos'),
)
CORS(app, origins=['http://localhost:3000'], supports_credentials=True)
db = SQLAlchemy(app)


class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)


class GeneralUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gmail = db.Column(db.String(254), unique=True, nullable=False)


class Photos(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    date_taken = db.Column(db.Date, nullable=False)
    tags = db.Column(db.Text, nullable=False, default='')
    comments = db.Column(db.Text, nullable=False, default='')

    def as_dict(self):
        return dict(id=self.id, name=self.name, date_taken=self.date_taken.isoformat(),
                    tags=self.tags, comments=self.comments)


def require_user(admin=False):
    def decorate(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            if not session.get('username'):
                return jsonify(message='Login required'), 401
            if admin and session.get('usertype') != 'admin':
                return jsonify(message='Admin access required'), 403
            return fn(*args, **kwargs)
        return wrapped
    return decorate


def payload():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def text_field(data, key):
    value = data.get(key, '')
    return value.strip() if isinstance(value, str) else ''


@app.route('/api/admin', methods=['POST', 'GET'])
def admins():
    if request.method == 'GET':
        if session.get('usertype') != 'admin':
            return jsonify(message='Admin access required'), 403
        return jsonify(admins=[dict(id=a.id, username=a.username) for a in Admin.query.all()])
    # Bootstrap exactly one administrator. Subsequent registration is forbidden.
    if db.session.get(Admin, 1):
        return jsonify(message='An admin already exists'), 409
    data = payload()
    username, password = text_field(data, 'username'), text_field(data, 'password')
    if not username or not password:
        return jsonify(message='Username and password required'), 400
    db.session.add(Admin(id=1, username=username, password=generate_password_hash(password)))
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(message='An admin already exists'), 409
    return jsonify(message='Created', username=username), 201


@app.route('/api/generaluser', methods=['GET', 'POST'])
@require_user(admin=True)
def general_users():
    if request.method == 'GET':
        return jsonify(generalusers=[dict(id=u.id, gmail=u.gmail) for u in GeneralUser.query.all()])
    gmail = text_field(payload(), 'gmail').lower()
    import re
    if not re.fullmatch(r'[a-z0-9.!#$%&\x27*+/=?^_`{|}~-]+@gmail\.com', gmail):
        return jsonify(message='A valid gmail.com address is required'), 400
    db.session.add(GeneralUser(gmail=gmail))
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(message='User already exists'), 409
    return jsonify(message='Created', gmail=gmail), 201


@app.post('/api/adminlogin')
def admin_login():
    data = payload()
    username = text_field(data, 'username') or text_field(data, 'name')
    admin = Admin.query.filter_by(username=username).first()
    password = text_field(data, 'password')
    if not admin or not check_password_hash(admin.password, password):
        return jsonify(message='NotFound'), 401
    session.clear()
    session.update(username=admin.username, usertype='admin')
    return jsonify(message='Success', username=admin.username, usertype='admin')


@app.post('/api/generaluserlogin')
def generaluser_login():
    user = GeneralUser.query.filter_by(gmail=text_field(payload(), 'gmail').lower()).first()
    if not user:
        return jsonify(message='NotFound'), 401
    session.clear()
    session.update(username=user.gmail, usertype='generaluser')
    return jsonify(message='Success', username=user.gmail, usertype='generaluser')


@app.get('/api/session')
@require_user()
def current_session():
    return jsonify(username=session['username'], usertype=session['usertype'])


@app.post('/api/logout')
def logout():
    usertype = session.get('usertype', 'generaluser')
    session.clear()
    return jsonify(message='Success', usertype=usertype)


@app.get('/api/photos')
@require_user()
def get_photos():
    return jsonify(photos=[p.as_dict() for p in Photos.query.order_by(Photos.id.desc()).all()])


@app.get('/api/photos/<photo_name>/comments')
@require_user()
def get_photo_comments(photo_name):
    photo = Photos.query.filter_by(name=photo_name).first_or_404()
    return jsonify(comments=photo.comments)


@app.get('/static/images/photos/<photo_name>')
@require_user()
def photo_file(photo_name):
    Photos.query.filter_by(name=photo_name).first_or_404()
    return send_from_directory(app.config['UPLOAD_FOLDER'], photo_name)


@app.post('/api/upload')
@require_user(admin=True)
def upload_photo():
    file = request.files.get('photo_file')
    if not file or not file.filename:
        return jsonify(message='No file uploaded'), 400
    name = secure_filename(file.filename)
    if not name or Path(name).suffix.lower() not in {'.png', '.jpg', '.jpeg', '.gif', '.webp'}:
        return jsonify(message='Choose a PNG, JPEG, GIF, or WebP image'), 400
    try:
        taken = date.fromisoformat(request.form.get('date_taken', ''))
    except ValueError:
        return jsonify(message='Date must be YYYY-MM-DD'), 400
    content = file.read()
    try:
        with Image.open(BytesIO(content)) as image:
            image.verify()
    except (UnidentifiedImageError, OSError, SyntaxError, Image.DecompressionBombError):
        return jsonify(message='Invalid image file'), 400
    if Photos.query.filter_by(name=name).first():
        return jsonify(message='A photo with this name already exists'), 409
    photo = Photos(name=name, date_taken=taken, tags=request.form.get('tags', '').strip(),
                   comments=request.form.get('comments', '').strip())
    folder = Path(app.config['UPLOAD_FOLDER'])
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    # Exclusive creation prevents two uploads from silently overwriting one image.
    try:
        with path.open('xb') as output:
            output.write(content)
    except FileExistsError:
        return jsonify(message='A file with this name already exists'), 409
    try:
        db.session.add(photo)
        db.session.commit()
    except Exception:
        db.session.rollback()
        path.unlink(missing_ok=True)
        raise
    return jsonify(message='Upload successful!', **photo.as_dict()), 201


@app.post('/api/search')
@require_user()
def search():
    data = payload()
    kind, query = text_field(data, 'type').lower(), text_field(data, 'query')
    photos = Photos.query
    if kind == 'date':
        if query:
            try:
                photos = photos.filter_by(date_taken=date.fromisoformat(query))
            except ValueError:
                return jsonify(message='Date must be YYYY-MM-DD'), 400
    elif kind in ('name', 'tags'):
        # Escape SQL wildcard characters: search input is a literal substring.
        column = Photos.name if kind == 'name' else Photos.tags
        photos = photos.filter(column.icontains(query, autoescape=True))
    else:
        return jsonify(message='Choose Name, Tags, or Date'), 400
    return jsonify(results=[p.as_dict() for p in photos.order_by(Photos.id.desc()).all()])


@app.errorhandler(413)
def too_large(error):
    return jsonify(message='Image must be smaller than 10 MB'), 413


with app.app_context():
    db.create_all()
    # Pre-configured local assignment account; override before first startup.
    if not db.session.get(Admin, 1):
        db.session.add(Admin(id=1, username=os.environ.get('ADMIN_USERNAME', 'admin'),
                             password=generate_password_hash(os.environ.get('ADMIN_PASSWORD', 'admin'))))
        db.session.commit()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
