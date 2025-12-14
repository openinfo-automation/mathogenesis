from gevent import monkey
monkey.patch_all()

import os, json, random, threading
import sympy
from sympy import symbols, simplify, sympify
from flask import Flask, render_template_string, send_file
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'final-logic-hardened-2025'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

DB_FILE = "knowledge_base.json"
ALIEN_FILE = "alien_knowledge.json"
RUNNING_FLAG = "SYSTEM_ON.flag"
db_lock = threading.Lock()

# --- PHYSICAL SYMBOLS & DIMENSIONS ---
# L=Length, M=Mass, T=Time, Q=Charge, K=Temperature
G, hbar, c, kb, epsilon0 = symbols('G hbar c kb epsilon0')
rho, a, M, m, t, E, pi, Lambda, D, p, x, h, T, k, A = symbols('rho a M m t E pi Lambda D p x h T k A')

UNIT_MAP = {
    G: "L**3 * M**-1 * T**-2",
    c: "L * T**-1",
    hbar: "M * L**2 * T**-1",
    kb: "M * L**2 * T**-2 * K**-1",
    epsilon0: "Q**2 * T**2 * M**-1 * L**-3",
    rho: "Q * L**-3",
    a: "L",
    M: "M",
    m: "M",
    t: "T",
    E: "M * L**2 * T**-2",
    D: "Q * L**-2",
    p: "M * L * T**-1",
    x: "L",
    h: "M * L**2 * T**-1",
    A: "L**2",
    k: "M * L**2 * T**-2 * K**-1"
}

# --- YOUR ORIGINAL PHYSICS TEMPLATES ---
CONJECTURE_TEMPLATES = [
    "R_uv - 1/2*R*g_uv + Lambda*g_uv = 8*pi*G/c**4*T_uv", 
    "S_BH = (k*A*c**3)/(4*G*hbar)",
    "i*hbar*d/dt|psi> = H|psi>",
    "delta_x * delta_p >= hbar/2",
    "R_s = 2*G*M/c**2",
    "Zeta(s) = sum(n**(-s), 1, inf)",
    "Res(f, c) = 1/(2*pi*i) * oint(f(z)dz)",
    "L = sqrt(hbar*G/c**3)",
    "curl(E) = -dB/dt",
    "grad * D = rho",
    "P**2 = (4*pi**2 / (G*(M+m))) * a**3",
    "chi(M) = V - E + F = 2 - 2g",
    "integral(exp(-x**2), -inf, inf) = sqrt(pi)"
]

running = os.path.exists(RUNNING_FLAG)
knowledge_base, alien_theorems = [], []
agents_spawned, proven_theorems = 0, 0

def load_db():
    global knowledge_base, alien_theorems
    for f_path, target in [(DB_FILE, knowledge_base), (ALIEN_FILE, alien_theorems)]:
        if os.path.exists(f_path):
            try:
                with open(f_path, 'r') as f:
                    data = json.load(f)
                    target.extend(data if isinstance(data, list) else [])
            except: pass

load_db()

# --- VERIFIERS: ALGEBRA + DIMENSIONS ---
def verify_dimensions(lhs, rhs):
    try:
        ratio = lhs / rhs
        dim_ratio = ratio
        for sym, dim in UNIT_MAP.items():
            dim_ratio = dim_ratio.subs(sym, sympify(dim))
        return simplify(dim_ratio).is_number
    except: return False

def attempt_hard_proof(conjecture):
    try:
        clean = conjecture.replace("^", "**").replace("Ψ(", "").replace(")", "").strip()
        if "=" not in clean: return False, None
        
        parts = clean.split("=")
        lhs, rhs = sympify(parts[0].strip()), sympify(parts[1].strip())
        
        # Check Algebra
        if simplify(lhs - rhs) == 0:
            # Check Physical Units
            if verify_dimensions(lhs, rhs):
                return True, "Physical Identity"
        return False, None
    except: return False, None

def mutate_conjecture(template):
    mutations = [
        lambda c: c.replace("a", "((r0 + 1) * a)") if "a" in c else c + " * (c/c)",
        lambda c: c.replace("G", "(G / 1)") if "G" in c else c,
        lambda c: f"Ψ({c})" if "Ψ" not in c else c
    ]
    return random.choice(mutations)(template)

