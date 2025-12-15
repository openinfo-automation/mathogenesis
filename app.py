from gevent import monkey
monkey.patch_all()

import os, json, random, threading
import sympy
from sympy import symbols, simplify, sympify, Function, expand, count_ops
from flask import Flask, render_template_string, Response
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'stage21-recursive-stable-v10.3'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

db_lock = threading.Lock()

# --- THE OMNIVERSAL REGISTRY ---
G, hbar, c, kb, epsilon0, pi, d, dt, i = symbols('G hbar c kb epsilon0 pi d dt i')
rho, a, M, m, t, E, Lambda, D, r0, Xi, A, P, H, delta_x, delta_p = symbols(
    'rho a M m t E Lambda D r0 Xi A P H delta_x delta_p'
)

Omega_op = Function('Ω∞_op')
Sigma_op = Function('Σ_op')

UNIT_MAP = {
    G: "L**3*M**-1*T**-2", c: "L*T**-1", hbar: "M*L**2*T**-1",
    kb: "M*L**2*T**-2*K**-1", rho: "Q*L**-3", a: "L", M: "M",
    m: "M", t: "T", E: "M*L**2*T**-2", D: "Q*L**-2", A: "L**2", H: "M*L**2*T**-2"
}

# SEED THEOREMS
CORE_PHYSICS = [
    "L = sqrt(hbar * G / c**3)",
    "P**2 = (4 * pi**2 / (G * (M + m))) * a**3",
    "S_BH = (kb * A * c**3) / (4 * G * hbar)",
    "E = m * c**2",
    "delta_x * delta_p = hbar / 2",
    "H = i * hbar * d / dt"
]

session_findings = [] 
running = False

def verify_logic(conjecture):
    """Algebraic verification with an added Complexity Guard."""
    try:
        # Prevent runaway complexity (The 'System Break' Guard)
        if len(conjecture) > 250: return False
        
        work_str = conjecture.replace("^", "**").replace("Ω∞_op(", "").replace("Σ_op(", "").replace(")", "").strip()
        if "=" not in work_str: return False
        lhs_s, rhs_s = work_str.split("=")
        lhs, rhs = sympify(lhs_s.strip()), sympify(rhs_s.strip())
        
        # 1. Truth Test
        if simplify(lhs - rhs) != 0: return False
        
        # 2. Physics Test
        ratio = lhs / rhs
        dim_check = ratio
        for sym, dim in UNIT_MAP.items():
            if sym in dim_check.free_symbols:
                dim_check = dim_check.subs(sym, sympify(dim))
        return simplify(dim_check).is_number
    except: return False

def mutate(template):
    """The Hill-Climbing Discovery Logic."""
    muts = [
        lambda c: f"Ω∞_op({c})" if "Ω∞_op" not in c else c,
        lambda c: f"Σ_op({c})" if "Σ_op" not in c else c,
        lambda c: c.replace("a", "((r0 + 1)**Xi * a)") if ("a" in c and "r0" not in c) else c,
        lambda c: c.replace("G", "(G / (epsilon0**Xi))") if ("G" in c and "epsilon0" not in c) else c,
        lambda c: c.replace("E", "(m * c**2)") if "E" in c else c,
        lambda c: f"({c}) + (E - m * c**2)" if "E" in c and "m" in c else c # Complex substitution
    ]
    return random.choice(muts)(template)

def evolution_loop():
    global running
    while running:
        # RECURSIVE SELECTION: 80% weight on building upon new findings
        if session_findings and random.random() < 0.8:
            template = random.choice(session_findings)
        else:
            template = random.choice(CORE_PHYSICS)
            
        conjecture = mutate(template)
        
        if verify_logic(conjecture):
            try:
                has_o, has_s = "Ω∞_op" in conjecture, "Σ_op" in conjecture
                core = conjecture.replace("Ω∞_op(", "").replace("Σ_op(", "").replace(")", "").strip()
                l_s, r_s = core.split("=")
                # Clean mathematical condensation
                clean = f"{simplify(expand(sympify(l_s)))} = {simplify(expand(sympify(r_s)))}"
                
                if has_s: clean = f"Σ_op({clean})"
                if has_o: clean = f"Ω∞_op({clean})"
                
                # CHECK FOR NOVELTY: Only save if it's a genuine step forward
                if clean not in session_findings and clean not in CORE_PHYSICS:
                    with db_lock:
                        session_findings.append(clean)
                        socketio.emit('new_theorem', {'text': f"🧬 {clean}"})
            except: pass
        
        socketio.emit('discovery', {'text': f"Advancing Logic... {conjecture[:28]}"})
        socketio.emit('agent_stats', {'proven': len(session_findings)})
        socketio.sleep(0.4)

@app.route("/")
def index(): return render_template_string(HTML_UI)

@app.route("/download")
def download():
    content = "--- STAGE 21 NEW THEOREMS ---\n\n" + "\n\n".join(session_findings)
    return Response(content, mimetype="text/plain", headers={"Content-disposition": "attachment; filename=discoveries.txt"})

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

HTML_UI = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Stage 21 Evolution</title>
    <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
    <style>
        body { font-family: 'Courier New', monospace; background: #000; color: #00ffcc; margin: 0; padding: 10px; }
        .controls { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 10px; }
        button, .btn { padding: 22px; font-weight: bold; border: none; text-align: center; text-decoration: none; cursor: pointer; border-radius: 4px; font-size: 1.1em; }
        #startBtn { background: #00ffcc; color: #000; }
        #stopBtn { background: #ff0055; color: #fff; }
        .dl-btn { background: #ff00ff; color: #fff; grid-column: span 2; }
        .log-container { background: #050505; border: 1px solid #1a1a1a; height: 62vh; overflow-y: auto; padding: 12px; }
        .proof { color: #00ff99; margin-bottom: 15px; border-left: 3px solid #00ff99; padding-left: 10px; font-size: 0.9em; background: rgba(0,255,153,0.05); padding-top: 8px; padding-bottom: 8px; }
        .scan { color: #333; font-size: 0.7em; }
        .status { font-size: 0.8em; margin-top: 10px; display: flex; justify-content: space-between; }
    </style>
</head>
<body>
    <div class="controls">
        <button id="startBtn" onclick="sendAction('start')">START ENGINE</button>
        <button id="stopBtn" onclick="sendAction('stop')">HALT ENGINE</button>
        <a href="/download" class="btn dl-btn">DOWNLOAD DISCOVERIES</a>
    </div>
    <div class="status">
        <span>THEOREMS PROVEN: <b id="proven">0</b></span>
    </div>
    <div id="stream" class="log-container"></div>
    <script>
        const socket = io();
        function sendAction(act) { socket.emit('toggle_system', {action: act}); }
        socket.on('status_change', (data) => {
            document.getElementById('startBtn').disabled = data.running;
            document.getElementById('stopBtn').disabled = !data.running;
            document.getElementById('startBtn').style.opacity = data.running ? "0.3" : "1";
            document.getElementById('stopBtn').style.opacity = !data.running ? "0.3" : "1";
        });
        socket.on('new_theorem', (data) => {
            const d = document.createElement('div'); d.className='proof'; d.textContent = data.text;
            document.getElementById('stream').prepend(d);
        });
        socket.on('discovery', (data) => {
            const s = document.getElementById('stream');
            const d = document.createElement('div'); d.className='scan'; d.textContent = `> ${data.text}`;
            s.prepend(d); if(s.childNodes.length > 30) s.removeChild(s.lastChild);
        });
        socket.on('agent_stats', (data) => { document.getElementById('proven').textContent = data.proven; });
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
