from flask import Flask, render_template, request, redirect, session
#from config import get_db_connection
import mysql.connector

app = Flask(__name__)
app.secret_key = "secret123"

def get_db_connection():
    configs = [
        
        {"host": "localhost", "user": "root", "password": " ", "database": "getpassdb"},
        
    ]
    

    last_error = None
    for config in configs:
        try:
            return mysql.connector.connect(**config)
        except mysql.connector.Error as exc:
            last_error = exc

    if last_error:
        raise last_error

    raise RuntimeError("MySQL connection failed for all known local configs.")

# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        mobile = request.form['mobile']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # STUDENT
        cursor.execute("SELECT * FROM students WHERE mobile_no=%s AND password=%s", (mobile, password))
        user = cursor.fetchone()
        if user:
            session['user'] = user['roll_no']
            session['role'] = 'student'
            return redirect('/student')

        # STAFF
        cursor.execute("SELECT * FROM staff WHERE mobile_no=%s AND password=%s", (mobile, password))
        user = cursor.fetchone()
        if user:
            session['user'] = user['staff_id']
            session['role'] = 'staff'
            return redirect('/staff')

        # HOD
        cursor.execute("SELECT * FROM hod WHERE mobile_no=%s AND password=%s", (mobile, password))
        user = cursor.fetchone()
        if user:
            session['user'] = user['staff_id']
            session['role'] = 'hod'
            return redirect('/hod')

        # ADMIN
        cursor.execute("SELECT * FROM admin WHERE username=%s AND password=%s", (mobile, password))
        user = cursor.fetchone()
        if user: 
            session['user'] = user['username']
            session['role'] = 'admin'
            return redirect('/admin')

        # SECURITY
        cursor.execute("SELECT * FROM security WHERE mobile_no=%s AND password=%s", (mobile, password))
        user = cursor.fetchone()
        if user:
            session['user'] = user['security_id']
            session['role'] = 'security'
            return redirect('/security')

        return "Invalid Login"

    return render_template('login.html')




# ---------------- STUDENT ----------------
@app.route('/student', methods=['GET', 'POST'])
def student():
    if session.get('role') != 'student':
        return redirect('/')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        reason = request.form['reason']
        out_time = request.form['out_time']

        cursor.execute("""
            INSERT INTO outpass_requests (outpass_id, roll_no, reason, out_time, status_staff, status_hod)
            VALUES (UUID(), %s, %s, %s, 'pending', 'pending')
        """, (session['user'], reason, out_time))
        conn.commit()

    cursor.execute("SELECT * FROM outpass_requests WHERE roll_no=%s", (session['user'],))
    data = cursor.fetchall()

    return render_template('student.html', data=data)
76

# ---------------- STAFF ----------------

@app.route('/staff')
def staff():
    if session.get('role') != 'staff':
        return redirect('/')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
SELECT o.*, s.name 
FROM outpass_requests o
JOIN students s ON o.roll_no = s.roll_no
""")
    data = cursor.fetchall()

    return render_template('staff.html', data=data)

    rejected = cursor.fetchall()

    return render_template('staff.html', data=data)

@app.route('/staff_action/<id>/<action>')
def staff_action(id, action):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE outpass_requests SET status_staff=%s WHERE id=%s", (action, id))
    conn.commit()

    return redirect('/staff')


# ---------------- HOD ----------------
@app.route('/hod')
def hod():
    if session.get('role') != 'hod':
        return redirect('/')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
    SELECT o.*, s.name 
    FROM outpass_requests o
    JOIN students s ON o.roll_no = s.roll_no
    WHERE o.status_staff='approved'
    """)
    data = cursor.fetchall()

    return render_template('hod.html', data=data)

@app.route('/hod_action/<id>/<action>')
def hod_action(id, action):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE outpass_requests SET status_hod=%s WHERE id=%s", (action, id))
    conn.commit()

    return redirect('/hod')


# ---------------- ADMIN ----------------
@app.route('/admin')
def admin():
    if session.get('role') != 'admin':
        return redirect('/')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM students")
    students = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM visitors")
    visitors = cursor.fetchone()[0]

    return render_template('admin.html', students=students, visitors=visitors)


# ---------------- SECURITY ----------------
@app.route('/security', methods=['GET', 'POST'])
def security():
    if session.get('role') != 'security':
        return redirect('/')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        name = request.form['name']
        mobile = request.form['mobile']
        reason = request.form['reason']

        cursor.execute("""
            INSERT INTO visitors (visitor_id, name, mobile_no, reason, entry_time)
            VALUES (UUID(), %s, %s, %s, NOW())
        """, (name, mobile, reason))
        conn.commit()

    cursor.execute("SELECT * FROM visitors")
    data = cursor.fetchall()

    return render_template('security.html', data=data)

@app.route('/manage_students', methods=['GET', 'POST'])
def manage_students():
    if session.get('role') != 'admin':
        return redirect('/')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # ADD STUDENT
    if request.method == 'POST':
        roll = request.form['roll']
        name = request.form['name']
        dept = request.form['dept']
        mobile = request.form['mobile']
        password = request.form['password']

        cursor.execute("""
            INSERT INTO students (roll_no, name, dept, mobile_no, password)
            VALUES (%s,%s,%s,%s,%s)
        """, (roll, name, dept, mobile, password))
        conn.commit()

    cursor.execute("SELECT * FROM students")
    data = cursor.fetchall()

    return render_template('manage_students.html', data=data)
