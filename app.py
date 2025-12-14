import os
import time
import random
import threading
from collections import deque, defaultdict

from flask import Flask, render_template_string
from flask_socketio import SocketIO

# ======================
# Flask / SocketIO
# ======================
app = Flask(__name__)
app.config["SECRET_KEY"] = "infinite-symbolic-math"
socketio = SocketIO(app, async_mode="gevent", cors_allowed_origins="*")

PORT = int(os.environ.get("PORT", 5000))

# ======================
# Persistent Memory
# ======================
DISCOVERIES = deque(maxlen=200)
STRUCTURAL_CLASSES = defaultdict(int)
DERIVATION_GRAPH = defaultdict(set)
GEN = 0

# ======================
# Base Symbolic Knowledge
# ======================
SYMBOLS = ["a", "b", "c", "x", "y", "z"]

AXIOMS = {
    "comm_add": "a + b = b + a",
    "comm_mul": "a * b = b * a",
    "assoc_add": "(a + b) + c = a + (b + c)",
    "assoc_mul": "(a * b) * c = a * (b * c)",
    "dist": "a * (b + c) = a*b + a*c",
}

# ======================
# Symbolic Generation
# ======================
def generate_expression():
    s1, s2, s3 = random.sample(SYMBOLS, 3)
    patterns = [
        (f"({s1}+{s2})^2", f"{s1}^2 + 2*{s1}*{s2} + {s2}^2", "binomial_square"),
        (f"({s1}-{s2})^2", f"{s1}^2 - 2*{s1}*{s2} + {s2}^2", "binomial_square"),
        (f"{s1}^2 - {s2}^2", f"({s1}-{s2})({s1}+{s2})", "difference_of_squares"),
        (f"{s1}^3 - {s2}^3", f"({s1}-{s2})({s1}^2+{s1}{s2}+{s2}^2)", "difference_of_cubes"),
        (f"({s1}+{s2}+{s3})^2",
         f"{s1}^2+{s2}^2+{s3}^2+2({s1}{s2}+{s1}{s3}+{s2}{s3})",
         "trinomial_square"),
    ]
    return random.choice(patterns)

# ======================
# Milestone Classification
# ======================
def classify(lhs, rhs, structure):
    STRUCTURAL_CLASSES[structure] += 1
    depth = random.randint(1, 4)

    milestone = None
    if STRUCTURAL_CLASSES[structure] == 1:
        milestone = "🔵 NEW STRUCTURAL CLASS"
    elif depth >= 3:
        milestone = "🟣 COMPOSITE DERIVATION"
    elif STRUCTURAL_CLASSES[structure] <= 2:
        milestone = "🟡 RARE FORM"

    if depth >= 3 and STRUCTURAL_CLASSES[structure] >= 3:
        milestone = "🔴 MAJOR MILESTONE"

    return milestone, depth

# ======================
# Engine (NEVER STOPS)
# ======================
def math_engine():
    global GEN
    while True:
        time.sleep(random.uniform(1.2, 2.8))
        GEN += 1

        lhs, rhs, structure = generate_expression()
        milestone, depth = classify(lhs, rhs, structure)

        entry = {
            "gen": GEN,
            "lhs": lhs,
            "rhs": rhs,
            "structure": structure,
            "depth": depth,
            "milestone": milestone
        }

        DISCOVERIES.appendleft(entry)

        socketio.emit("update", {
            "latest": entry,
            "all": list(DISCOVERIES)
        })

# ======================
# Web UI
# ======================
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Infinite Symbolic Math Engine</title>
<script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
<style>
body {
    background:black;
    color:#00ffcc;
    font-family:monospace;
}
h1 { font-size:32px; }
.entry {
    font-size:20px;
    margin:10px 0;
}
.milestone {
    font-size:24px;
    color:#ff3366;
    font-weight:bold;
}
.meta {
    font-size:14px;
    color:#aaa;
}
</style>
</head>
<body>
<h1>LIVE MATHEMATICAL DISCOVERIES</h1>
<div id="stream"></div>

<script>
const socket = io();
const stream = document.getElementById("stream");

socket.on("update", data => {
    stream.innerHTML = "";
    data.all.forEach(e => {
        const div = document.createElement("div");
        div.className = "entry";
        div.innerHTML = `
            <div>${e.lhs} = ${e.rhs}</div>
            <div class="meta">GEN ${e.gen} | DEPTH ${e.depth} | ${e.structure}</div>
            ${e.milestone ? `<div class="milestone">${e.milestone}</div>` : ""}
        `;
        stream.appendChild(div);
    });
});
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

# ======================
# Boot
# ======================
if __name__ == "__main__":
    threading.Thread(target=math_engine, daemon=True).start()
    socketio.run(app, host="0.0.0.0", port=PORT)
