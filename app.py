from flask import Flask, request, render_template_string, send_file, abort, Response
import psycopg2
import os
import io
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)

# Database connection parameters from environment variable
DATABASE_URL = os.getenv('DATABASE_URL')

# Parse the database URL
result = urlparse(DATABASE_URL)
username = result.username
password = result.password
database = result.path[1:]
hostname = result.hostname
port = result.port

# Connect to the database
conn = psycopg2.connect(
    dbname=database,
    user=username,
    password=password,
    host=hostname,
    port=port
)

cur = conn.cursor()

# Create tables for name, age, date, and images
cur.execute("""
CREATE TABLE IF NOT EXISTS names (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS ages (
    id SERIAL PRIMARY KEY,
    age INTEGER NOT NULL
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS dates (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS images (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    image BYTEA NOT NULL
)
""")
conn.commit()

@app.route('/', methods=['GET', 'POST'])
def index():
    message = ""
    if request.method == 'POST':
        if 'submit_name' in request.form:
            name = request.form['name']
            cur.execute("INSERT INTO names (name) VALUES (%s)", (name,))
            conn.commit()
            message = 'Name saved successfully!'
        elif 'submit_age' in request.form:
            age = request.form['age']
            cur.execute("INSERT INTO ages (age) VALUES (%s)", (age,))
            conn.commit()
            message = 'Age saved successfully!'
        elif 'submit_date' in request.form:
            date = request.form['date']
            cur.execute("INSERT INTO dates (date) VALUES (%s)", (date,))
            conn.commit()
            message = 'Date saved successfully!'
        elif 'view_name' in request.form:
            cur.execute("SELECT * FROM names")
            rows = cur.fetchall()
            return render_template_string(view_template, rows=rows, table_name="Names")
        elif 'view_age' in request.form:
            cur.execute("SELECT * FROM ages")
            rows = cur.fetchall()
            return render_template_string(view_template, rows=rows, table_name="Ages")
        elif 'view_date' in request.form:
            cur.execute("SELECT * FROM dates")
            rows = cur.fetchall()
            return render_template_string(view_template, rows=rows, table_name="Dates")
        elif 'upload_image' in request.form:
            name = request.form['name']
            image = request.files['image']
            if image:
                image_binary = image.read()
                cur.execute("INSERT INTO images (name, image) VALUES (%s, %s)", (name, psycopg2.Binary(image_binary)))
                conn.commit()
                message = 'Image uploaded successfully!'
        elif 'download_image' in request.form:
            name = request.form['name']
            cur.execute("SELECT image FROM images WHERE name = %s", (name,))
            result = cur.fetchone()
            if result:
                image_binary = result[0]
                return Response(image_binary, mimetype='image/jpeg', headers={"Content-Disposition": f"attachment;filename={name}.jpg"})
            else:
                message = "Image not uploaded for this name!"

    return render_template_string(main_template, message=message)

# Template strings
main_template = '''
    <form method="post">
        <h2>Submit Your Information</h2>
        Name: <input type="text" name="name"><br>
        Age: <input type="number" name="age"><br>
        Date: <input type="date" name="date"><br>
        <input type="submit" name="submit_name" value="Submit Name">
        <input type="submit" name="submit_age" value="Submit Age">
        <input type="submit" name="submit_date" value="Submit Date">
    </form>
    <br>
    <form method="post">
        <input type="submit" name="view_name" value="View All Names">
        <input type="submit" name="view_age" value="View All Ages">
        <input type="submit" name="view_date" value="View All Dates">
    </form>
    <br>
    <form method="post" enctype="multipart/form-data">
        <h2>Upload Your Image</h2>
        Name: <input type="text" name="name"><br>
        Image: <input type="file" name="image"><br>
        <input type="submit" name="upload_image" value="Upload Image">
    </form>
    <br>
    <form method="post">
        <h2>Download Your Image</h2>
        Name: <input type="text" name="name"><br>
        <input type="submit" name="download_image" value="Download Image">
    </form>
    <br>
    <h3>{{ message }}</h3>
'''

view_template = '''
    <h2>{{ table_name }}</h2>
    <table border="1">
        <tr>
            <th>ID</th>
            <th>Content</th>
        </tr>
        {% for row in rows %}
        <tr>
            <td>{{ row[0] }}</td>
            <td>{{ row[1] }}</td>
        </tr>
        {% endfor %}
    </table>
    <br>
    <a href="/">Go Back</a>
'''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
