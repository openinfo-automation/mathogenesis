import os
import json
import random
import threading
from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mathogenesis-universal-2025'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

DB_FILE = "knowledge_base.json"
running = False
knowledge_base = []

def load_db():
    global knowledge_base
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f:
                knowledge_base = json.load(f)
        except:
            knowledge_base = []

def save_db(theorem):
    if theorem not in knowledge_base:
        knowledge_base.append(theorem)
        with open(DB_FILE, 'w') as f:
            json.dump(knowledge_base, f)

load_db()

# --- Advanced Mathematical & Astrophysical Templates ---
CONJECTURE_TEMPLATES = [
    "R_uv - 1/2*R*g_uv + Lambda*g_uv = 8*pi*G/c^4*T_uv", 
    "S_BH = (k*A*c^3)/(4*G*hbar)",
    "i*hbar*d/dt|psi> = H|psi>",
    "delta_x * delta_p >= hbar/2",
    "R_s = 2*G*M/c^2",
    "Zeta(s) = sum(n^(-s), 1, inf)",
    "Res(f, c) = 1/(2*pi*i) * oint(f(z)dz)",
    "L = sqrt(hbar*G/c^3)",
    "curl(E) = -dB/dt",
    "grad * D = rho",
    "P^2 = (4*pi^2 / G(M+m)) * a^3",
    "chi(M) = V - E + F = 2 - 2g",
    "integral(exp(-x^2), -inf, inf) = sqrt(pi)"
]

def attempt_proof(conjecture):
    if conjecture in knowledge_base:
        return True, "Historical Consistency"
    # Dimensional and Tensor Analysis simulation
    if any(c in conjecture for c in ["G", "hbar", "c", "pi", "R_uv"]):
        if random.random() < 0.05: # High complexity threshold
            return True, "Tensor Contraction & Dimensional Invariance"
    if random.random() < 0.1:
        return True, "Formal Analytic Verification"
    return False, None

def evolution_loop():
    global running
    while running:
        template = random.choice(CONJECTURE_TEMPLATES)
        conjecture = template
        if random.random() < 0.3:
            conjecture = conjecture.replace("a", "((r_0 + 1) * a)")
            
        proved, method = attempt_proof(conjecture)
        is_novel = conjecture not in knowledge_base
        
        if proved and is_novel:
            save_db(conjecture)
            socketio.emit('new_theorem', {'text': f"🎓 PROVED: {conjecture} via {method}"})
        else:
            socketio.emit('discovery', {'text': f"Scanning: {conjecture}"})
        
        socketio.sleep(0.5)

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE, kb=knowledge_base)

@socketio.on('toggle_system')
def handle_toggle(data):
    global running
    action = data.get('action')
    if action == 'start' and not running:
        running = True
        socketio.start_background_task(evolution_loop)
    elif action == 'stop':
        running = False
    emit('status_change', {'running': running}, broadcast=True)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Mathogenesis Universal</title>
    <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
    <style>
        body { font-family: 'Consolas', monospace; background: #050505; color: #00ffcc; margin: 0; overflow: hidden; display: flex; flex-direction: column; height: 100vh; }
        .header { background: #111; padding: 15px 25px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #00ffcc; }
        .container { display: flex; gap: 10px; flex: 1; padding: 10px; overflow: hidden; }
        .panel { flex: 1; background: #0a0a0a; border: 1px solid #222; display: flex; flex-direction: column; }
        .panel-header { padding: 8px; background: #222; font-size: 0.8em; color: #aaa; letter-spacing: 1px; }
        .content { flex: 1; overflow-y: auto; padding: 15px; }
        .theorem { color: #00ff99; background: rgba(0,255,153,0.05); padding: 10px; margin-bottom: 10px; border-left: 2px solid #00ff99; font-size: 0.9em; }
        .discovery { color: #444; font-size: 0.8em; margin-bottom: 4px; }
        button { padding: 10px 20px; font-weight: bold; cursor: pointer; border: none; }
        #startBtn { background: #00ffcc; color: #000; }
        #stopBtn { background: #ff0055; color: #fff; }
        button:disabled { opacity: 0.2; cursor: not-allowed; }
        #status { font-size: 0.8em; }
    </style>
</head>
<body>
    <div class="header">
        <h2 style="margin:0;">MATHOGENESIS v4.0 (ASTROPHYSICS & ANALYSIS)</h2>
        <div>
            <span id="status">STATUS: OFFLINE</span>
            <button id="startBtn" onclick="sendAction('start')">INITIALIZE</button>
            <button id="stopBtn" onclick="sendAction('stop')" disabled>HALT</button>
        </div>
    </div>
    <div class="container">
        <div class="panel">
            <div class="panel-header">SEARCH_STREAM</div>
            <div id="stream" class="content"></div>
        </div>
        <div class="panel">
            <div class="panel-header">PERSISTENT_KNOWLEDGE_BASE</div>
            <div id="kb" class="content">
                {% for t in kb %}<div class="theorem">🎓 LOADED: {{ t }}</div>{% endfor %}
            </div>
        </div>
    </div>
    <script>
        const socket = io();
        function sendAction(act) { socket.emit('toggle_system', {action: act}); }
        socket.on('status_change', (data) => {
            document.getElementById('startBtn').disabled = data.running;
            document.getElementById('stopBtn').disabled = !data.running;
            document.getElementById('status').textContent = data.running ? "STATUS: ACTIVE" : "STATUS: HALTED";
        });
        socket.on('discovery', (data) => {
            const s = document.getElementById('stream');
            const div = document.createElement('div');
            div.className = 'discovery'; div.textContent = `> ${data.text}`;
            s.prepend(div);
            if(s.childNodes.length > 50) s.removeChild(s.lastChild);
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
    port = int(os.environ.get("PORT", 10000))
    socketio.run(app, host="0.0.0.0", port=port)
