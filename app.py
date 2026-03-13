import sqlite3
import requests
from flask import Flask, render_template, redirect, url_for, request
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'wow_secret_key_123'

def init_db():
    conn = sqlite3.connect('wow.db')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY, content TEXT)')
    conn.commit()
    conn.close()

init_db()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

@app.route('/')
def index(): # or 'def home():' depending on your file
    price = "Data Unavailable"
    status = "Global Market Link: Offline"
    
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        # We add a User-Agent header because some APIs block Python's default "requests" identity
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, timeout=5, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            # Double check if 'bitcoin' actually exists in the data before grabbing it
            if 'bitcoin' in data:
                price = data['bitcoin']['usd']
                status = "Global Market Link: Online"
            else:
                print("DEBUG: API returned success but 'bitcoin' key was missing.")
        else:
            print(f"DEBUG: API returned status code {response.status_code}")

    except Exception as err: # We use 'err' here to avoid confusion
        print(f"API Error Detected: {err}")
        status = f"Connection Error: {err}"

    return render_template('index.html', price=price, status=status)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/links')
def links():
    
    my_projects = [
        {"name": "WowOS", "status": "Online"},
        {"name": "WowLink", "status": "Development"},
        {"name": "WowDocs", "status": "Pending"}
    ]
    return render_template('links.html', projects=my_projects)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_input = request.form.get('username')
        pass_input = request.form.get('password')
        
        print(f"DEBUG: Attempted login with User: '{user_input}' and Pass: '{pass_input}'")
        
        if user_input == 'admin' and pass_input == 'WowPass123':
            user = User(id='admin')
            login_user(user)
            return redirect(url_for('admin'))
        else:
            return "<h1>Login Failed!</h1><a href='/login'>Try again</a>"
            
    return render_template('login.html')

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    conn = sqlite3.connect('wow.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        # Check if they clicked 'Delete All'
        if 'delete_all' in request.form:
            cursor.execute('DELETE FROM logs')
            conn.commit()
        else:
            # Otherwise, it's a normal log post
            new_log = request.form.get('log_content')
            if new_log:
                cursor.execute('INSERT INTO logs (content) VALUES (?)', (new_log,))
                conn.commit()

    cursor.execute('SELECT * FROM logs ORDER BY id DESC')
    all_logs = cursor.fetchall()
    conn.close()
    return render_template('admin.html', logs=all_logs)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)