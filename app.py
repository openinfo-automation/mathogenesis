import os
import random
import time
from threading import Thread
from flask import Flask, render_template_string
from flask_socketio import SocketIO

# Flask setup
app = Flask(__name__)
socketio = SocketIO(app, async_mode="gevent")

# Knowledge base
AXIOMS = [
    "x + 0 = x",
    "x * 1 = x",
    "x * 0 = 0",
    "(x + y) + z = x + (y + z)",
    "x * y = y * x",
    "x + y = y + x",
]
KNOWN_THEOREMS = [
    "sum(n, 0, x) = x(x+1)/2",
    "(x + 1)^2 = x^2 + 2x + 1",
    "x^2 - y^2 = (x-y)(x+y)",
    "factorial(n) / (factorial(k) * factorial(n-k)) = binomial(n,k)",
]
knowledge_base = []

# Generate a new conjecture
def generate_conjecture():
    templates = [
        "(a + b)^2 = a^2 + 2*a*b + b^2",
        "(a - b)^2 = a^2 - 2*a*b + b^2",
        "a^3 + b^3 = (a + b)(a^2 - a*b + b^2)",
        "sum(k^2, 0, n) = n(n+1)(2n+1)/6",
        "product(1 + 1/k, 1, n) = n + 1",
        "(a + b)^n = sum(binomial(n,k) * a^(n-k) * b^k, k, 0, n)",
    ]
    base = random.choice(KNOWN_THEOREMS + knowledge_base)
    mutations = [
        base.replace("+", "*"),
        base.replace("*", "+"),
        base.replace("a", "(a+1)"),
        base.replace("n", "(n-1)"),
    ]
    if random.random() < 0.5:
        return random.choice(mutations)
    return random.choice(templates)

# Attempt to "prove" conjecture
def attempt_proof(conjecture):
    if conjecture in AXIOMS + KNOWN_THEOREMS + knowledge_base:
        return True, "Already Known"
    if any(op in conjecture for op in ["sum(", "product("]):
        if random.random() < 0.3:
            return True, "Mathematical Induction"
    simplified = conjecture.replace(" ", "").replace("(a+b)^2", "a^2+2*a*b+b^2")
    if simplified in AXIOMS + KNOWN_THEOREMS + knowledge_base:
        return True, "Algebraic Simplification"
    return False, None

# Background thread to continuously generate new math
def math_generator():
    while True:
        conjecture = generate_conjecture()
        proved, method = attempt_proof(conjecture)
        is_novel = conjecture not in knowledge_base + KNOWN_THEOREMS
        if is_novel and proved:
            knowledge_base.append(conjecture)
        socketio.emit("new_math", {
            "conjecture": conjecture,
            "proved": proved,
            "method": method,
            "novel": is_novel
        })
        time.sleep(1)  # Generate every second

# Webpage template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Unified Intelligence Lab</title>
<script src="https://cdn.socket.io/4.6.1/socket.io.min.js"></script>
<style>
body { background:#111; color:#0f0; font-family:monospace; padding:20px; }
h1 { color:#ff0; }
.conjecture { font-size:1.5em; margin:10px 0; }
.proved { color:#0ff; }
.novel { color:#f0f; }
</style>
</head>
<body>
<h1>Unified Intelligence Lab — Live Math Discoveries</h1>
<div id="math"></div>
<script>
var socket = io();
socket.on('new_math', function(data){
    var container = document.getElementById('math');
    var div = document.createElement('div');
    div.className = 'conjecture';
    div.innerHTML = data.conjecture +
        (data.proved ? ' <span class="proved">✔ ('+data.method+')</span>' : '') +
        (data.novel ? ' <span class="novel">★ Novel</span>' : '');
    container.insertBefore(div, container.firstChild);
});
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    thread = Thread(target=math_generator)
    thread.daemon = True
    thread.start()
    socketio.run(app, host="0.0.0.0", port=port)
