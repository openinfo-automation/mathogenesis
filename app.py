from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, emit
import threading, time, random, json, os

app = Flask(__name__)
# The secret key is required for session-based features in SocketIO
app.config['SECRET_KEY'] = 'math-secret!'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

# --- Persistence ---
DB_FILE = "knowledge_base.json"
running = False
knowledge_base = []

def load_db():
    global knowledge_base
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            knowledge_base = json.load(f)

def save_db(theorem):
    if theorem not in knowledge_base:
        knowledge_base.append(theorem)
        with open(DB_FILE, 'w') as f:
            json.dump(knowledge_base, f)

load_db()

# --- Logic ---
CONJECTURE_TEMPLATES = [
    "(a+b)^2 = a^2 + 2ab + b^2", "a^3 + b^3 = (a+b)(a^2 - ab + b^2)",
    "sum(k^2,0,n) = n(n+1)(2n+1)/6", "sum(k^3,0,n) = (n(n+1)/2)^2",
    "product(1+1/k,1,n) = n+1", "sum(r^k,0,n-1) = (1-r^n)/(1-r)"
]

def evolution_loop():
    global running
    while running:
        template = random.choice(CONJECTURE_TEMPLATES)
        conjecture = template
        if random.random() < 0.3:
            conjecture = conjecture.replace("a", "((a+1)+b)")

        # Logic: 15% chance to prove something new
        is_known = conjecture in knowledge_base
        if not is_known and random.random() < 0.15:
            save_db(conjecture)
            # Push specifically to the "proven" side via WebSocket
            socketio.emit('new_theorem', {'text': f"🎓 PROVED: {conjecture}"})
        else:
            # Push to the "discovery" side via WebSocket
            socketio.emit('discovery', {'text': f"Scanning: {conjecture}"})
        
        socketio.sleep(0.6) # Use socketio.sleep instead of time.sleep

# --- Routes & Socket Events ---
@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE, kb=knowledge_base)

@socketio.on('toggle_system')
def handle_toggle(data):
    global running
    if data['action'] == 'start' and not running:
        running = True
        socketio.start_background_task(evolution_loop)
    elif data['action'] == 'stop':
        running = False
    emit('status_change', {'running': running}, broadcast=True)

# --- Integrated HTML/JS ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>SocketIO Math Engine</title>
    <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
    <style>
        body { font-family: monospace; background: #050505; color: #00ffcc; padding: 20px; }
        .container { display: flex; gap: 20px; height: 80vh; margin-top: 20px;}
        .panel { flex: 1; background: #111; padding: 15px; border: 1px solid #333; overflow-y: auto; }
        .theorem { color: #00ff00; background: rgba(0,255,0,0.1); padding: 5px; margin-bottom: 5px; border-left: 3px solid #00ff00; }
        .discovery { color: #666; font-size: 0.9em; }
        .controls { background: #222; padding: 15px; display: flex; gap: 10px; align-items: center; }
        button { padding: 10px 20px; cursor: pointer; border: none; font-weight: bold; }
        #startBtn { background: #27ae60; color: white; }
        #stopBtn { background: #c0392b; color: white; }
    </style>
</head>
<body>
    <h1>WEBSOCKET MATHEMATICAL EVOLUTION</h1>
    <div class="controls">
        <button id="startBtn" onclick="sendAction('start')">START</button>
        <button id="stopBtn" onclick="sendAction('stop')" disabled>STOP</button>
        <span id="statusText">System: Offline</span>
    </div>
    <div class="container">
        <div class="panel"><h2>Live Stream</h2><div id="stream"></div></div>
        <div class="panel"><h2>Proven Database</h2><div id="kb">
            {% for t in kb %}<div class="theorem">🎓 LOADED: {{ t }}</div>{% endfor %}
        </div></div>
    </div>
    <script>
        const socket = io();
        function sendAction(act) { socket.emit('toggle_system', {action: act}); }

        socket.on('status_change', (data) => {
            document.getElementById('startBtn').disabled = data.running;
            document.getElementById('stopBtn').disabled = !data.running;
            document.getElementById('statusText').textContent = data.running ? "System: RUNNING" : "System: HALTED";
        });

        socket.on('discovery', (data) => {
            const div = document.createElement('div');
            div.className = 'discovery'; div.textContent = data.text;
            const s = document.getElementById('stream');
            s.prepend(div);
        });

        socket.on('new_theorem', (data) => {
            const div = document.createElement('div');
            div.className = 'theorem'; div.textContent = data.text;
            document.getElementById('kb').prepend(div);
        });
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    # Note: When using SocketIO + gevent, you run it differently
    socketio.run(app, host="0.0.0.0", port=10000)
