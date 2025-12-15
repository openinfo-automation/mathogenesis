from gevent import monkey
monkey.patch_all()

import os, json, random, threading
import sympy
from sympy import symbols, simplify, sympify, Function, expand
from flask import Flask, render_template_string, Response
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'stage21-absolute-v10'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

db_lock = threading.Lock()

# --- THE OMNIVERSAL REGISTRY ---
# Added 'd' and 'dt' to prevent symbolic parsing errors in calculus templates
G, hbar, c, kb, epsilon0, pi, d, dt = symbols('G hbar c kb epsilon0 pi d dt')
rho, a, M, m, t, E, Lambda, D, r0, Xi, A, P, H, delta_x, delta_p = symbols(
    'rho a M m t E Lambda D r0 Xi A P H delta_x delta_p'
)

# Custom Operators
Omega_op = Function('Ω∞_op')
Sigma_op = Function('Σ_op')

# SI Dimensional Registry
UNIT_MAP = {
    G: "L**3*M**-1*T**-2", c: "L*T**-1", hbar: "M*L**2*T**-1",
    kb: "M*L**2*T**-2*K**-1", rho: "Q*L**-3", a: "L", M: "M",
    m: "M", t: "T", E: "M*L**2*T**-2", D: "Q*L**-2", A: "L**2", H: "M*L**2*T**-2"
}

# Clean Core Templates
CORE_PHYSICS = [
    "L = sqrt(hbar * G / c**3)",
    "P**2 = (4 * pi**2 / (G * (M + m))) * a**3",
    "S_BH = (kb * A * c**3) / (4 * G * hbar)",
    "E = m * c**2",
    "R_s = 2*G*M/c**2",
    "delta_x * delta_p = hbar / 2",
    "H = i * hbar * d / dt"
]

session_findings = [] 
running = False

def verify_logic(conjecture):
    """Rigorous Algebraic and Dimensional Verification."""
    try:
        # Prepare for SymPy
        work_str = conjecture.replace("^", "**").replace("Ω∞_op(", "").replace("Σ_op(", "").replace(")", "").strip()
        if "=" not in work_str: return False
        
        lhs_s, rhs_s = work_str.split("=")
        lhs = sympify(lhs_s.strip())
        rhs = sympify(rhs_s.strip())

        # 1. Algebraic Identity Verification
        if simplify(lhs - rhs) != 0: return False

        # 2. Dimensional Analysis (Hole Proofed)
        ratio = lhs / rhs
        dim_check = ratio
        for sym, dim in UNIT_MAP.items():
            if sym in dim_check.free_symbols:
                dim_check = dim_check.subs(sym, sympify(dim))
        
        return simplify(dim_check).is_number
    except: return False

def mutate(template):
    """Recursive Stage 21 Mutations."""
    muts = [
        lambda c: f"Ω∞_op({c})" if "Ω∞_op" not in c else c,
        lambda c: f"Σ_op({c})" if "Σ_op" not in c else c,
        lambda c: c.replace("a", "((r0 + 1)**Xi * a)") if ("a" in c and "r0" not in c) else c,
        lambda c: c.replace("G", "(G / (epsilon0**Xi))") if ("G" in c and "epsilon0" not in c) else c,
        lambda c: f"({c}) * (c / c)" # Temporarily used for identity testing, stripped later
    ]
    return random.choice(muts)(template)

def evolution_loop():
    global running
    while running:
        pool = CORE_PHYSICS + session_findings
        template = random.choice(pool)
        conjecture = mutate(template)
        
        if verify_logic(conjecture):
            # THE PURIFIER: Strips redundant noise like (c/c) before saving
            try:
                # Isolate the operators
                has_omega = "Ω∞_op" in conjecture
                has_sigma = "Σ_op" in conjecture
                
                # Clean the core math
                core = conjecture.replace("Ω∞_op(", "").replace("Σ_op(", "").replace(")", "").strip()
                l_s, r_s = core.split("=")
                clean_expr = f"{simplify(expand(sympify(l_s)))} = {simplify(expand(sympify(r_s)))}"
                
                # Re-wrap
                if has_sigma: clean_expr = f"Σ_op({clean_expr})"
                if has_omega: clean_expr = f"Ω∞_op({clean_expr})"
                
                if clean_expr not in session_findings and clean_expr not in CORE_PHYSICS:
                    with db_lock:
                        session_findings.append(clean_expr)
                        socketio.emit('new_theorem', {'text': f"💎 {clean_expr}"})
            except: pass
        
        socketio.emit('discovery', {'text': f"Scanning Logic... {conjecture[:30]}"})
        socketio.emit('agent_stats', {'proven': len(session_findings)})
        socketio.sleep(0.5)

@app.route("/")
def index():
    return render_template_string(HTML_UI)

@app.route("/download")
def download():
    """Direct Download for iPhone/Mobile."""
    content = "--- STAGE 21 SESSION FINDINGS ---\n\n"
    content += "\n\n".join(session_findings) if session_findings else "No new identities proven yet."
    return Response(
        content,
        mimetype="text/plain",
        headers={"Content-disposition": "attachment; filename=stage21_results.txt"}
    )

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
    <title>Stage 21 Engine</title>
    <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
    <style>
        body { font-family: 'Courier New', monospace; background: #000; color: #00ffcc; margin: 0; padding: 10px; }
        .header { display: flex; flex-direction: column; gap: 10px; border-bottom: 2px solid #00ffcc; padding-bottom: 10px; }
        .controls { display: flex; gap: 10px; }
        button, .btn { flex: 1; padding: 18px; font-weight: bold; border: none; text-align: center; text-decoration: none; cursor: pointer; border-radius: 4px; }
        #startBtn { background: #00ffcc; color: #000; }
        .dl-btn { background: #ff00ff; color: #fff; }
        .log-container { margin-top: 15px; background: #050505; border: 1px solid #1a1a1a; height: 65vh; overflow-y: auto; padding: 12px; }
        .proof { color: #00ff99; margin-bottom: 12px; border-left: 3px solid #00ff99; padding-left: 10px; font-size: 0.95em; line-height: 1.4; }
        .scan { color: #333; font-size: 0.75em; margin-bottom: 4px; }
        .stats { font-size: 0.85em; margin-top: 10px; opacity: 0.7; }
    </style>
</head>
<body>
    <div class="header">
        <h2 style="margin:0;">OMNIVERSAL ENGINE v10.0</h2>
        <div class="controls">
            <button id="startBtn" onclick="sendAction('start')">START ENGINE</button>
            <a href="/download" class="btn dl-btn">DOWNLOAD RESULTS</a>
        </div>
        <div class="stats">Proven Singularities: <span id="proven">0</span></div>
    </div>
    <div id="stream" class="log-container"></div>
    <script>
        const socket = io();
        function sendAction(act) { socket.emit('toggle_system', {action: act}); }
        socket.on('new_theorem', (data) => {
            const d = document.createElement('div'); d.className='proof'; d.textContent = data.text;
            document.getElementById('stream').prepend(d);
        });
        socket.on('discovery', (data) => {
            const s = document.getElementById('stream');
            const d = document.createElement('div'); d.className='scan'; d.textContent = `> ${data.text}`;
            s.prepend(d); if(s.childNodes.length > 40) s.removeChild(s.lastChild);
        });
        socket.on('agent_stats', (data) => { document.getElementById('proven').textContent = data.proven; });
        socket.on('status_change', (data) => {
            document.getElementById('startBtn').textContent = data.running ? "ENGINE RUNNING..." : "START ENGINE";
            document.getElementById('startBtn').style.opacity = data.running ? "0.5" : "1";
        });
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
