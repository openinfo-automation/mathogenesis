from gevent import monkey
monkey.patch_all()  # Must remain at the very top for Render/Gevent stability

import os
import json
import random
from flask import Flask, render_template_string
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mathogenesis-recursive-2025'
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

# ===== SYSTEM ESCALATION FLAGS =====
representation_mutation_enabled = False
axiom_mutation_enabled = False
novelty_filter_enabled = False

# Track milestones
milestones = {
    'representation_mutation': False,
    'axiom_mutation': False,
    'novelty_filter': False
}

# Track agent stats
agent_stats = {
    'agents_spawned': 0,
    'proven_theorems': 0,
    'novel_conjectures': 0
}

def attempt_proof(conjecture):
    if conjecture in knowledge_base:
        return False, "Redundant" 
    
    complexity_weight = any(c in conjecture for c in ["G", "hbar", "c", "R_uv", "oint", "sum"])
    
    if complexity_weight and random.random() < 0.06:
        return True, "Recursive Dimensional Analysis"
    if random.random() < 0.08:
        return True, "Formal Symbolic Verification"
    return False, None

def evolution_loop():
    global running
    while running:
        agent_stats['agents_spawned'] += 1

        # ===== AUTO-ACTIVATION BASED ON SYSTEM OBSERVATION =====
        if not milestones['novelty_filter'] and len(knowledge_base) >= 5:
            novelty_filter_enabled = True
            milestones['novelty_filter'] = True
            socketio.emit('discovery', {'text': "💡 NOVELTY FILTER ACTIVATED!"})

        if not milestones['representation_mutation'] and len(knowledge_base) >= 10:
            representation_mutation_enabled = True
            milestones['representation_mutation'] = True
            socketio.emit('discovery', {'text': "💡 REPRESENTATION MUTATION ENABLED!"})

        if not milestones['axiom_mutation'] and len(knowledge_base) >= 15:
            axiom_mutation_enabled = True
            milestones['axiom_mutation'] = True
            socketio.emit('discovery', {'text': "💡 AXIOM MUTATION ENABLED!"})

        # ===== CONJECTURE SELECTION =====
        if knowledge_base and random.random() < 0.6:
            template = random.choice(knowledge_base)
            mode = "RECURSIVE"
        else:
            template = random.choice(CONJECTURE_TEMPLATES)
            mode = "BASE"

        conjecture = template

        # ===== MUTATION PHASE =====
        mut_roll = random.random()
        if mut_roll < 0.3:
            conjecture = conjecture.replace("a", "((r_0 + 1) * a)")
        elif mut_roll < 0.5:
            conjecture = conjecture.replace("G", "(G / epsilon_0)")
        elif mut_roll < 0.6:
            conjecture = conjecture.replace("hbar", "(hbar * kappa)")

        if representation_mutation_enabled and random.random() < 0.3:
            conjecture = conjecture.replace("c", "(c * gamma)")

        if axiom_mutation_enabled and random.random() < 0.2:
            conjecture = f"mutated_axiom({conjecture})"

        if novelty_filter_enabled and conjecture in knowledge_base:
            socketio.emit('discovery', {'text': f"Filtered redundant: {conjecture}"})
            socketio.sleep(0.5)
            continue

        proved, method = attempt_proof(conjecture)
        
        if proved:
            save_db(conjecture)
            agent_stats['proven_theorems'] += 1
            socketio.emit('new_theorem', {'text': f"🎓 PROVED [{mode}]: {conjecture}"})
        else:
            agent_stats['novel_conjectures'] += 1
            socketio.emit('discovery', {'text': f"Scanning: {conjecture}"})
        
        # ===== EMIT AGENT STATS =====
        socketio.emit('status_update', {
            'agents_spawned': agent_stats['agents_spawned'],
            'proven_theorems': agent_stats['proven_theorems'],
            'novel_conjectures': agent_stats['novel_conjectures']
        })

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
    <title>Mathogenesis Recursive</title>
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
        button { padding: 10px 20px; font-weight: bold; cursor: pointer; border: none; border-radius: 2px; }
        #startBtn { background: #00ffcc; color: #000; }
        #stopBtn { background: #ff0055; color: #fff; }
        button:disabled { opacity: 0.2; }
    </style>
</head>
<body>
    <div class="header">
        <h2 style="margin:0;">MATHOGENESIS v5.1 (RECURSIVE CORE + AUTO SYSTEMS)</h2>
        <div>
            <button id="startBtn" onclick="sendAction('start')">INITIALIZE</button>
            <button id="stopBtn" onclick="sendAction('stop')" disabled>HALT</button>
        </div>
    </div>
    <div class="container">
        <div class="panel">
            <div class="panel-header">MUTATION_STREAM</div>
            <div id="stream" class="content"></div>
        </div>
        <div class="panel">
            <div class="panel-header">PERSISTENT_KNOWLEDGE_BASE</div>
            <div id="kb" class="content">
                {% for t in kb %}<div class="theorem">🎓 PROVED: {{ t }}</div>{% endfor %}
            </div>
        </div>
        <div class="panel">
            <div class="panel-header">AGENT_STATS</div>
            <div id="stats" class="content">
                <div>Agents Spawned: 0</div>
                <div>Proven Theorems: 0</div>
                <div>Novel Conjectures: 0</div>
            </div>
        </div>
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
            if(s.childNodes.length > 50) s.removeChild(s.lastChild);
        });
        socket.on('new_theorem', (data) => {
            const div = document.createElement('div');
            div.className = 'theorem'; div.textContent = data.text;
            document.getElementById('kb').prepend(div);
        });
        socket.on('status_update', (data) => {
            const stats = document.getElementById('stats');
            stats.innerHTML = `
                <div>Agents Spawned: ${data.agents_spawned}</div>
                <div>Proven Theorems: ${data.proven_theorems}</div>
                <div>Novel Conjectures: ${data.novel_conjectures}</div>
            `;
        });
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    socketio.run(app, host="0.0.0.0", port=port)
