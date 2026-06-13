"""
Campus Voice - Smart Complaint Management System
Flask Backend Application
"""

import os
import sqlite3
from datetime import datetime
from functools import wraps
from flask import (Flask, render_template, request, redirect, url_for,
                   session, flash, jsonify, g)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'campus-voice-secret-key-2024'

# ── Configuration ─────────────────────────────────────────────────────────
BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
DATABASE       = os.path.join(BASE_DIR, 'database.db')
UPLOAD_FOLDER  = os.path.join(BASE_DIR, 'static', 'uploads')
ALLOWED_EXT    = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_CONTENT_LEN = 5 * 1024 * 1024   # 5 MB

app.config['UPLOAD_FOLDER']      = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LEN

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

CATEGORIES = ['Classroom','Wi-Fi / Internet','Electrical','Laboratory',
              'Library','Washroom','Canteen','Security','Other']
STATUSES   = ['Pending','Assigned','In Progress','Resolved']
PRIORITIES = ['Low','Medium','High']

# ── Database helpers ───────────────────────────────────────────────────────
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode=WAL")
    return g.db

@app.teardown_appcontext
def close_db(exc):
    db = g.pop('db', None)
    if db:
        db.close()

def query(sql, args=(), one=False):
    cur = get_db().execute(sql, args)
    rv  = cur.fetchall()
    return (rv[0] if rv else None) if one else rv

def execute(sql, args=()):
    db = get_db()
    cur = db.execute(sql, args)
    db.commit()
    return cur.lastrowid

def init_db():
    db = sqlite3.connect(DATABASE)
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            name      TEXT    NOT NULL,
            email     TEXT    UNIQUE NOT NULL,
            password  TEXT    NOT NULL,
            role      TEXT    NOT NULL DEFAULT 'student',
            created_at TEXT   DEFAULT (datetime('now'))
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            title       TEXT    NOT NULL,
            description TEXT    NOT NULL,
            category    TEXT    NOT NULL,
            image       TEXT,
            status      TEXT    NOT NULL DEFAULT 'Pending',
            priority    TEXT    NOT NULL DEFAULT 'Low',
            created_at  TEXT    DEFAULT (datetime('now')),
            updated_at  TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    # Seed admin account
    existing = db.execute("SELECT id FROM users WHERE email='admin@campus.edu'").fetchone()
    if not existing:
        db.execute(
            "INSERT INTO users (name, email, password, role) VALUES (?,?,?,?)",
            ('Admin', 'admin@campus.edu',
             generate_password_hash('Admin@123'), 'admin')
        )
    db.commit()
    db.close()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT

# ── Auth decorators ────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ── Public routes ──────────────────────────────────────────────────────────
@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('admin_panel') if session['role'] == 'admin'
                        else url_for('dashboard'))
    return render_template('home.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name     = request.form.get('name','').strip()
        email    = request.form.get('email','').strip().lower()
        password = request.form.get('password','')
        confirm  = request.form.get('confirm_password','')

        if not all([name, email, password, confirm]):
            flash('All fields are required.', 'danger')
        elif password != confirm:
            flash('Passwords do not match.', 'danger')
        elif len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
        elif query("SELECT id FROM users WHERE email=?", (email,), one=True):
            flash('Email already registered.', 'danger')
        else:
            execute("INSERT INTO users (name,email,password) VALUES (?,?,?)",
                    (name, email, generate_password_hash(password)))
            flash('Account created! Please log in.', 'success')
            return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email    = request.form.get('email','').strip().lower()
        password = request.form.get('password','')
        user     = query("SELECT * FROM users WHERE email=?", (email,), one=True)

        if user and check_password_hash(user['password'], password):
            session.clear()
            session['user_id'] = user['id']
            session['name']    = user['name']
            session['email']   = user['email']
            session['role']    = user['role']
            flash(f'Welcome back, {user["name"]}!', 'success')
            return redirect(url_for('admin_panel') if user['role'] == 'admin'
                            else url_for('dashboard'))
        flash('Invalid email or password.', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    name = session.get('name', 'User')
    session.clear()
    flash(f'Goodbye, {name}! You have been logged out.', 'info')
    return redirect(url_for('home'))

# ── Student routes ─────────────────────────────────────────────────────────
@app.route('/dashboard')
@login_required
def dashboard():
    uid = session['user_id']
    total    = query("SELECT COUNT(*) as c FROM complaints WHERE user_id=?", (uid,), one=True)['c']
    pending  = query("SELECT COUNT(*) as c FROM complaints WHERE user_id=? AND status='Pending'", (uid,), one=True)['c']
    inprog   = query("SELECT COUNT(*) as c FROM complaints WHERE user_id=? AND status='In Progress'", (uid,), one=True)['c']
    resolved = query("SELECT COUNT(*) as c FROM complaints WHERE user_id=? AND status='Resolved'", (uid,), one=True)['c']
    recent   = query("SELECT * FROM complaints WHERE user_id=? ORDER BY created_at DESC LIMIT 5", (uid,))
    return render_template('dashboard.html',
                           total=total, pending=pending,
                           inprog=inprog, resolved=resolved,
                           recent=recent, categories=CATEGORIES)

@app.route('/complaint/new', methods=['GET','POST'])
@login_required
def new_complaint():
    if request.method == 'POST':
        title       = request.form.get('title','').strip()
        description = request.form.get('description','').strip()
        category    = request.form.get('category','')
        image_file  = request.files.get('image')

        if not all([title, description, category]):
            flash('Title, description, and category are required.', 'danger')
            return render_template('complaint.html', categories=CATEGORIES)

        image_name = None
        if image_file and image_file.filename:
            if allowed_file(image_file.filename):
                fname      = secure_filename(image_file.filename)
                ts         = datetime.now().strftime('%Y%m%d%H%M%S')
                image_name = f"{ts}_{fname}"
                image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_name))
            else:
                flash('Invalid file type. Allowed: png, jpg, jpeg, gif, webp.', 'danger')
                return render_template('complaint.html', categories=CATEGORIES)

        execute("""INSERT INTO complaints (user_id,title,description,category,image)
                   VALUES (?,?,?,?,?)""",
                (session['user_id'], title, description, category, image_name))
        flash('Complaint submitted successfully!', 'success')
        return redirect(url_for('my_complaints'))

    return render_template('complaint.html', categories=CATEGORIES)

