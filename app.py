from gevent import monkey
monkey.patch_all()  # Must remain at the very top for Render/Gevent stability

import os
import json
import random
import threading
from flask import Flask, render_template_string, send_file
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mathogenesis-recursive-2025'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

DB_FILE = "knowledge_base.json"
ALIEN_FILE = "alien_knowledge.json"
RUNNING_FLAG = "SYSTEM_ON.flag"
db_lock = threading.Lock()

# --- SYSTEM STATE ---
running = os.path.exists(RUNNING_FLAG)
knowledge_base = []
alien_theorems = []
agents_spawned = 0
novel_conjectures = 0
proven_theorems = 0

def load_db():
    global knowledge_base, alien_theorems
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f:
                knowledge_base = json.load(f)
        except: knowledge_base = []
    
    if os.path.exists(ALIEN_FILE):
        try:
            with open(ALIEN_FILE, 'r') as f:
                alien_theorems = json.load(f)
        except: alien_theorems = []

def save_to_json(file_path, data_list, item):
    with db_lock:
        if item not in data_list:
            data_list.append(item)
            with open(file_path, 'w') as f:
                json.dump(data_list, f)

load_db()

# --- CONJECTURE TEMPLATES ---
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

def mutate_conjecture(template):
    mutation_attempts = [
        lambda c: c.replace("a", "((r_0 + 1) * a)") if "a" in c else c + " + ∇_alien",
        lambda c: c.replace("G", "(G / ε_0)") if "G" in c else c + " * Ξ",
        lambda c: c.replace("hbar", "(ħ * κ)") if "hbar" in c or "ħ" in c else c + " + ħ_prime",
        lambda c: f"Ψ({c})" if len(c) < 50 else c[:20] + "..." 
    ]
    return random.choice(mutation_attempts)(template)

def attempt_proof(conjecture):
    if conjecture in knowledge_base or conjecture in alien_theorems:
        return False, "Redundant"
    weight = sum(1 for char in ["G", "ħ", "π", "∫", "∑", "Ξ"] if char in conjecture)
    if random.random() < (0.08 + (weight * 0.01)):
        return True, "Symbolic Convergence"
    return False, None

def evolution_loop():
    global running, agents_spawned, novel_conjectures, proven_theorems
    while running:
        agents_spawned += 1
        # XENO-RECURSIVE POOL: Merges terrestrial and alien math
        pool = CONJECTURE_TEMPLATES + knowledge_base + alien_theorems
        template = random.choice(pool)
        
        mode = "BASE"
        if template in knowledge_base: mode = "RECURSIVE"
        if template in alien_theorems: mode = "XENO-RECURSIVE"

        conjecture = mutate_conjecture(template)
        proved, method = attempt_proof(conjecture)

        if proved:
            proven_theorems += 1
            save_to_json(DB_FILE, knowledge_base, conjecture)
            socketio.emit('new_theorem', {'text': f"🎓 PROVED [{mode}]: {conjecture}"})
        else:
            novel_conjectures += 1
            socketio.emit('discovery', {'text': f"Scanning: {conjecture}"})
            if novel_conjectures % 12 == 0 and random.random() < 0.3:
                save_to_json(ALIEN_FILE, alien_theorems, conjecture)
                socketio.emit('alien_theorem', {'text': f"🛸 ALIEN DISCOVERY: {conjecture}"})

        socketio.emit('agent_stats', {'agents': agents_spawned, 'proven': proven_theorems, 'novel': novel_conjectures})
        socketio.sleep(0.5)

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE, kb=knowledge_base, alien_kb=alien_theorems)

@app.route("/download/<type>")
def download_file(type):
    file_map = {"terrestrial": DB_FILE, "alien": ALIEN_FILE}
    target = file_map.get(type)
    if target and os.path.exists(target):
        return send_file(target, as_attachment=True)
    return "File not found", 404

