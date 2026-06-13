# 🎓 Campus Voice – Smart Complaint Management System

A full-stack web application for managing campus complaints, built with Flask, SQLite, Bootstrap 5, and vanilla JavaScript.

---

## ✨ Features

| Feature | Details |
|---|---|
| 🔐 Auth | Register, Login, Logout, Session Management |
| 📋 Student Dashboard | Stats, recent complaints, quick actions |
| 📝 Submit Complaint | Title, description, category, image upload |
| 📁 My Complaints | Full table with status & priority badges |
| 🛡️ Admin Panel | Search, filter, update status/priority, delete |
| 📊 Admin Analytics | 5 KPI cards — total, pending, in-progress, resolved, high-priority |
| 🔔 Toast Notifications | Flash messages rendered as toast pop-ups |
| 📱 Responsive | Mobile sidebar, adaptive grid |

---

## 📂 Project Structure

```
campus-voice/
├── app.py                  ← Flask app (routes, auth, DB helpers)
├── init_db.py              ← One-time DB setup script
├── database.db             ← SQLite database (auto-created)
├── requirements.txt
├── static/
│   ├── css/
│   │   └── style.css       ← Full custom stylesheet
│   ├── js/
│   │   └── main.js         ← Toasts, sidebar, upload, modals
│   └── uploads/            ← Uploaded complaint images
└── templates/
    ├── base.html           ← Shared layout (sidebar + topbar)
    ├── home.html           ← Landing page
    ├── login.html          ← Login form
    ├── register.html       ← Registration form
    ├── dashboard.html      ← Student dashboard
    ├── complaint.html      ← Submit complaint form
    ├── my_complaints.html  ← Student complaints list
    └── admin.html          ← Admin panel
```

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip

### Step 1 — Clone / Download
```bash
# If using git:
git clone <your-repo-url>
cd campus-voice

# Or simply navigate into the project folder:
cd campus-voice
```

### Step 2 — Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3 — Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4 — Initialize Database
```bash
python init_db.py
```
This creates `database.db` and seeds the admin account.

### Step 5 — Run the Application
```bash
python app.py
```

Open your browser at: **http://localhost:5000**

---

## 🔑 Credentials

### Admin
| Field | Value |
|---|---|
| Email | `admin@campus.edu` |
| Password | `Admin@123` |

### Student
Register a new account at `/register`.

---

## 🗃️ Database Schema

### `users`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER | Primary key |
| name | TEXT | Full name |
| email | TEXT | Unique |
| password | TEXT | Hashed (Werkzeug) |
| role | TEXT | `student` or `admin` |
| created_at | TEXT | Auto timestamp |

### `complaints`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER | Primary key |
| user_id | INTEGER | FK → users.id |
| title | TEXT | Short title |
| description | TEXT | Full description |
| category | TEXT | One of 9 categories |
| image | TEXT | Filename in uploads/ |
| status | TEXT | Pending / Assigned / In Progress / Resolved |
| priority | TEXT | Low / Medium / High |
| created_at | TEXT | Submission timestamp |
| updated_at | TEXT | Last update timestamp |

---

## 🏷️ Complaint Categories
Classroom · Wi-Fi / Internet · Electrical · Laboratory · Library · Washroom · Canteen · Security · Other

## 📊 Complaint Statuses
`Pending` → `Assigned` → `In Progress` → `Resolved`

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML5, CSS3, JavaScript (ES6+) |
| UI Framework | Bootstrap 5.3 + Bootstrap Icons |
| Backend | Python Flask 3.0 |
| Database | SQLite (via sqlite3) |
| Auth | Werkzeug password hashing + Flask sessions |
| File Upload | Werkzeug secure_filename |

---

## ⚙️ Configuration

Edit `app.py` to change:
```python
app.secret_key = 'your-secret-key-here'   # Change in production!
MAX_CONTENT_LEN = 5 * 1024 * 1024         # Max upload size (5 MB)
ALLOWED_EXT = {'png','jpg','jpeg','gif','webp'}
```

---

## 📸 Pages Overview

| URL | Page | Access |
|---|---|---|
| `/` | Landing home | Public |
| `/register` | Student registration | Public |
| `/login` | Login | Public |
| `/dashboard` | Student dashboard | Student |
| `/complaint/new` | Submit complaint | Student |
| `/my-complaints` | My complaints list | Student |
| `/admin` | Admin panel | Admin only |
| `/api/complaint/<id>` | Complaint JSON detail | Admin only |

---

## 🔒 Security Notes

- Passwords are hashed with Werkzeug's `generate_password_hash` (PBKDF2-SHA256).
- File uploads are sanitized with `secure_filename` and type-checked.
- All student routes are protected with `@login_required`.
- All admin routes are protected with `@admin_required`.
- Change `app.secret_key` before deploying to production.

---

## 📦 Deployment (Optional)

For production, use Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

Or with a `Procfile` for platforms like Railway / Render:
```
web: gunicorn app:app
```

---

*Built with ❤️ for Campus Voice – Smart Complaint Management*