@app.route('/delete_student/<id>')
def delete_student(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM students WHERE id=%s", (id,))
    conn.commit()

    return redirect('/manage_students')

@app.route('/manage_staff', methods=['GET', 'POST'])
def manage_staff():
    if session.get('role') != 'admin':
        return redirect('/')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        staff_id = request.form['staff_id']
        name = request.form['name']
        dept = request.form['dept']
        mobile = request.form['mobile']
        password = request.form['password']

        cursor.execute("""
            INSERT INTO staff (staff_id, staff_name, dept_name, mobile_no, password)
            VALUES (%s,%s,%s,%s,%s)
        """, (staff_id, name, dept, mobile, password))
        conn.commit()

    cursor.execute("SELECT * FROM staff")
    data = cursor.fetchall()

    return render_template('manage_staff.html', data=data)

@app.route('/delete_staff/<id>')
def delete_staff(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM staff WHERE id=%s", (id,))
    conn.commit()

    return redirect('/manage_staff')
@app.route('/manage_hod', methods=['GET', 'POST'])
def manage_hod():
    if session.get('role') != 'admin':
        return redirect('/')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        staff_id = request.form['staff_id']
        name = request.form['name']
        dept = request.form['dept']
        mobile = request.form['mobile']
        password = request.form['password']

        cursor.execute("""
            INSERT INTO hod (staff_id, staff_name, dept_name, mobile_no, password)
            VALUES (%s,%s,%s,%s,%s)
        """, (staff_id, name, dept, mobile, password))
        conn.commit()

    cursor.execute("SELECT * FROM hod")
    data = cursor.fetchall()

    return render_template('manage_hod.html', data=data)
@app.route('/delete_hod/<id>')
def delete_hod(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM hod WHERE id=%s", (id,))
    conn.commit()

    return redirect('/manage_hod')


@app.route('/manage_security', methods=['GET', 'POST'])
def manage_security():
    if session.get('role') != 'admin':
        return redirect('/')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        sec_id = request.form['sec_id']
        name = request.form['name']
        mobile = request.form['mobile']
        password = request.form['password']

        cursor.execute("""
            INSERT INTO security (security_id, security_name, mobile_no, password)
            VALUES (%s,%s,%s,%s)
        """, (sec_id, name, mobile, password))
        conn.commit()

    cursor.execute("SELECT * FROM security")
    data = cursor.fetchall()

    return render_template('manage_security.html', data=data)

@app.route('/delete_security/<id>')
def delete_security(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM security WHERE id=%s", (id,))
    conn.commit()

    return redirect('/manage_security')
@app.route('/receipt/<id>')
def receipt(id):
    if session.get('role') not in ['student','staff','hod','security','admin']:
        return redirect('/')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT o.*, s.name, s.dept 
        FROM outpass_requests o
        JOIN students s ON o.roll_no = s.roll_no
        WHERE o.id=%s
    """, (id,))

    data = cursor.fetchone()

    if data['status_staff'] != 'approved' or data['status_hod'] != 'approved':
        return "Pass not fully approved!"

    return render_template('receipt.html', data=data)
@app.route('/visitor_exit/<id>')
def visitor_exit(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE visitors SET exit_time = NOW() WHERE id = %s", (id,))
    conn.commit()

    return redirect('/security')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        roll = request.form.get('roll')
        name = request.form.get('name')
        dept = request.form.get('dept')
        mobile = request.form.get('mobile')
        password = request.form.get('password')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "INSERT INTO students (roll_no, name, dept, mobile_no, password) VALUES (%s, %s, %s, %s, %s)",
            (roll, name, dept, mobile, password)
        )
        conn.commit()
        return redirect('/student_login')

    return render_template('register.html')

@app.route('/')
def home():
    return render_template('home.html')
@app.route('/student_login', methods=['GET','POST'])
def student_login():
    if request.method == 'POST':
        mobile = request.form['mobile']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM students WHERE mobile_no=%s AND password=%s", (mobile,password))
        user = cursor.fetchone()

        if user:
            session['user'] = user['roll_no']
            session['role'] = 'student'
            return redirect('/student')

        return "Invalid Login"

    return render_template('student_login.html')
@app.route('/staff_login', methods=['GET','POST'])
def staff_login():
    if request.method == 'POST':
        mobile = request.form['mobile']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # STAFF
        cursor.execute("SELECT * FROM staff WHERE mobile_no=%s AND password=%s",(mobile,password))
        user = cursor.fetchone()
        if user:
            session['user'] = user['staff_id']
            session['role'] = 'staff'
            return redirect('/staff')

        # HOD
        cursor.execute("SELECT * FROM hod WHERE mobile_no=%s AND password=%s",(mobile,password))
        user = cursor.fetchone()
        if user:
            session['user'] = user['staff_id']
            session['role'] = 'hod'
            return redirect('/hod')

        # ADMIN
        cursor.execute("SELECT * FROM admin WHERE username=%s AND password=%s",(mobile,password))
        user = cursor.fetchone()
        if user:
            session['user'] = user['username']
            session['role'] = 'admin'
            return redirect('/admin')

        return "Invalid Login"

    return render_template('staff_login.html')

@app.route('/admin_login', methods=['GET','POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username') or request.form.get('mobile')
        password = request.form.get('password')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM admin WHERE username=%s AND password=%s", (username, password))
        user = cursor.fetchone()

        if user:
            session['user'] = user['username']
            session['role'] = 'admin'
            return redirect('/admin')

        return "Invalid Admin Login"

    return render_template('admin_login.html')

@app.route('/security_login', methods=['GET','POST'])
def security_login():
    if request.method == 'POST':
        mobile = request.form['mobile']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM security WHERE mobile_no=%s AND password=%s",(mobile,password))
        user = cursor.fetchone()

        if user:
            session['user'] = user['security_id']
            session['role'] = 'security'
            return redirect('/security')

        return "Invalid Login"

    return render_template('security_login.html')


# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


if __name__ == "__main__":
    app.run(debug=True)


    #---------------------------
    import mysql.connector
