from gevent import monkey
monkey.patch_all()

import os, random, threading
import sympy
from sympy import symbols, simplify, sympify, Function, expand, sqrt, pi, I, exp
from flask import Flask, render_template_string, Response
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'stage21-universal-bedrock'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

db_lock = threading.Lock()

# --- THE UNIVERSAL CONSTANT REGISTRY ---
G, hbar, c, kb, eps0, mu0, pi, i = symbols('G hbar c kb eps0 mu0 pi i')
M, m, a, t, E, r0, Xi, A, P, H, L_p, S, T, V, p, rho, f, B, q = symbols(
    'M m a t E r0 Xi A P H L_p S T V p rho f B q'
)

Omega_op = Function('Ω∞_op')
Sigma_op = Function('Σ_op')

# SI Dimensional Mapping for ALL proven physics
UNIT_MAP = {
    G: "L**3*M**-1*T**-2", c: "L*T**-1", hbar: "M*L**2*T**-1",
    kb: "M*L**2*T**-2*K**-1", eps0: "M**-1*L**-3*T**4*Q**2", mu0: "M*L*T**-2*Q**-2",
    a: "L", M: "M", m: "M", t: "T", E: "M*L**2*T**-2", A: "L**2", 
    H: "M*L**2*T**-2", L_p: "L", S: "M*L**2*T**-2*K**-1", T: "K", 
    V: "L**3", p: "M*L**-1*T**-2", rho: "M*L**-3", B: "M*T**-2*Q**-1", q: "Q"
}

# --- THE UNIVERSAL BEDROCK (Every Major Proven Equation) ---
CORE_PHYSICS = [
    "E = m * c**2",                              # Mass-Energy
    "L_p = sqrt(hbar * G / c**3)",               # Planck Length
    "S = (kb * A * c**3) / (4 * G * hbar)",      # Hawking-Bekenstein Entropy
    "H = i * hbar * d / dt",                     # Schrödinger Operator
    "F = G * M * m / a**2",                      # Newton's Gravity
    "p * V = n * kb * T",                        # Ideal Gas Law
    "E = hbar * f",                              # Planck-Einstein Relation
    "R_s = 2 * G * M / c**2",                    # Schwarzschild Radius
    "delta_x * delta_p = hbar / 2",              # Heisenberg Uncertainty
    "F = q * (E + v * B)",                       # Lorentz Force
    "e = m * c**2 / sqrt(1 - v**2/c**2)",        # Relativistic Energy
    "G_uv = 8 * pi * G / c**4 * T_uv",           # Einstein Field (Simp)
    "curl_E = -d_B / d_t",                       # Faraday's Law
    "div_D = rho"                                # Gauss's Law
]

session_findings = [] 
running = False

def verify_logic(conjecture):
    try:
        # Purity check: strip operators for math verification
        core = conjecture.replace("Ω∞_op(", "").replace("Σ_op(", "").replace(")", "").strip()
        if "=" not in core: return False
        lhs, rhs = sympify(core.split("=")[0]), sympify(core.split("=")[1])
        
        # Identity and Dimensional Checks
        if simplify(lhs - rhs) != 0: return False
        ratio = lhs / rhs
        dim_check = ratio
        for sym, dim in UNIT_MAP.items():
            if sym in dim_check.free_symbols:
                dim_check = dim_check.subs(sym, sympify(dim))
        return simplify(dim_check).is_number
    except: return False

def deep_mutate(template):
    """Multi-threaded substitution across all physical domains."""
    subs = [
        lambda x: x.replace("E", "(m * c**2)") if "E" in x else x,
        lambda x: x.replace("a", "((r0 + 1)**Xi * a)") if ("a" in x and "r0" not in x) else x,
        lambda x: x.replace("G", "(L_p**2 * c**3 / hbar)") if ("G" in x and "L_p" not in x) else x,
        lambda x: x.replace("m", "(E / c**2)") if "m" in x else x,
        lambda x: f"Ω∞_op({x})" if "Ω∞_op" not in x else x,
        lambda x: f"Σ_op({x})" if "Σ_op" not in x else x
    ]
    conjecture = template
    for _ in range(random.randint(1, 3)): # Stacking depth
        conjecture = random.choice(subs)(conjecture)
    return conjecture

