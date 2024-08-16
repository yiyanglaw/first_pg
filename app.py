from flask import Flask, request, render_template, send_file, abort, Response, redirect, url_for, flash, session
import psycopg2
import os
import io
from urllib.parse import urlparse
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
import functools
from flask import jsonify


load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

DATABASE_URL = os.getenv('DATABASE_URL')

result = urlparse(DATABASE_URL)
username = result.username
password = result.password
database = result.path[1:]
hostname = result.hostname
port = result.port

def get_db_connection():
    return psycopg2.connect(
        dbname=database,
        user=username,
        password=password,
        host=hostname,
        port=port
    )

def create_tables():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS patients (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        ic TEXT UNIQUE NOT NULL,
        phone TEXT NOT NULL,
        age INTEGER NOT NULL,
        gender TEXT NOT NULL,
        address TEXT NOT NULL,
        image BYTEA,
        medicine_type TEXT NOT NULL,
        medicine_interval INTEGER NOT NULL,
        medicine_frequency INTEGER NOT NULL
    )
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS heart_rates (
        id SERIAL PRIMARY KEY,
        patient_id INTEGER REFERENCES patients(id),
        date DATE NOT NULL,
        rate INTEGER NOT NULL
    )
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS medicine_intakes (
        id SERIAL PRIMARY KEY,
        patient_id INTEGER REFERENCES patients(id),
        date DATE NOT NULL,
        taken BOOLEAN NOT NULL
    )
    """)
    
    conn.commit()
    cur.close()
    conn.close()

create_tables()

def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
            conn.commit()
            flash('Registration successful. Please log in.', 'success')
            return redirect(url_for('login'))
        except psycopg2.IntegrityError:
            conn.rollback()
            flash('Username already exists.', 'danger')
        finally:
            cur.close()
            conn.close()
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        
        cur.close()
        conn.close()
        
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            flash('Login successful.', 'success')
            return redirect(url_for('main'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))

@app.route('/main')
@login_required
def main():
    conn = get_db_connection()
    cur = conn.cursor()
    
    search = request.args.get('search', '')
    sort = request.args.get('sort', 'name')
    order = request.args.get('order', 'asc')
    
    query = f"SELECT * FROM patients WHERE name ILIKE %s OR phone ILIKE %s ORDER BY {sort} {order}"
    cur.execute(query, (f'%{search}%', f'%{search}%'))
    patients = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template('main.html', patients=patients)

@app.route('/add_patient', methods=['GET', 'POST'])
@login_required
def add_patient():
    if request.method == 'POST':
        name = request.form['name']
        ic = request.form['ic']
        phone = request.form['phone']
        age = request.form['age']
        gender = request.form['gender']
        address = request.form['address']
        image = request.files['image'].read() if 'image' in request.files else None
        medicine_type = request.form['medicine_type']
        medicine_interval = request.form['medicine_interval']
        medicine_frequency = request.form['medicine_frequency']
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
        INSERT INTO patients (name, ic, phone, age, gender, address, image, medicine_type, medicine_interval, medicine_frequency)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (name, ic, phone, age, gender, address, psycopg2.Binary(image) if image else None, medicine_type, medicine_interval, medicine_frequency))
        
        conn.commit()
        cur.close()
        conn.close()
        
        flash('Patient added successfully.', 'success')
        return redirect(url_for('main'))
    
    return render_template('add_patient.html')

@app.route('/update_patient/<int:id>', methods=['GET', 'POST'])
@login_required
def update_patient(id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    if request.method == 'POST':
        name = request.form['name']
        ic = request.form['ic']
        phone = request.form['phone']
        age = request.form['age']
        gender = request.form['gender']
        address = request.form['address']
        image = request.files['image'].read() if 'image' in request.files else None
        medicine_type = request.form['medicine_type']
        medicine_interval = request.form['medicine_interval']
        medicine_frequency = request.form['medicine_frequency']
        
        if image:
            cur.execute("""
            UPDATE patients 
            SET name=%s, ic=%s, phone=%s, age=%s, gender=%s, address=%s, image=%s, 
                medicine_type=%s, medicine_interval=%s, medicine_frequency=%s
            WHERE id=%s
            """, (name, ic, phone, age, gender, address, psycopg2.Binary(image), 
                  medicine_type, medicine_interval, medicine_frequency, id))
        else:
            cur.execute("""
            UPDATE patients 
            SET name=%s, ic=%s, phone=%s, age=%s, gender=%s, address=%s, 
                medicine_type=%s, medicine_interval=%s, medicine_frequency=%s
            WHERE id=%s
            """, (name, ic, phone, age, gender, address, 
                  medicine_type, medicine_interval, medicine_frequency, id))
        
        conn.commit()
        flash('Patient updated successfully.', 'success')
        return redirect(url_for('main'))
    
    cur.execute("SELECT * FROM patients WHERE id = %s", (id,))
    patient = cur.fetchone()
    
    cur.close()
    conn.close()
    
    return render_template('update_patient.html', patient=patient)

@app.route('/delete_patient/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_patient(id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM patients WHERE id = %s", (id,))
    patient = cur.fetchone()
    
    if patient is None:
        flash('Patient not found.', 'danger')
        return redirect(url_for('main'))
    
    if request.method == 'POST':
        if request.form.get('confirm') == 'yes':
            cur.execute("DELETE FROM patients WHERE id = %s", (id,))
            conn.commit()
            flash('Patient deleted successfully.', 'success')
            return redirect(url_for('main'))
    
    cur.close()
    conn.close()
    
    return render_template('delete_patient.html', patient=patient)

@app.route('/add_heart_rate/<int:patient_id>', methods=['POST'])
@login_required
def add_heart_rate(patient_id):
    date = request.form['date']
    rate = request.form['rate']
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("INSERT INTO heart_rates (patient_id, date, rate) VALUES (%s, %s, %s)", 
                (patient_id, date, rate))
    conn.commit()
    
    cur.close()
    conn.close()
    
    flash('Heart rate added successfully.', 'success')
    return redirect(url_for('update_patient', id=patient_id))

@app.route('/add_medicine_intake/<int:patient_id>', methods=['POST'])
@login_required
def add_medicine_intake(patient_id):
    date = request.form['date']
    taken = request.form['taken'] == 'yes'
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("INSERT INTO medicine_intakes (patient_id, date, taken) VALUES (%s, %s, %s)", 
                (patient_id, date, taken))
    conn.commit()
    
    cur.close()
    conn.close()
    
    flash('Medicine intake recorded successfully.', 'success')
    return redirect(url_for('update_patient', id=patient_id))

@app.route('/download_image/<int:patient_id>')
@login_required
def download_image(patient_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT image FROM patients WHERE id = %s", (patient_id,))
    image = cur.fetchone()[0]
    
    cur.close()
    conn.close()
    
    if image:
        return send_file(
            io.BytesIO(image),
            mimetype='image/jpeg',
            as_attachment=True,
            download_name=f'patient_{patient_id}_image.jpg'
        )
    else:
        abort(404)
        
@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM patients")
    total_patients = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM patients WHERE DATE_TRUNC('month', created_at) = DATE_TRUNC('month', CURRENT_DATE)")
    new_patients_this_month = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM medicine_intakes WHERE date = CURRENT_DATE")
    medicine_intakes_today = cur.fetchone()[0]
    
    cur.close()
    conn.close()
    
    return render_template('dashboard.html', 
                           total_patients=total_patients,
                           new_patients_this_month=new_patients_this_month,
                           medicine_intakes_today=medicine_intakes_today)


@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

@app.route('/api/patients')
@login_required
def api_patients():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM patients")
        patients = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify([dict(zip([column[0] for column in cur.description], patient)) for patient in patients])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5100, debug=True)