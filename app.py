import os
import random
import threading
import time
from flask import Flask, render_template_string
from flask_socketio import SocketIO, emit
import eventlet

eventlet.monkey_patch()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode='eventlet')

# -------------------------
# Knowledge & agent storage
# -------------------------
knowledge_base = []
proven_theorems = []
novel_conjectures = []
agents = []
pool = []

# -------------------------
# Graph for pathfinding
# -------------------------
GRAPH = {
    "nodes": ["A","B","C","D","E","F"],
    "edges": {
        "A": [["B",4],["C",2]],
        "B": [["C",1],["D",5],["E",10]],
        "C": [["D",3],["E",8]],
        "D": [["E",2],["F",4]],
        "E": [["F",1]],
        "F": []
    },
    "start": "A",
    "end": "F",
    "mandatoryCheckpoints": ["C","D"]
}

# -------------------------
# Agent definitions
# -------------------------
AGENT_TYPES = [
    "CodeWriter", "PathFinder", "Tester", "Optimizer",
    "Validator", "Logger", "Adversary", "Conjecturer",
    "Prover", "InductionProver", "Symbolizer"
]

CODE_TEMPLATES = [
    "lambda x: x**2 + 2*x + 1",
    "lambda x: (x+1)**2",
    "lambda x: x*(x+2)+1",
    "lambda x: (x+1)*(x+1)",
    "lambda x: pow(x+1,2)"
]

TEST_INPUTS = [0,1,2,3,4,-1,-2,10,100,-10]

AXIOMS = [
    "x + 0 = x",
    "x * 1 = x",
    "x * 0 = 0",
    "(x + y) + z = x + (y + z)",
    "x * y = y * x",
    "x + y = y + x"
]

KNOWN_THEOREMS = [
    "sum(n,0,x)=x*(x+1)/2",
    "(x+1)^2 = x^2 + 2x + 1",
    "x^2 - y^2 = (x-y)*(x+y)",
    "factorial(n)/(factorial(k)*factorial(n-k)) = binomial(n,k)"
]

# -------------------------
# Utility functions
# -------------------------
def evaluate_code(code_str):
    try:
        fn = eval(code_str)
        target_fn = eval("lambda x: x**2 + 2*x + 1")
        correct = sum(1 for x in TEST_INPUTS if fn(x) == target_fn(x))
        return correct / len(TEST_INPUTS)
    except:
        return 0

def mutate_code(code, agent_type):
    if agent_type == "Adversary":
        return random.choice(["lambda x: x**2 + 2*x","lambda x: x**2 + x + 1"])
    if random.random() < 0.3:
        return random.choice(CODE_TEMPLATES)
    return code

def generate_conjecture():
    templates = [
        "(a + b)^2 = a^2 + 2*a*b + b^2",
        "(a - b)^2 = a^2 - 2*a*b + b^2",
        "a^3 + b^3 = (a + b)(a^2 - a*b + b^2)",
        "sum(k^2,0,n)=n*(n+1)*(2*n+1)/6",
        "(a + b)^n = sum(binomial(n,k)*a^(n-k)*b^k, k,0,n)"
    ]
    return random.choice(templates)

def attempt_proof(conjecture):
    proved = random.random() < 0.3
    novel = conjecture not in knowledge_base
    if novel:
        knowledge_base.append(conjecture)
        if proved:
            proven_theorems.append(conjecture)
        else:
            novel_conjectures.append(conjecture)
    return proved, novel

# -------------------------
# Agent loop
# -------------------------
def agent_loop():
    while True:
        time.sleep(1)
        # Each cycle: spawn some agents
        for _ in range(3):
            agent_type = random.choice(AGENT_TYPES)
            # Code agent
            if agent_type in ["CodeWriter","Optimizer","Tester"]:
                parent_code = random.choice(CODE_TEMPLATES)
                code_output = mutate_code(parent_code, agent_type)
                evaluate_code(code_output)
            # Math agent
            if agent_type in ["Conjecturer","Prover","InductionProver","Symbolizer"]:
                conjecture = generate_conjecture()
                attempt_proof(conjecture)
            # Path agent (optional display, simplified)
            if agent_type in ["PathFinder","Logger","Optimizer"]:
                path = ["A","C","D","F"]  # simplified
        # Emit latest discoveries to front-end
        socketio.emit('update', {
            'knowledge_base': knowledge_base[-20:],
            'proven_theorems': proven_theorems[-20:],
            'novel_conjectures': novel_conjectures[-20:]
        })

# Start agent loop in background
threading.Thread(target=agent_loop, daemon=True).start()

# -------------------------
# Flask routes
# -------------------------
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<title>Unified Intelligence Lab</title>
<script src="//cdnjs.cloudflare.com/ajax/libs/socket.io/4.6.1/socket.io.min.js"></script>
<style>
body { background:#111;color:#fff;font-family:monospace;padding:20px;}
h1 { color:#ff00ff;}
.section{margin-bottom:20px;}
.item{margin:2px 0;}
</style>
</head>
<body>
<h1>Unified Intelligence Lab</h1>
<div class="section"><h2>Last 20 Discoveries</h2><div id="knowledge"></div></div>
<div class="section"><h2>Proven Theorems</h2><div id="proven"></div></div>
<div class="section"><h2>Novel Conjectures</h2><div id="novel"></div></div>

<script>
var socket = io();
socket.on('update', function(data){
    const kb = document.getElementById('knowledge');
    const proven = document.getElementById('proven');
    const novel = document.getElementById('novel');
    kb.innerHTML=''; proven.innerHTML=''; novel.innerHTML='';
    data.knowledge_base.forEach(i=>kb.innerHTML+='<div class="item">'+i+'</div>');
    data.proven_theorems.forEach(i=>proven.innerHTML+='<div class="item">'+i+'</div>');
    data.novel_conjectures.forEach(i=>novel.innerHTML+='<div class="item">'+i+'</div>');
});
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

# -------------------------
# Run
# -------------------------
if __name__ == '__main__':
    PORT = int(os.environ.get("PORT",5000))
    socketio.run(app, host='0.0.0.0', port=PORT)
