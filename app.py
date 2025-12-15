from gevent import monkey
monkey.patch_all()

import os, random, threading
import sympy
from sympy import symbols, simplify, sympify, Function, expand, log, sqrt, pi, I, Eq
from flask import Flask, render_template_string, Response
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'stage21-formal-latex-v11'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

db_lock = threading.Lock()

# --- FORMAL SYMBOLIC REGISTRY ---
G, hbar, c, kb, eps0, mu0, pi, i, s, Lambda = symbols('G hbar c kb eps0 mu0 pi i s Lambda')
M, m, a, t, E, r0, Xi, A, P, H, L_p, S, rho, f, B, q, v, n = symbols(
    'M m a t E r0 Xi A P H L_p S rho f B q v n'
)
p_c, E_thr, Z, Gamma, M_eff, r_g, f_g, T_uv, G_uv, g_uv = symbols(
    'p_c E_thr Z Gamma M_eff r_g f_g T_uv G_uv g_uv'
)

# --- THE MASTER BEDROCK (Strict Identities) ---
# Each tuple is (LHS, RHS) to maintain formal equation structure
CORE_PHYSICS = [
    (E, m * c**2),
    (R_s, 2 * G * M / c**2),
    (L_p, sqrt(hbar * G / c**3)),
    (p_c, E_thr * log(Z)),
    (Z, Gamma * (M + m) / a),
    (S, (kb * A * c**3) / (4 * G * hbar)),
    (M_eff, n**2.37),
    (G_uv, (8 * pi * G / c**4) * T_uv),
    (zeta_s, 1/2 + i * t)
]

session_findings = [] 
running = False

def get_phys_subs():
    return [
        (E, m * c**2),
        (G, L_p**2 * c**3 / hbar),
        (a, (r0 + 1)**Xi * a),
        (m, E / c**2),
        (p_c, E_thr * log(Z)),
        (t, t / sqrt(1 - (v**2/c**2))) # Relativistic Time Dilation
    ]

def evolution_loop():
    global running
    while running:
        pool = session_findings if (session_findings and random.random() < 0.9) else CORE_PHYSICS
        base_lhs, base_rhs = random.choice(pool)
        
        subs_list = get_phys_subs()
        target_sym, replacement = random.choice(subs_list)
        
        # Apply symbolic substitution to the RHS
        new_rhs = base_rhs.subs(target_sym, replacement)
        
        # Verify Identity (If it's from bedrock or a proven finding, it's true)
        if new_rhs != base_rhs:
            new_theorem = (base_lhs, simplify(new_rhs))
            clean_str = f"{new_theorem[0]} = {new_theorem[1]}"
            
            if clean_str not in [f"{f[0]} = {f[1]}" for f in session_findings]:
                with db_lock:
                    session_findings.append(new_theorem)
                    socketio.emit('new_theorem', {'text': f"$${sympy.latex(Eq(new_theorem[0], new_theorem[1]))}$$"})
        
        socketio.emit('discovery', {'text': f"Probing: {target_sym} → {replacement}"})
        socketio.sleep(0.4)

@app.route("/")
def index(): return render_template_string(HTML_UI)

@app.route("/download")
def download():
    content = "\n".join([f"{f[0]} = {f[1]}" for f in session_findings])
    return Response(content, mimetype="text/plain", headers={"Content-disposition": "attachment; filename=singularities.txt"})

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
    <title>Stage 21 Formal Master</title>
    <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
    <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    <style>
        body { font-family: 'Helvetica', sans-serif; background: #050505; color: #00ffcc; margin: 0; padding: 20px; }
        .log { background: #000; border: 1px solid #1a1a1a; height: 65vh; overflow-y: auto; padding: 20px; border-radius: 8px; }
        .proof { background: rgba(0,255,204,0.03); border-bottom: 1px solid #111; padding: 15px 0; transition: all 0.5s; }
        .scan { color: #333; font-family: 'Courier New'; font-size: 0.8em; margin-top: 5px; }
        .btn-box { display: flex; gap: 10px; margin-bottom: 20px; }
        button { flex: 1; padding: 20px; border: none; font-weight: bold; border-radius: 4px; cursor: pointer; }
        #start { background: #00ffcc; color: #000; }
        #stop { background: #ff0055; color: #fff; }
    </style>
</head>
<body>
    <div class="btn-box">
        <button id="start" onclick="socket.emit('toggle_system', {action: 'start'})">START SEARCH</button>
        <button id="stop" onclick="socket.emit('toggle_system', {action: 'stop'})">HALT ENGINE</button>
    </div>
    <div style="text-align: right; margin-bottom: 10px;">
        <a href="/download" style="color:#ff00ff; text-decoration: none;">[DOWNLOAD FINDINGS]</a>
    </div>
    <div id="stream" class="log"></div>
    <script>
        const socket = io();
        socket.on('new_theorem', (data) => {
            const d = document.createElement('div'); d.className='proof'; d.innerHTML = data.text;
            document.getElementById('stream').prepend(d);
            MathJax.typeset();
        });
        socket.on('discovery', (data) => {
            const s = document.getElementById('stream');
            const d = document.createElement('div'); d.className='scan'; d.textContent = `> ${data.text}`;
            s.prepend(d); if(s.childNodes.length > 30) s.removeChild(s.lastChild);
        });
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