@app.route('/my-complaints')
@login_required
def my_complaints():
    rows = query("SELECT * FROM complaints WHERE user_id=? ORDER BY created_at DESC",
                 (session['user_id'],))
    return render_template('my_complaints.html', complaints=rows)

# ── Admin routes ───────────────────────────────────────────────────────────
@app.route('/admin')
@admin_required
def admin_panel():
    total    = query("SELECT COUNT(*) as c FROM complaints", one=True)['c']
    pending  = query("SELECT COUNT(*) as c FROM complaints WHERE status='Pending'", one=True)['c']
    inprog   = query("SELECT COUNT(*) as c FROM complaints WHERE status='In Progress'", one=True)['c']
    resolved = query("SELECT COUNT(*) as c FROM complaints WHERE status='Resolved'", one=True)['c']
    high_pri = query("SELECT COUNT(*) as c FROM complaints WHERE priority='High'", one=True)['c']

    status_f   = request.args.get('status','')
    category_f = request.args.get('category','')
    search_q   = request.args.get('q','').strip()

    sql    = """SELECT c.*, u.name as student_name, u.email as student_email
                FROM complaints c JOIN users u ON c.user_id=u.id WHERE 1=1"""
    params = []
    if status_f:
        sql += " AND c.status=?"; params.append(status_f)
    if category_f:
        sql += " AND c.category=?"; params.append(category_f)
    if search_q:
        sql += " AND (c.title LIKE ? OR c.description LIKE ? OR u.name LIKE ?)"
        params += [f'%{search_q}%', f'%{search_q}%', f'%{search_q}%']
    sql += " ORDER BY c.created_at DESC"

    complaints = query(sql, params)
    return render_template('admin.html',
                           total=total, pending=pending,
                           inprog=inprog, resolved=resolved,
                           high_pri=high_pri, complaints=complaints,
                           categories=CATEGORIES, statuses=STATUSES,
                           priorities=PRIORITIES,
                           status_f=status_f, category_f=category_f,
                           search_q=search_q)

@app.route('/admin/complaint/<int:cid>/update', methods=['POST'])
@admin_required
def update_complaint(cid):
    status   = request.form.get('status')
    priority = request.form.get('priority')
    if status not in STATUSES or priority not in PRIORITIES:
        flash('Invalid status or priority.', 'danger')
        return redirect(url_for('admin_panel'))
    execute("""UPDATE complaints SET status=?, priority=?, updated_at=datetime('now')
               WHERE id=?""", (status, priority, cid))
    flash('Complaint updated successfully.', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/complaint/<int:cid>/delete', methods=['POST'])
@admin_required
def delete_complaint(cid):
    row = query("SELECT image FROM complaints WHERE id=?", (cid,), one=True)
    if row and row['image']:
        path = os.path.join(app.config['UPLOAD_FOLDER'], row['image'])
        if os.path.exists(path):
            os.remove(path)
    execute("DELETE FROM complaints WHERE id=?", (cid,))
    flash('Complaint deleted.', 'success')
    return redirect(url_for('admin_panel'))

# API endpoint for complaint detail modal
@app.route('/api/complaint/<int:cid>')
@admin_required
def complaint_detail(cid):
    row = query("""SELECT c.*, u.name as student_name, u.email as student_email
                   FROM complaints c JOIN users u ON c.user_id=u.id WHERE c.id=?""",
                (cid,), one=True)
    if not row:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(dict(row))

# ── Entry point ────────────────────────────────────────────────────────────
if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