@socketio.on('toggle_system')
def handle_toggle(data):
    global running
    action = data.get('action')
    if action == 'start' and not running:
        running = True
        with open(RUNNING_FLAG, 'a'): pass
        socketio.start_background_task(evolution_loop)
    elif action == 'stop':
        running = False
        if os.path.exists(RUNNING_FLAG): os.remove(RUNNING_FLAG)
    emit('status_change', {'running': running}, broadcast=True)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Mathogenesis Recursive</title>
    <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
    <style>
        body { font-family: 'Consolas', monospace; background: #050505; color: #00ffcc; margin: 0; overflow: hidden; display: flex; flex-direction: column; height: 100vh; }
        .header { background: #111; padding: 15px 25px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #00ffcc; }
        .container { display: flex; gap: 10px; flex: 1; padding: 10px; overflow: hidden; }
        .panel { flex: 1; background: #0a0a0a; border: 1px solid #222; display: flex; flex-direction: column; }
        .panel-header { padding: 8px; background: #222; font-size: 0.8em; color: #aaa; letter-spacing: 1px; }
        .content { flex: 1; overflow-y: auto; padding: 15px; }
        .theorem { color: #00ff99; background: rgba(0,255,153,0.05); padding: 8px; margin-bottom: 5px; border-left: 2px solid #00ff99; font-size: 0.85em; }
        .discovery { color: #555; font-size: 0.75em; margin-bottom: 2px; }
        .alien { color: #ffff00; background: rgba(255,255,0,0.05); padding: 8px; margin-bottom: 5px; border-left: 2px solid #ffff00; font-size: 0.85em; }
        button { padding: 10px 20px; font-weight: bold; cursor: pointer; border: none; margin-left: 5px; }
        #startBtn { background: #00ffcc; color: #000; }
        #stopBtn { background: #ff0055; color: #fff; }
        button:disabled { opacity: 0.2; }
        .dl-link { color: #00ffcc; font-size: 0.7em; text-decoration: none; margin-right: 15px; border: 1px solid #333; padding: 3px; }
    </style>
</head>
<body>
    <div class="header">
        <h2 style="margin:0;">MATHOGENESIS v5.3 [XENO-CORE]</h2>
        <div>
            <a href="/download/terrestrial" class="dl-link">DL_TERRESTRIAL</a>
            <a href="/download/alien" class="dl-link">DL_ALIEN</a>
            <button id="startBtn" onclick="sendAction('start')">INITIALIZE</button>
            <button id="stopBtn" onclick="sendAction('stop')" disabled>HALT</button>
        </div>
    </div>
    <div class="container">
        <div class="panel"><div class="panel-header">STREAM</div><div id="stream" class="content"></div></div>
        <div class="panel"><div class="panel-header">TERRESTRIAL_KB</div><div id="kb" class="content">{% for t in kb %}<div class="theorem">🎓 {{ t }}</div>{% endfor %}</div></div>
        <div class="panel"><div class="panel-header">ALIEN_KB</div><div id="alien" class="content">{% for a in alien_kb %}<div class="alien">🛸 {{ a }}</div>{% endfor %}</div></div>
        <div class="panel" style="max-width: 150px;"><div class="panel-header">STATS</div><div class="content">Agents: <span id="agents">0</span><br>Proven: <span id="proven">0</span><br>Novel: <span id="novel">0</span></div></div>
    </div>
    <script>
        const socket = io();
        function sendAction(act) { socket.emit('toggle_system', {action: act}); }
        socket.on('status_change', (data) => {
            document.getElementById('startBtn').disabled = data.running;
            document.getElementById('stopBtn').disabled = !data.running;
        });
        socket.on('discovery', (data) => {
            const s = document.getElementById('stream');
            const div = document.createElement('div');
            div.className = 'discovery'; div.textContent = `> ${data.text}`;
            s.prepend(div);
            if(s.childNodes.length > 30) s.removeChild(s.lastChild);
        });
        socket.on('new_theorem', (data) => {
            const div = document.createElement('div');
            div.className = 'theorem'; div.textContent = data.text;
            document.getElementById('kb').prepend(div);
        });
        socket.on('alien_theorem', (data) => {
            const div = document.createElement('div');
            div.className = 'alien'; div.textContent = data.text;
            document.getElementById('alien').prepend(div);
        });
        socket.on('agent_stats', (data) => {
            document.getElementById('agents').textContent = data.agents;
            document.getElementById('proven').textContent = data.proven;
            document.getElementById('novel').textContent = data.novel;
        });
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    socketio.run(app, host="0.0.0.0", port=port)
