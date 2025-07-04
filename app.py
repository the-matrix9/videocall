import json, os
from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
import requests

app = Flask(__name__)
app.secret_key = 'supersecretkey'
socketio = SocketIO(app, cors_allowed_origins='*')

USERS_FILE = 'users.json'
IMGBB_API_KEY = '6654d803dfda9a1777d8137ad566209e'  # Replace this with your real IMGBB API key

if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, 'w') as f:
        json.dump([], f)

def load_users():
    with open(USERS_FILE) as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def upload_to_imgbb(file):
    res = requests.post(
        'https://api.imgbb.com/1/upload',
        params={'key': IMGBB_API_KEY},
        files={'image': file}
    )
    return res.json()['data']['url']

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        file = request.files['dp']
        users = load_users()
        if any(u['username'] == username for u in users):
            return "User already exists!"
        dp_url = upload_to_imgbb(file)
        users.append({'username': username, 'password': password, 'dp': dp_url})
        save_users(users)
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_users()
        for user in users:
            if user['username'] == username and user['password'] == password:
                session['user'] = user
                return redirect(url_for('dashboard'))
        return "Invalid credentials"
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', user=session['user'])

@app.route('/call/<username>')
def call_user(username):
    users = load_users()
    for u in users:
        if u['username'] == username:
            return render_template('call.html', target=u, user=session['user'])
    return "User not found"

@socketio.on('connect')
def on_connect():
    sid = request.sid
    print(f"{sid} connected")


@socketio.on('signal')
def on_signal(data):
    sid = request.sid
    room = rooms.get(sid)
    print(f"Signal from {sid}: {data}")
    # broadcast to others in the room
    for client_id, r in rooms.items():
        if r == room and client_id != sid:
            socketio.emit('signal', data, to=client_id)

@socketio.on('join-room')
def on_join(data):
    sid = request.sid
    room_id = data.get('room')
    rooms[sid] = room_id
    join_room(room_id)
    print(f"{sid} joined room {room_id}")

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
