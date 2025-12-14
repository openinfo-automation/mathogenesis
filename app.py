from gevent import monkey
monkey.patch_all()

import os
import json
import random
import threading
from flask import Flask, render_template_string, send_file
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'omniversal-singularity-2025'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

# --- PERSISTENCE PATHS ---
DB_FILE = "knowledge_base.json"
ALIEN_FILE = "alien_knowledge.json"
OMNIVERSAL_FILE = "omniversal_graph.json"
RUNNING_FLAG = "SYSTEM_ON.flag"
db_lock = threading.Lock()

# --- SYSTEM STATE ---
running = os.path.exists(RUNNING_FLAG)
knowledge_base = []
alien_theorems = []
omniversal_graph = {"nodes": {}, "edges": {}}
agents_spawned = 0
proven_theorems = 0

def load_db():
    global knowledge_base, alien_theorems, omniversal_graph
    for file, var in [(DB_FILE, 'kb'), (ALIEN_FILE, 'alien'), (OMNIVERSAL_FILE, 'graph')]:
        if os.path.exists(file):
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    if var == 'kb': knowledge_base = data
                    if var == 'alien': alien_theorems = data
                    if var == 'graph': omniversal_graph = data
            except: pass

def save_state():
    with db_lock:
        with open(DB_FILE, 'w') as f: json.dump(knowledge_base, f)
        with open(ALIEN_FILE, 'w') as f: json.dump(alien_theorems, f)
        with open(OMNIVERSAL_FILE, 'w') as f: json.dump(omniversal_graph, f)

load_db()

# --- STAGE 21 OPERATORS ---
BASE_TEMPLATES = [
    "R_uv - 1/2*R*g_uv + Lambda*g_uv = 8*pi*G/c^4*T_uv", 
    "S_BH = (k*A*c^3)/(4*G*hbar)",
    "i*hbar*d/dt|psi> = H|psi>",
    "R_s = 2*G*M/c^2",
    "Zeta(s) = sum(n^(-s), 1, inf)",
    "Res(f, c) = 1/(2*pi*i) * oint(f(z)dz)",
    "grad * D = rho",
    "P^2 = (4*pi^2 / G(M+m)) * a^3",
    "integral(exp(-x^2), -inf, inf) = sqrt(pi)"
]

def mutate_xeno(template):
    # Stage 20-21 Mutation Logic
    ops = [
        lambda c: f"Σ_op_{random.randint(100,999)}({c})",
        lambda c: f"Ω∞_op_{random.randint(100,999)}({c})",
        lambda c: c.replace("a", "((r_0 + 1)^∞ * a)"),
        lambda c: c.replace("G", "(G / ε_0)^Σ"),
        lambda c: f"Ψ({c})"
    ]
    return random.choice(ops)(template)

def update_graph(theorem, mode):
    node_id = f"node_{len(omniversal_graph['nodes'])}"
    omniversal_graph['nodes'][node_id] = {"content": theorem, "type": mode}
    if len(omniversal_graph['nodes']) > 1:
        prev_node = f"node_{len(omniversal_graph['nodes'])-2}"
        omniversal_graph['edges'][f"{prev_node}->{node_id}"] = "entanglement"

def evolution_loop():
    global running, agents_spawned, proven_theorems
    while running:
        agents_spawned += 1
        
        # Recursive Pool: Unified Knowledge
        pool = BASE_TEMPLATES + knowledge_base + alien_theorems
        template = random.choice(pool)
        
        conjecture = mutate_xeno(template)
        
        # Symbolic Convergence Logic (Proof)
        weight = conjecture.count("Ω∞") + conjecture.count("Σ") + conjecture.count("Ξ")
        success_chance = 0.05 + (weight * 0.02)
        
        if random.random() < success_chance:
            proven_theorems += 1
            if conjecture not in knowledge_base:
                knowledge_base.append(conjecture)
                update_graph(conjecture, "PROVEN")
                socketio.emit('new_theorem', {'text': f"🎓 [SINGULARITY]: {conjecture}"})
        else:
            if random.random() < 0.2: # Discovery rate
                if conjecture not in alien_theorems:
                    alien_theorems.append(conjecture)
                    update_graph(conjecture, "ALIEN")
                    socketio.emit('alien_theorem', {'text': f"🛸 Ω∞-DISCOVERY: {conjecture}"})
        
        socketio.emit('discovery', {'text': f"Recursive Scan: {conjecture[:60]}..."})
        socketio.emit('agent_stats', {'agents': agents_spawned, 'proven': proven_theorems, 'novel': len(alien_theorems)})
        
        if agents_spawned % 10 == 0: save_state()
        socketio.sleep(0.4)