def evolution_loop():
    global running, agents_spawned, proven_theorems
    while running:
        agents_spawned += 1
        pool = CONJECTURE_TEMPLATES + knowledge_base + alien_theorems
        template = random.choice(pool)
        conjecture = mutate_conjecture(template)
        
        proved, _ = attempt_hard_proof(conjecture)

        if proved:
            proven_theorems += 1
            if conjecture not in knowledge_base:
                with db_lock:
                    knowledge_base.append(conjecture)
                    with open(DB_FILE, 'w') as f: json.dump(knowledge_base, f)
                socketio.emit('new_theorem', {'text': f"🎓 PROVED: {conjecture}"})
        else:
            if random.random() < 0.15:
                if conjecture not in alien_theorems:
                    with db_lock:
                        alien_theorems.append(conjecture)
                        with open(ALIEN_FILE, 'w') as f: json.dump(alien_theorems, f)
                    socketio.emit('alien_theorem', {'text': f"🛸 ALIEN: {conjecture}"})

        socketio.emit('discovery', {'text': f"Verifying Logic: {conjecture[:45]}..."})
        socketio.emit('agent_stats', {'agents': agents_spawned, 'proven': proven_theorems, 'novel': len(alien_theorems)})
        socketio.sleep(0.5)

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE, kb=knowledge_base[-20:], alien_kb=alien_theorems[-20:])

@socketio.on('toggle_system')
def handle_toggle(data):
    global running
    if data.get('action') == 'start' and not running:
        running = True
        with open(RUNNING_FLAG, 'a'): pass
        socketio.start_background_task(evolution_loop)
    elif data.get('action') == 'stop':
        running = False
        if os.path.exists(RUNNING_FLAG): os.remove(RUNNING_FLAG)
    emit('status_change', {'running': running}, broadcast=True)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Mathogenesis v7.2 - Real Logic</title>
    <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
    <style>
        body { font-family: 'Consolas', monospace; background: #020202; color: #00ffcc; margin: 0; overflow: hidden; display: flex; flex-direction: column; height: 100vh; }
        .header { background: #000; padding: 15px 25px; display: flex; justify-content: space-between; border-bottom: 2px solid #00ffcc; }
        .container { display: flex; gap: 10px; flex: 1; padding: 10px; overflow: hidden; }
        .panel { flex: 1; background: #050505; border: 1px solid #111; display: flex; flex-direction: column; }
        .panel-header { padding: 8px; background: #111; font-size: 0.75em; color: #888; text-transform: uppercase; }
        .content { flex: 1; overflow-y: auto; padding: 10px; font-size: 0.8em; }
        .theorem { color: #00ff99; border-left: 2px solid #00ff99; padding: 5px; margin-bottom: 5px; background: rgba(0,255,153,0.05); }
        .alien { color: #ffff00; border-left: 2px solid #ffff00; padding: 5px; margin-bottom: 5px; background: rgba(255,255,0,0.05); }
        .discovery { color: #444; }
        button { padding: 10px 20px; cursor: pointer; border: none; font-weight: bold; background: #00ffcc; color: #000; }
        #stopBtn { background: #ff0055; color: white; }
        button:disabled { background: #333; color: #666; cursor: default; }
    </style>
</head>
<body>
    <div class="header">
        <h2 style="margin:0;">MATHOGENESIS v7.2 [HARD-LOGIC-RESTORED]</h2>
        <div>
            <button id="startBtn" onclick="sendAction('start')">START</button>
            <button id="stopBtn" onclick="sendAction('stop')" disabled>STOP</button>
        </div>
    </div>
    <div class="container">
        <div class="panel"><div class="panel-header">Verifying_Logic</div><div id="stream" class="content"></div></div>
        <div class="panel"><div class="panel-header">Proven_Identities</div><div id="kb" class="content">{% for t in kb %}<div class="theorem">🎓 {{ t }}</div>{% endfor %}</div></div>
        <div class="panel"><div class="panel-header">Speculative_Math</div><div id="alien" class="content">{% for a in alien_kb %}<div class="alien">🛸 {{ a }}</div>{% endfor %}</div></div>
        <div class="panel" style="max-width: 150px;"><div class="panel-header">Stats</div><div class="content">Agents: <span id="agents">0</span><br>Proved: <span id="proven">0</span><br>Alien: <span id="novel">0</span></div></div>
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
            if(s.childNodes.length > 25) s.removeChild(s.lastChild);
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
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