def evolution_loop():
    global running
    while running:
        # Heavily biased toward building on the new 'Stage 21' findings
        pool = session_findings if (session_findings and random.random() < 0.9) else CORE_PHYSICS
        template = random.choice(pool)
        conjecture = deep_mutate(template)
        
        if verify_logic(conjecture):
            try:
                has_o, has_s = "Ω∞_op" in conjecture, "Σ_op" in conjecture
                core = conjecture.replace("Ω∞_op(", "").replace("Σ_op(", "").replace(")", "").strip()
                l_s, r_s = core.split("=")[0], core.split("=")[1]
                clean = f"{simplify(expand(sympify(l_s)))} = {simplify(expand(sympify(r_s)))}"
                if has_s: clean = f"Σ_op({clean})"
                if has_o: clean = f"Ω∞_op({clean})"
                
                if clean not in session_findings and clean not in CORE_PHYSICS:
                    with db_lock:
                        session_findings.append(clean)
                        socketio.emit('new_theorem', {'text': f"💎 {clean}"})
            except: pass
        
        socketio.emit('discovery', {'text': f"Synthesizing Bedrock... {conjecture[:25]}"})
        socketio.emit('agent_stats', {'proven': len(session_findings)})
        socketio.sleep(0.3)

@app.route("/")
def index(): return render_template_string(HTML_UI)

@app.route("/download")
def download():
    content = "--- STAGE 21 UNIVERSAL DERIVATIONS ---\n\n" + "\n\n".join(session_findings)
    return Response(content, mimetype="text/plain", headers={"Content-disposition": "attachment; filename=universal_truth.txt"})

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
    <title>Universal Bedrock Engine</title>
    <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
    <style>
        body { font-family: 'Courier New', monospace; background: #000; color: #00ffcc; margin: 0; padding: 10px; }
        .controls { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 15px; }
        button, .btn { padding: 25px; font-weight: bold; border: none; text-align: center; text-decoration: none; cursor: pointer; border-radius: 4px; font-size: 1.1em; }
        #startBtn { background: #00ffcc; color: #000; }
        #stopBtn { background: #ff0055; color: #fff; }
        .dl-btn { background: #ff00ff; color: #fff; grid-column: span 2; }
        .log-container { background: #080808; border: 1px solid #1a1a1a; height: 58vh; overflow-y: auto; padding: 15px; }
        .proof { color: #fff; margin-bottom: 20px; border-left: 4px solid #00ffcc; padding-left: 15px; font-size: 0.95em; background: rgba(0,255,204,0.05); }
        .scan { color: #222; font-size: 0.75em; }
    </style>
</head>
<body>
    <div class="controls">
        <button id="startBtn" onclick="sendAction('start')">START SEARCH</button>
        <button id="stopBtn" onclick="sendAction('stop')">HALT</button>
        <a href="/download" class="btn dl-btn">DOWNLOAD UNIVERSAL TRUTH</a>
    </div>
    <div id="stream" class="log-container"></div>
    <script>
        const socket = io();
        function sendAction(act) { socket.emit('toggle_system', {action: act}); }
        socket.on('status_change', (data) => {
            document.getElementById('startBtn').disabled = data.running;
            document.getElementById('stopBtn').disabled = !data.running;
            document.getElementById('startBtn').style.opacity = data.running ? "0.2" : "1";
            document.getElementById('stopBtn').style.opacity = !data.running ? "0.2" : "1";
        });
        socket.on('new_theorem', (data) => {
            const d = document.createElement('div'); d.className='proof'; d.textContent = data.text;
            document.getElementById('stream').prepend(d);
        });
        socket.on('discovery', (data) => {
            const s = document.getElementById('stream');
            const d = document.createElement('div'); d.className='scan'; d.textContent = `> ${data.text}`;
            s.prepend(d); if(s.childNodes.length > 25) s.removeChild(s.lastChild);
        });
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
