import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps

app = Flask(__name__)
app.secret_key = 'hiit_secret_defense_key'
DB_NAME = 'portal.db'

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'password123'

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            duration TEXT NOT NULL,
            fee TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS enrollments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            course_id INTEGER NOT NULL,
            registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'Pending',
            FOREIGN KEY (course_id) REFERENCES courses (id)
        )
    ''')
    cursor.execute('SELECT COUNT(*) FROM courses')
    if cursor.fetchone()[0] == 0:
        sample_courses = [
            ('Python for Data Science', 'Software & Data', '8 Weeks', '₦120,000'),
            ('Full-Stack Web Development', 'Software & Data', '12 Weeks', '₦150,000'),
            ('Cisco Certified Network Associate (CCNA)', 'Networking', '10 Weeks', '₦140,000'),
            ('CompTIA Cyber Security Analyst (CySA+)', 'Cybersecurity', '8 Weeks', '₦160,000')
        ]
        cursor.executemany('INSERT INTO courses (title, category, duration, fee) VALUES (?, ?, ?, ?)', sample_courses)
    conn.commit()
    conn.close()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            flash('Admin authentication required.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    conn = get_db_connection()
    courses = conn.execute('SELECT * FROM courses ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('index.html', courses=courses)

@app.route('/enroll', methods=['GET', 'POST'])
def enroll():
    conn = get_db_connection()
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        phone = request.form['phone']
        course_id = request.form['course_id']
        conn.execute('INSERT INTO enrollments (full_name, email, phone, course_id) VALUES (?, ?, ?, ?)', (full_name, email, phone, course_id))
        conn.commit()
        conn.close()
        flash('Enrollment submitted successfully!', 'success')
        return redirect(url_for('index'))
    selected_course_id = request.args.get('course_id')
    courses = conn.execute('SELECT * FROM courses').fetchall()
    conn.close()
    return render_template('enroll.html', courses=courses, selected_course_id=selected_course_id)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['is_admin'] = True
            flash('Signed in as Admin.', 'success')
            return redirect(url_for('admin'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('is_admin', None)
    flash('Logged out successfully.', 'info')
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin():
    conn = get_db_connection()
    enrollments = conn.execute('''
        SELECT e.id, e.full_name, e.email, e.phone, e.registration_date, e.status, c.title AS course_title 
        FROM enrollments e 
        JOIN courses c ON e.course_id = c.id 
        ORDER BY e.registration_date DESC
    ''').fetchall()
    courses = conn.execute('SELECT * FROM courses ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('admin.html', enrollments=enrollments, courses=courses)

@app.route('/admin/add_course', methods=['POST'])
@login_required
def add_course():
    title = request.form['title']
    category = request.form['category']
    duration = request.form['duration']
    fee = request.form['fee']
    if title and category and duration and fee:
        conn = get_db_connection()
        conn.execute('INSERT INTO courses (title, category, duration, fee) VALUES (?, ?, ?, ?)', (title, category, duration, fee))
        conn.commit()
        conn.close()
        flash(f'Course "{title}" added successfully!', 'success')
    return redirect(url_for('admin'))

@app.route('/admin/update_status/<int:enrollment_id>/<string:new_status>')
@login_required
def update_status(enrollment_id, new_status):
    conn = get_db_connection()
    conn.execute('UPDATE enrollments SET status = ? WHERE id = ?', (new_status, enrollment_id))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

init_db()
print("SERVER RUNNING! Open http://127.0.0.1:5000")
app.run(host="127.0.0.1", port=5000, debug=False)