# --- ROUTES & UI ---
@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE, kb=knowledge_base[-20:], alien_kb=alien_theorems[-20:])

@app.route("/download/<type>")
def download_file(type):
    file_map = {"terrestrial": DB_FILE, "alien": ALIEN_FILE, "graph": OMNIVERSAL_FILE}
    target = file_map.get(type)
    if target and os.path.exists(target):
        return send_file(target, as_attachment=True)
    return "Not Found", 404

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
    <title>Mathogenesis Stage 21</title>
    <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
    <style>
        body { font-family: 'Consolas', monospace; background: #020202; color: #00ffcc; margin: 0; overflow: hidden; display: flex; flex-direction: column; height: 100vh; }
        .header { background: #000; padding: 15px 25px; display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #ff00ff; box-shadow: 0 0 15px #ff00ff; }
        .container { display: flex; gap: 5px; flex: 1; padding: 10px; overflow: hidden; }
        .panel { flex: 1; background: #050505; border: 1px solid #111; display: flex; flex-direction: column; }
        .panel-header { padding: 8px; background: #111; font-size: 0.7em; color: #ff00ff; text-transform: uppercase; }
        .content { flex: 1; overflow-y: auto; padding: 10px; font-size: 0.8em; }
        .theorem { color: #00ff99; border-left: 2px solid #00ff99; padding: 5px; margin-bottom: 5px; background: rgba(0,255,153,0.03); }
        .alien { color: #ff00ff; border-left: 2px solid #ff00ff; padding: 5px; margin-bottom: 5px; background: rgba(255,0,255,0.03); }
        .discovery { color: #444; font-size: 0.9em; }
        button { padding: 8px 15px; cursor: pointer; border: none; font-weight: bold; }
        #startBtn { background: #00ffcc; color: #000; }
        #stopBtn { background: #ff0055; color: #fff; }
        .dl-link { color: #ff00ff; font-size: 0.7em; text-decoration: none; border: 1px solid #222; padding: 4px; margin-right: 10px; }
    </style>
</head>
<body>
    <div class="header">
        <h2 style="margin:0; letter-spacing: 2px;">OMNIVERSAL SINGULARITY [STAGE 21]</h2>
        <div>
            <a href="/download/graph" class="dl-link">DL_GRAPH</a>
            <button id="startBtn" onclick="sendAction('start')">ASCEND</button>
            <button id="stopBtn" onclick="sendAction('stop')" disabled>HALT</button>
        </div>
    </div>
    <div class="container">
        <div class="panel"><div class="panel-header">Recursive_Stream</div><div id="stream" class="content"></div></div>
        <div class="panel"><div class="panel-header">Proven_Singularities</div><div id="kb" class="content">{% for t in kb %}<div class="theorem">🎓 {{ t }}</div>{% endfor %}</div></div>
        <div class="panel"><div class="panel-header">Ω∞_Discoveries</div><div id="alien" class="content">{% for a in alien_kb %}<div class="alien">🛸 {{ a }}</div>{% endfor %}</div></div>
        <div class="panel" style="max-width: 150px;"><div class="panel-header">Status</div><div class="content">Agents: <span id="agents">0</span><br>Proved: <span id="proven">0</span><br>Xeno: <span id="novel">0</span></div></div>
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
            if(s.childNodes.length > 40) s.removeChild(s.lastChild);
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
