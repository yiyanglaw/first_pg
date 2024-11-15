from flask import Flask, request, render_template, send_file, abort, Response, redirect, url_for, flash, session, jsonify
import psycopg2
import os
import io
from urllib.parse import urlparse
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
import functools
from datetime import datetime, timedelta

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

DATABASE_URL = "postgresql://sql_db1_user:g8sxsV1TJYempiYrYKq77RBwnBc2oGan@dpg-csrjke56l47c73fg1mdg-a.singapore-postgres.render.com/sql_db1"

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
        medicine_frequency INTEGER NOT NULL,
        medicine_times TEXT[]
    )
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS heart_rates (
        id SERIAL PRIMARY KEY,
        patient_id INTEGER REFERENCES patients(id) ON DELETE CASCADE,
        date DATE NOT NULL,
        rate INTEGER NOT NULL
    )
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS medicine_intakes (
        id SERIAL PRIMARY KEY,
        patient_id INTEGER REFERENCES patients(id) ON DELETE CASCADE,
        date DATE NOT NULL,
        time TIME NOT NULL,
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
    
    query = f"SELECT * FROM patients WHERE LOWER(name) ILIKE LOWER(%s) OR phone ILIKE %s ORDER BY LOWER({sort}) {order}"
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
        medicine_frequency = int(request.form['medicine_frequency'])
        medicine_times = [request.form.get(f'medicine_time_{i}') for i in range(1, medicine_frequency + 1)]
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            cur.execute("""
            INSERT INTO patients (name, ic, phone, age, gender, address, image, medicine_type, medicine_interval, medicine_frequency, medicine_times)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """, (name, ic, phone, age, gender, address, psycopg2.Binary(image) if image else None, medicine_type, medicine_interval, medicine_frequency, medicine_times))
            
            patient_id = cur.fetchone()[0]
            
            # Initialize medicine intakes for today
            today = datetime.now().date()
            for time in medicine_times:
                cur.execute("""
                INSERT INTO medicine_intakes (patient_id, date, time, taken)
                VALUES (%s, %s, %s, %s)
                """, (patient_id, today, time, False))
            
            conn.commit()
            flash('Patient added successfully.', 'success')
            return redirect(url_for('main'))
        except psycopg2.IntegrityError as e:
            conn.rollback()
            if "patients_ic_key" in str(e):
                flash('A patient with this IC already exists.', 'danger')
            else:
                flash('An error occurred while adding the patient.', 'danger')
        finally:
            cur.close()
            conn.close()
    
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
        medicine_frequency = int(request.form['medicine_frequency'])
        medicine_times = [request.form.get(f'medicine_time_{i}') for i in range(1, medicine_frequency + 1)]
        
        try:
            if image:
                cur.execute("""
                UPDATE patients 
                SET name=%s, ic=%s, phone=%s, age=%s, gender=%s, address=%s, image=%s, 
                    medicine_type=%s, medicine_interval=%s, medicine_frequency=%s, medicine_times=%s
                WHERE id=%s
                """, (name, ic, phone, age, gender, address, psycopg2.Binary(image), 
                      medicine_type, medicine_interval, medicine_frequency, medicine_times, id))
            else:
                cur.execute("""
                UPDATE patients 
                SET name=%s, ic=%s, phone=%s, age=%s, gender=%s, address=%s, 
                    medicine_type=%s, medicine_interval=%s, medicine_frequency=%s, medicine_times=%s
                WHERE id=%s
                """, (name, ic, phone, age, gender, address, 
                      medicine_type, medicine_interval, medicine_frequency, medicine_times, id))
            
            conn.commit()
            flash('Patient updated successfully.', 'success')
            return redirect(url_for('main'))
        except psycopg2.IntegrityError as e:
            conn.rollback()
            if "patients_ic_key" in str(e):
                flash('A patient with this IC already exists.', 'danger')
            else:
                flash('An error occurred while updating the patient.', 'danger')
    
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
            cur.execute("DELETE FROM heart_rates WHERE patient_id = %s", (id,))
            cur.execute("DELETE FROM medicine_intakes WHERE patient_id = %s", (id,))
            cur.execute("DELETE FROM patients WHERE id = %s", (id,))
            conn.commit()
            flash('Patient and associated records deleted successfully.', 'success')
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
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT medicine_frequency, medicine_times FROM patients WHERE id = %s", (patient_id,))
    patient_data = cur.fetchone()
    medicine_frequency = patient_data[0]
    medicine_times = patient_data[1]
    
    # Delete existing intakes for the given date
    cur.execute("DELETE FROM medicine_intakes WHERE patient_id = %s AND date = %s", (patient_id, date))
    
    for i in range(1, medicine_frequency + 1):
        time = medicine_times[i-1]
        taken = request.form.get(f'taken_{i}') == 'yes'
        
        cur.execute("INSERT INTO medicine_intakes (patient_id, date, time, taken) VALUES (%s, %s, %s, %s)", 
                    (patient_id, date, time, taken))
    
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
        
@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM patients")
    total_patients = cur.fetchone()[0]
    
    today = datetime.now().date()
    cur.execute("SELECT COUNT(*) FROM medicine_intakes WHERE date = %s", (today,))
    medicine_intakes_today = cur.fetchone()[0]
    
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    cur.execute("""
    SELECT p.name, COUNT(*) as missed_doses
    FROM patients p
    LEFT JOIN medicine_intakes mi ON p.id = mi.patient_id
    WHERE mi.date BETWEEN %s AND %s AND mi.taken = FALSE
    GROUP BY p.id
    ORDER BY missed_doses DESC
    LIMIT 5
    """, (week_ago, today))
    missed_doses_week = cur.fetchall()
    
    cur.execute("""
    SELECT p.name, AVG(hr.rate) as avg_rate
    FROM patients p
    JOIN heart_rates hr ON p.id = hr.patient_id
    WHERE hr.date BETWEEN %s AND %s
    GROUP BY p.id
    HAVING 
        (p.age BETWEEN 1 AND 2 AND (AVG(hr.rate) < 80 OR AVG(hr.rate) > 130)) OR
        (p.age BETWEEN 3 AND 5 AND (AVG(hr.rate) < 80 OR AVG(hr.rate) > 120)) OR
        (p.age BETWEEN 6 AND 12 AND (AVG(hr.rate) < 70 OR AVG(hr.rate) > 110)) OR
        (p.age BETWEEN 13 AND 18 AND (AVG(hr.rate) < 60 OR AVG(hr.rate) > 100)) OR
        (p.age >= 19 AND (AVG(hr.rate) < 60 OR AVG(hr.rate) > 100))
    ORDER BY avg_rate DESC
    LIMIT 5
    """, (month_ago, today))
    unhealthy_heart_rates = cur.fetchall()
    
    patient_name = request.form.get('patient_name', '')
    if patient_name:
        cur.execute("""
        SELECT p.id, p.name, p.medicine_frequency, p.medicine_times, mi.date, mi.time, mi.taken, hr.rate
        FROM patients p
        LEFT JOIN medicine_intakes mi ON p.id = mi.patient_id
        LEFT JOIN heart_rates hr ON p.id = hr.patient_id AND mi.date = hr.date
        WHERE LOWER(p.name) LIKE LOWER(%s)
        ORDER BY mi.date DESC, mi.time DESC
        """, (f'%{patient_name}%',))
        patient_records = cur.fetchall()
        
        if patient_records:
            patient_id = patient_records[0][0]
            cur.execute("SELECT age FROM patients WHERE id = %s", (patient_id,))
            patient_age = cur.fetchone()[0] if cur.rowcount > 0 else None
            heart_rate_levels = []
            for record in patient_records:
                if record[7]:  # If heart rate is recorded
                    rate = record[7]
                    if 1 <= patient_age <= 2:
                        level = 'Normal' if 80 <= rate <= 130 else 'Abnormal'
                    elif 3 <= patient_age <= 5:
                        level = 'Normal' if 80 <= rate <= 120 else 'Abnormal'
                    elif 6 <= patient_age <= 12:
                        level = 'Normal' if 70 <= rate <= 110 else 'Abnormal'
                    elif 13 <= patient_age <= 18:
                        level = 'Normal' if 60 <= rate <= 100 else 'Abnormal'
                    else:
                        level = 'Normal' if 60 <= rate <= 100 else 'Abnormal'
                    heart_rate_levels.append(level)
                else:
                    heart_rate_levels.append('No data')
            
            # Group medicine intakes by date
            grouped_records = {}
            for record in patient_records:
                date = record[4]
                if date not in grouped_records:
                    grouped_records[date] = {
                        'date': date,
                        'intakes': [{'time': record[5], 'taken': record[6]}],
                        'heart_rate': record[7]
                    }
                else:
                    grouped_records[date]['intakes'].append({'time': record[5], 'taken': record[6]})
            
            # Sort intakes by time for each date
            for date, data in grouped_records.items():
                data['intakes'].sort(key=lambda x: x['time'])
            
            # Convert back to list and sort by date
            patient_records = sorted(grouped_records.values(), key=lambda x: x['date'], reverse=True)
        else:
            patient_records = []
            heart_rate_levels = []
    else:
        patient_records = []
        heart_rate_levels = []
    
    cur.close()
    conn.close()
    
    return render_template('dashboard.html', 
                           total_patients=total_patients,
                           medicine_intakes_today=medicine_intakes_today,
                           missed_doses_week=missed_doses_week,
                           unhealthy_heart_rates=unhealthy_heart_rates,
                           patient_records=patient_records,
                           heart_rate_levels=heart_rate_levels)

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
