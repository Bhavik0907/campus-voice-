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
REWARD_POINTS = {'Low': 10, 'Medium': 20, 'High': 30}
ASSIGNED_POINTS = 50

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
            points    INTEGER NOT NULL DEFAULT 0,
            created_at TEXT   DEFAULT (datetime('now'))
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id       INTEGER NOT NULL,
            title         TEXT    NOT NULL,
            description   TEXT    NOT NULL,
            category      TEXT    NOT NULL,
            image         TEXT,
            status        TEXT    NOT NULL DEFAULT 'Pending',
            priority      TEXT    NOT NULL DEFAULT 'Low',
            reward_points INTEGER NOT NULL DEFAULT 0,
            created_at    TEXT    DEFAULT (datetime('now')),
            updated_at    TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    cols = [row[1] for row in db.execute("PRAGMA table_info(users)").fetchall()]
    if 'points' not in cols:
        db.execute("ALTER TABLE users ADD COLUMN points INTEGER NOT NULL DEFAULT 0")
    cols = [row[1] for row in db.execute("PRAGMA table_info(complaints)").fetchall()]
    if 'reward_points' not in cols:
        db.execute("ALTER TABLE complaints ADD COLUMN reward_points INTEGER NOT NULL DEFAULT 0")
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

def get_reward_level(points):
    if points >= 150:
        return 'Gold'
    if points >= 75:
        return 'Silver'
    if points >= 30:
        return 'Bronze'
    return 'Starter'

@app.context_processor
def inject_user_points():
    if 'user_id' in session and session.get('role') != 'admin':
        user = query("SELECT points FROM users WHERE id=?", (session['user_id'],), one=True)
        return {'current_points': user['points'] if user else 0}
    return {}

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
            session['points']  = user['points'] if 'points' in user.keys() else 0
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
    user     = query("SELECT points FROM users WHERE id=?", (uid,), one=True)
    points   = user['points'] if user else 0
    reward_level = get_reward_level(points)
    return render_template('dashboard.html',
                           total=total, pending=pending,
                           inprog=inprog, resolved=resolved,
                           recent=recent, categories=CATEGORIES,
                           points=points, reward_level=reward_level)

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
    reward_count = query("SELECT COUNT(*) as c FROM complaints WHERE assigned_points>0 OR reward_points>0", one=True)['c']
    assigned_count = query("SELECT COUNT(*) as c FROM complaints WHERE assigned_points>0", one=True)['c']
    resolved_count = query("SELECT COUNT(*) as c FROM complaints WHERE reward_points>0", one=True)['c']
    total_reward_points = query("SELECT IFNULL(SUM(assigned_points + reward_points), 0) as c FROM complaints", one=True)['c']
    rewarded_students = query(
        """
        SELECT u.id, u.name, u.email,
               SUM(c.assigned_points + c.reward_points) AS total_points,
               SUM(CASE WHEN c.assigned_points>0 THEN 1 ELSE 0 END) AS assigned_count,
               SUM(CASE WHEN c.reward_points>0 THEN 1 ELSE 0 END) AS resolved_count
        FROM users u
        JOIN complaints c ON c.user_id=u.id
        GROUP BY u.id
        HAVING total_points > 0
        ORDER BY total_points DESC
        """
    )

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
                           reward_count=reward_count,
                           assigned_count=assigned_count,
                           resolved_count=resolved_count,
                           total_reward_points=total_reward_points,
                           rewarded_students=rewarded_students,
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

    row = query("SELECT user_id, status, reward_points, assigned_points FROM complaints WHERE id=?", (cid,), one=True)
    if not row:
        flash('Complaint not found.', 'danger')
        return redirect(url_for('admin_panel'))

    reward_awarded = False
    assigned_awarded = False

    if status == 'Assigned' and (row['assigned_points'] == 0 or row['assigned_points'] is None):
        execute("UPDATE users SET points = points + ? WHERE id=?", (ASSIGNED_POINTS, row['user_id']))
        execute("""UPDATE complaints SET status=?, priority=?, assigned_points=?, updated_at=datetime('now')
                   WHERE id=?""", (status, priority, ASSIGNED_POINTS, cid))
        assigned_awarded = True
    elif status == 'Resolved' and (row['reward_points'] == 0 or row['reward_points'] is None):
        reward = REWARD_POINTS.get(priority, 10)
        execute("UPDATE users SET points = points + ? WHERE id=?", (reward, row['user_id']))
        execute("""UPDATE complaints SET status=?, priority=?, reward_points=?, updated_at=datetime('now')
                   WHERE id=?""", (status, priority, reward, cid))
        reward_awarded = True
    else:
        execute("""UPDATE complaints SET status=?, priority=?, updated_at=datetime('now')
                   WHERE id=?""", (status, priority, cid))

    message = 'Complaint updated successfully.'
    if assigned_awarded:
        message += ' 50 points awarded for assignment.'
    elif reward_awarded:
        message += ' Reward points awarded.'
    flash(message, 'success')
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
