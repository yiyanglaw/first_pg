from flask import Flask, request, render_template_string
import psycopg2
import os
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
cur.execute("""
CREATE TABLE IF NOT EXISTS texts (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL
)
""")
conn.commit()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'submit' in request.form:
            text = request.form['text']
            cur.execute("INSERT INTO texts (content) VALUES (%s)", (text,))
            conn.commit()
            return 'Text saved successfully!'
        elif 'view' in request.form:
            cur.execute("SELECT * FROM texts")
            rows = cur.fetchall()
            return render_template_string('''
                <form method="post">
                    <textarea name="text"></textarea>
                    <input type="submit" name="submit" value="Submit">
                </form>
                <form method="post">
                    <input type="submit" name="view" value="View All Data">
                </form>
                <h2>Stored Data:</h2>
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
            ''', rows=rows)
    return render_template_string('''
        <form method="post">
            <textarea name="text"></textarea>
            <input type="submit" name="submit" value="Submit">
        </form>
        <form method="post">
            <input type="submit" name="view" value="View All Data">
        </form>
    ''')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
