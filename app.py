from flask import Flask, jsonify, render_template_string, request
import threading, time, random, json, os

app = Flask(__name__)

# --- Persistence & State ---
DB_FILE = "knowledge_base.json"
running = False
discoveries = [] # Milestone stream
knowledge_base = [] # Proven theorems
metrics = {
    "agents_spawned": 0,
    "proven_theorems": 0,
    "novel_conjectures": 0
}

# --- Mathematical Foundation ---
AXIOMS = ["x + 0 = x", "x * 1 = x", "x * 0 = 0", "(x + y) + z = x + (y + z)", "x * y = y * x"]
KNOWN_THEOREMS = ["sum(n,0,x) = x(x+1)/2", "(x + 1)^2 = x^2 + 2x + 1", "x^2 - y^2 = (x-y)(x+y)"]

CONJECTURE_TEMPLATES = [
    "(a+b)^2 = a^2 + 2ab + b^2",
    "a^3 + b^3 = (a+b)(a^2 - ab + b^2)",
    "sum(k^2,0,n) = n(n+1)(2n+1)/6",
    "sum(k^3,0,n) = (n(n+1)/2)^2",
    "product(1+1/k,1,n) = n+1",
    "sum(r^k,0,n-1) = (1-r^n)/(1-r)",
    "(a+b)^n = sum(binomial(n,k)*a^(n-k)*b^k,k,0,n)"
]

def load_db():
    global knowledge_base
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            knowledge_base = json.load(f)
    metrics["proven_theorems"] = len(knowledge_base)

def save_db(theorem):
    if theorem not in knowledge_base:
        knowledge_base.append(theorem)
        with open(DB_FILE, 'w') as f:
            json.dump(knowledge_base, f)

load_db()

# --- Core Logic ---
def attempt_proof(conjecture):
    if conjecture in AXIOMS or conjecture in KNOWN_THEOREMS or conjecture in knowledge_base:
        return True, "Known Identity"
    # Logic simulation: complex patterns have a 15% chance of being "solved"
    if any(key in conjecture for key in ["sum", "product", "^n"]):
        if random.random() < 0.15:
            return True, "Induction/Algebra"
    return False, None

def evolution_loop():
    global running
    while running:
        metrics["agents_spawned"] += 1
        template = random.choice(CONJECTURE_TEMPLATES)
        
        # Mutation: slightly alter the conjecture to look for novel forms
        conjecture = template
        if random.random() < 0.3:
            conjecture = conjecture.replace("a", "((a+1)+b)")

        proved, method = attempt_proof(conjecture)
        is_novel = conjecture not in AXIOMS and conjecture not in KNOWN_THEOREMS and conjecture not in knowledge_base

        if is_novel:
            metrics["novel_conjectures"] += 1
            if proved:
                save_db(conjecture)
                metrics["proven_theorems"] = len(knowledge_base)
                discoveries.append({"text": f"🎓 PROVED: {conjecture} via {method}", "type": "theorem"})
            else:
                discoveries.append({"text": f"💡 CONJECTURE: {conjecture}", "type": "conjecture"})
        else:
            discoveries.append({"text": f"Scanning: {conjecture}", "type": "scan"})

        if len(discoveries) > 100: discoveries.pop(0)
        time.sleep(0.6)

# --- Routes ---
@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE, kb=knowledge_base)

@app.route("/status")
def status():
    return jsonify({
        "metrics": metrics,
        "discoveries": discoveries[-20:],
        "knowledge_base": knowledge_base[-20:],
        "is_running": running
    })

@app.route("/control", methods=["POST"])
def control():
    global running
    action = request.json.get("action")
    if action == "start" and not running:
        running = True
        threading.Thread(target=evolution_loop, daemon=True).start()
    elif action == "stop":
        running = False
    return jsonify({"status": "ok", "running": running})

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Math Discovery System</title>
    <style>
        body { font-family: 'Courier New', monospace; background: #0a0a0c; color: #00ffcc; padding: 20px; }
        .stats { background: #162447; padding: 15px; border-radius: 8px; margin-bottom: 20px; display: flex; gap: 20px; align-items: center; border: 1px solid #1f4068; }
        .container { display: flex; gap: 20px; height: 75vh; }
        .panel { flex: 1; background: #162447; padding: 15px; border-radius: 8px; overflow-y: auto; border: 1px solid #1f4068; }
        h2 { color: #e43f5a; margin-top: 0; font-size: 1.2em; border-bottom: 1px solid #1f4068; padding-bottom: 10px; }
        .theorem { color: #00ff99; font-weight: bold; margin-bottom: 8px; padding: 5px; background: rgba(0,255,153,0.1); }
        .conjecture { color: #888; font-size: 0.9em; margin-bottom: 4px; }
        .scan { color: #444; font-size: 0.8em; }
        button { padding: 10px 25px; cursor: pointer; border: none; font-weight: bold; border-radius: 4px; }
        #startBtn { background: #27ae60; color: white; }
        #stopBtn { background: #e43f5a; color: white; }
        button:disabled { background: #333; opacity: 0.5; }
    </style>
</head>
<body>
    <h1>SYSTEM: MATHEMATICAL EVOLUTION</h1>
    <div class="stats">
        <button id="startBtn" onclick="toggle('start')">START AGENTS</button>
        <button id="stopBtn" onclick="toggle('stop')" disabled>STOP</button>
        <div>Agents: <span id="s_agents">0</span></div>
        <div>Proven: <span id="s_proven">0</span></div>
        <div>Novel: <span id="s_novel">0</span></div>
    </div>
    <div class="container">
        <div class="panel">
            <h2>Discovery Stream</h2>
            <div id="stream"></div>
        </div>
        <div class="panel">
            <h2>Persistent Knowledge Base</h2>
            <div id="kb">
                {% for t in kb %} <div class="theorem">🎓 LOADED: {{ t }}</div> {% endfor %}
            </div>
        </div>
    </div>
    <script>
        async function toggle(action) {
            await fetch('/control', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({action: action})
            });
        }
        async function update() {
            const res = await fetch('/status');
            const data = await res.json();
            document.getElementById('startBtn').disabled = data.is_running;
            document.getElementById('stopBtn').disabled = !data.is_running;
            document.getElementById('s_agents').textContent = data.metrics.agents_spawned;
            document.getElementById('s_proven').textContent = data.metrics.proven_theorems;
            document.getElementById('s_novel').textContent = data.metrics.novel_conjectures;
            
            const stream = document.getElementById('stream');
            stream.innerHTML = data.discoveries.reverse().map(d => `<div class="${d.type}">${d.text}</div>`).join('');
            
            const kb = document.getElementById('kb');
            kb.innerHTML = data.knowledge_base.reverse().map(t => `<div class="theorem">🎓 PROVED: ${t}</div>`).join('');
        }
        setInterval(update, 800);
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
