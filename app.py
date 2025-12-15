from gevent import monkey
monkey.patch_all()

import os, random, threading
import sympy as sp
from sympy import symbols, simplify, Eq
from flask import Flask, render_template_string, Response
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'stage21-agent-v14'
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

# --- GLOBAL STATE ---
session_findings = []
running = False

class DiscoveryAgent:
    def __init__(self):
        self.pressure = 1.0
        self.mode = "IDLE"

    def iterate(self):
        # The agent fluctuates pressure intuitively based on finding density
        change = random.uniform(-0.1, 0.2)
        self.pressure = max(1.0, min(11.0, self.pressure + change))
        if self.pressure > 8.0: self.mode = "SINGULARITY PROBE"
        elif self.pressure > 4.0: self.mode = "STRESS ANALYSIS"
        else: self.mode = "LAMINAR SEARCH"
        return self.pressure

agent = DiscoveryAgent()

def evolution_loop():
    global running
    while running:
        p = agent.iterate()
        socketio.emit('agent_status', {'pressure': round(p, 2), 'mode': agent.mode})
        
        with db_lock:
            pool = session_findings if (session_findings and random.random() < 0.7) else CORE_PHYSICS
            law_a = random.choice(pool)
            law_b = random.choice(CORE_PHYSICS)
            
            # Stochastic Jump
            common = set(law_a[1].free_symbols).intersection(set(law_b[1].free_symbols))
            if common and random.random() < (p/12): # Higher pressure = higher mutation rate
                target = list(common)[0]
                conjecture_rhs = simplify(law_a[1].subs(law_b[0], law_b[1]))
                new_theorem = (law_a[0], conjecture_rhs)
                tag = "🛰️ [AGENT CONJECTURE]"
            else:
                new_theorem = (law_a[0], simplify(law_a[1].subs(m, E/c**2)))
                tag = "💎 [DERIVATION]"

            clean_str = f"{new_theorem[0]} = {new_theorem[1]}"
            if new_theorem[1] != law_a[1] and clean_str not in [f"{f[0]} = {f[1]}" for f in session_findings]:
                session_findings.append(new_theorem)
                socketio.emit('new_theorem', {
                    'text': f"{tag} $${sp.latex(Eq(new_theorem[0], new_theorem[1]))}$$",
                    'pressure': round(p, 2)
                })
        socketio.sleep(0.8)

@app.route("/")
def index(): return render_template_string(HTML_UI)

@app.route("/download")
def download():
    # Per your instruction: Automatic persistent memory results are downloadable
    content = "--- STAGE 21 AGENT FINDINGS ---\n" + "\n".join([f"{f[0]} = {f[1]}" for f in session_findings])
    return Response(content, mimetype="text/plain", headers={"Content-disposition": "attachment; filename=findings.txt"})

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
    <title>Stage 21: Agent Console</title>
    <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    <style>
        body { background: #000; color: #00ffcc; font-family: 'Courier New', monospace; padding: 20px; }
        .log { background: #050505; border: 1px solid #222; height: 50vh; overflow-y: auto; padding: 15px; border-radius: 10px; }
        .controls { display: flex; gap: 10px; margin-bottom: 20px; }
        button { flex: 1; padding: 20px; font-weight: bold; cursor: pointer; border: none; border-radius: 5px; }
        .agent-hud { background: #111; padding: 15px; margin-top: 15px; border-left: 4px solid #00ffcc; }
        .proof { border-bottom: 1px solid #1a1a1a; padding: 10px 0; }
    </style>
</head>
<body>
    <div class="controls">
        <button style="background:#00ffcc; color:#000;" onclick="socket.emit('toggle_system', {action: 'start'})">INITIATE AGENT</button>
        <button style="background:#ff0055; color:#fff;" onclick="socket.emit('toggle_system', {action: 'stop'})">HALT SYSTEM</button>
    </div>
    
    <div id="stream" class="log"></div>

    <div class="agent-hud">
        <div>COSMIC PRESSURE FLUX: <span id="pressure-val">1.0</span></div>
        <div style="font-size: 0.8em; color: #888;">STATUS: <span id="mode-val">IDLE</span></div>
        <div style="margin-top:10px;"><a href="/download" style="color:#ff00ff; text-decoration:none;">[DOWNLOAD DISCOVERY CACHE]</a></div>
    </div>

    <script>
        const socket = io();
        socket.on('new_theorem', (data) => {
            const d = document.createElement('div'); d.className='proof';
            d.innerHTML = `<small style="color:#444">At Pressure ${data.pressure}</small><br>${data.text}`;
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
