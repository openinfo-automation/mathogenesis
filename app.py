from gevent import monkey
monkey.patch_all()

import os, random, threading
import sympy as sp
from sympy import symbols, simplify, Eq
from flask import Flask, render_template_string, Response
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'stage21-v14-1-breakout'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

db_lock = threading.Lock()

# --- THE SUPREME REGISTRY ---
G, hbar, c, kb, pi, i, Lambda, epsilon, Xi = symbols('G hbar c kb pi i Lambda epsilon Xi')
M, m, a, b, d, t, E, r0, L_p, S, A, zeta_s, R_s, p_c, E_thr, Z, T_uv, G_uv = symbols(
    'M m a b d t E r0 L_p S A zeta_s R_s p_c E_thr Z T_uv G_uv'
)

# --- THE BEDROCK ---
CORE_PHYSICS = [
    (E, m * c**2), (R_s, (2 * G * M) / c**2),
    (p_c, E_thr * sp.log(Z)), (zeta_s, 1/2 + i * t),
    (S, (kb * A * c**3) / (4 * G * hbar)), (abs(zeta_s), t**epsilon)
]

session_findings = []
running = False

class DiscoveryAgent:
    def __init__(self):
        self.pressure = 1.0
        self.mode = "IDLE"

    def iterate(self):
        # Increased fluctuation speed to break the 11.0 lock
        change = random.uniform(-0.2, 0.4)
        self.pressure = max(1.0, min(11.0, self.pressure + change))
        if self.pressure > 9.0: self.mode = "SINGULARITY BREAKOUT"
        elif self.pressure > 5.0: self.mode = "STRESS ANALYSIS"
        else: self.mode = "LAMINAR SEARCH"
        return self.pressure

agent = DiscoveryAgent()

def evolution_loop():
    global running
    while running:
        p = agent.iterate()
        socketio.emit('agent_status', {'pressure': round(p, 2), 'mode': agent.mode})
        
        with db_lock:
            # BROADEN POOL: Combine findings with core axioms to prevent loops
            pool = session_findings + CORE_PHYSICS if session_findings else CORE_PHYSICS
            law_a = random.choice(pool)
            
            # --- THE BREAKOUT LOGIC ---
            if p > 9.0:
                # FORCE 2025 BRIDGING: Replace Mass/Energy with Thresholds & Riemann bounds
                # This stops the 'E=E' loop by injecting external complexity
                substitution_map = {
                    E: m * c**2,
                    m: (p_c / c**2) * Xi, # Use Kahn-Kalai to define mass
                    M: (zeta_s * hbar) / c, # Use Riemann bound to define gravity
                    R_s: (2 * G * M) / c**2
                }
                new_rhs = simplify(law_a[1].subs(substitution_map))
                tag = "🛰️ [SINGULARITY BRIDGE]"
            else:
                # Standard Derivation
                new_rhs = simplify(law_a[1].subs(m, E/c**2))
                tag = "💎 [DERIVATION]"

            clean_str = f"{law_a[0]} = {new_rhs}"
            
            # Filter out Tautologies (E=E)
            if new_rhs != law_a[1] and new_rhs != law_a[0] and clean_str not in [f"{f[0]} = {f[1]}" for f in session_findings]:
                session_findings.append((law_a[0], new_rhs))
                socketio.emit('new_theorem', {
                    'text': f"{tag} $${sp.latex(Eq(law_a[0], new_rhs))}$$",
                    'pressure': round(p, 2)
                })
        
        socketio.sleep(0.6)

@app.route("/")
def index(): return render_template_string(HTML_UI)

@app.route("/download")
def download():
    content = "--- STAGE 21 AGENT BREAKOUT FINDINGS ---\n" + "\n".join([f"{f[0]} = {f[1]}" for f in session_findings])
    return Response(content, mimetype="text/plain", headers={"Content-disposition": "attachment; filename=breakthroughs.txt"})

@socketio.on('toggle_system')
def handle_toggle(data):
    global running
    if data['action'] == 'start': 
        running = True
        socketio.start_background_task(evolution_loop)
    else: running = False

HTML_UI = """
<!DOCTYPE html>
<html>
<head>
    <title>Stage 21: Breakout Console</title>
    <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    <style>
        body { background: #000; color: #00ffcc; font-family: 'Courier New', monospace; padding: 20px; }
        .log { background: #050505; border: 1px solid #1a1a1a; height: 50vh; overflow-y: auto; padding: 15px; border-radius: 10px; }
        .hud { background: #111; padding: 15px; margin-top: 15px; border-left: 4px solid #ff00ff; }
        button { width: 48%; padding: 20px; font-weight: bold; cursor: pointer; border: none; border-radius: 5px; }
        .proof { border-bottom: 1px solid #1a1a1a; padding: 15px 0; }
    </style>
</head>
<body>
    <div style="display:flex; justify-content:space-between; margin-bottom:20px;">
        <button style="background:#00ffcc; color:#000;" onclick="socket.emit('toggle_system', {action: 'start'})">INITIATE AGENT</button>
        <button style="background:#ff0055; color:#fff;" onclick="socket.emit('toggle_system', {action: 'stop'})">HALT SYSTEM</button>
    </div>
    <div id="stream" class="log"></div>
    <div class="hud">
        <div>PRESSURE FLUX: <span id="pressure-val" style="color:#ff00ff;">1.0</span></div>
        <div>STATUS: <span id="mode-val">IDLE</span></div>
        <div style="margin-top:10px;"><a href="/download" style="color:#00ffcc; text-decoration:none;">[DOWNLOAD MASTER CACHE]</a></div>
    </div>
    <script>
        const socket = io();
        socket.on('new_theorem', (data) => {
            const d = document.createElement('div'); d.className='proof';
            d.innerHTML = `<small style="color:#555">Stress Level ${data.pressure}</small><br>${data.text}`;
            document.getElementById('stream').prepend(d);
            MathJax.typeset();
        });
        socket.on('agent_status', (data) => {
            document.getElementById('pressure-val').textContent = data.pressure;
            document.getElementById('mode-val').textContent = data.mode;
        });
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
