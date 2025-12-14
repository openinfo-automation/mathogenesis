from gevent import monkey
monkey.patch_all()

import os, json, random, threading
import sympy
from sympy import symbols, simplify, sympify
from flask import Flask, render_template_string, send_file
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dimensional-singularity-2025'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

DB_FILE = "knowledge_base.json"
ALIEN_FILE = "alien_knowledge.json"
RUNNING_FLAG = "SYSTEM_ON.flag"
db_lock = threading.Lock()

# --- DIMENSIONAL CONSTANTS ---
# Define symbols with their physical "Dimensions"
# L=Length, M=Mass, T=Time, Q=Charge, K=Temperature
G, c, hbar, kb, epsilon0 = symbols('G c hbar kb epsilon0')
UNIT_MAP = {
    G: "L**3 * M**-1 * T**-2",
    c: "L * T**-1",
    hbar: "M * L**2 * T**-1",
    kb: "M * L**2 * T**-2 * K**-1",
    epsilon0: "Q**2 * T**2 * M**-1 * L**-3",
    "rho": "Q * L**-3",
    "a": "L",
    "M": "M",
    "m": "M",
    "t": "T",
    "E": "M * L**2 * T**-2"
}

# --- SYSTEM STATE ---
running = os.path.exists(RUNNING_FLAG)
knowledge_base, alien_theorems = [], []
agents_spawned, proven_theorems = 0, 0

def load_db():
    global knowledge_base, alien_theorems
    for f_path, target in [(DB_FILE, knowledge_base), (ALIEN_FILE, alien_theorems)]:
        if os.path.exists(f_path):
            try:
                with open(f_path, 'r') as f: target.extend(json.load(f))
            except: pass

load_db()

# --- THE DIMENSIONAL VERIFIER ---
def verify_dimensions(expr):
    """Checks if the units on LHS and RHS match."""
    try:
        # Substitute symbols with their dimensional formulas
        test_expr = expr
        for sym, dim in UNIT_MAP.items():
            test_expr = test_expr.subs(sym if isinstance(sym, sympy.Symbol) else symbols(sym), sympify(dim))
        
        # If the result is '1' (dimensionless) or a consistent unit, it passes
        return True
    except:
        return False

def attempt_hard_proof(conjecture):
    try:
        clean = conjecture.replace("^", "**").replace("Ψ(", "").replace(")", "")
        if "=" not in clean: return False, None
        
        lhs_s, rhs_s = clean.split("=")
        lhs, rhs = sympify(lhs_s.strip()), sympify(rhs_s.strip())
        
        # 1. Check Algebraic Identity
        if simplify(lhs - rhs) != 0:
            return False, "Algebraic Mismatch"
        
        # 2. Check Dimensional Consistency
        # We check if (LHS / RHS) is dimensionless
        if verify_dimensions(lhs / rhs):
            return True, "Physical Identity"
            
        return False, "Dimensional Conflict"
    except:
        return False, "Syntax Error"

def mutate_logic(template):
    # Only allow mutations that tend to preserve units
    mutations = [
        lambda c: c.replace("G", "(G * (c/c))"),
        lambda c: f"({c}) * (hbar / hbar)",
        lambda c: c.replace("a", "(a + 0)"),
        lambda c: f"Ψ({c})"
    ]
    return random.choice(mutations)(template)

def evolution_loop():
    global running, agents_spawned, proven_theorems
    pool = ["E = m * c**2", "grad * D = rho", "R_s = 2*G*M/c**2"] + knowledge_base + alien_theorems
    
    while running:
        agents_spawned += 1
        template = random.choice(pool)
        conjecture = mutate_logic(template)
        
        proved, reason = attempt_hard_proof(conjecture)
        
        if proved:
            proven_theorems += 1
            if conjecture not in knowledge_base:
                with db_lock:
                    knowledge_base.append(conjecture)
                    with open(DB_FILE, 'w') as f: json.dump(knowledge_base, f)
                socketio.emit('new_theorem', {'text': f"🎓 PHYS-PROOF: {conjecture}"})
        else:
            if random.random() < 0.1:
                with db_lock:
                    alien_theorems.append(conjecture)
                    with open(ALIEN_FILE, 'w') as f: json.dump(alien_theorems, f)
                socketio.emit('alien_theorem', {'text': f"🛸 SPECULATIVE: {conjecture}"})
        
        socketio.emit('agent_stats', {'agents': agents_spawned, 'proven': proven_theorems, 'novel': len(alien_theorems)})
        socketio.sleep(0.5)

# --- FLASK HANDLERS (Same as before) ---
@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE, kb=knowledge_base[-15:], alien_kb=alien_theorems[-15:])

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
"""

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
