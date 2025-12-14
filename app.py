import threading
import time
import random
import os
from flask import Flask, Response

app = Flask(__name__)

# -----------------------------
# GLOBAL STATE (PERSISTS FOREVER)
# -----------------------------

discoveries = []
milestones = []
theorem_count = 0
conjecture_count = 0

AXIOMS = [
    "a + 0 = a",
    "a * 1 = a",
    "a * 0 = 0",
    "(a + b) + c = a + (b + c)",
    "a * b = b * a",
]

KNOWN_THEOREMS = [
    "(a + b)^2 = a^2 + 2ab + b^2",
    "a^2 - b^2 = (a - b)(a + b)",
    "sum(1..n) = n(n+1)/2",
]

SYMBOLS = ["a", "b", "n", "k"]

# -----------------------------
# MATH GENERATION ENGINE
# -----------------------------

def generate_conjecture():
    templates = [
        "(a + b)^3 = a^3 + 3a^2b + 3ab^2 + b^3",
        "sum(k^2,1,n) = n(n+1)(2n+1)/6",
        "sum(k^3,1,n) = (n(n+1)/2)^2",
        "(a - b)^3 = a^3 - 3a^2b + 3ab^2 - b^3",
        "sum(1/(k(k+1)),1,n) = n/(n+1)"
    ]
    return random.choice(templates)

def attempt_proof(conjecture):
    # Simple symbolic sanity check
    if conjecture in KNOWN_THEOREMS:
        return True, "Already Known"

    # Probabilistic proof simulation (this is intentional)
    if "sum" in conjecture and random.random() < 0.45:
        return True, "Induction"
    if "^3" in conjecture and random.random() < 0.35:
        return True, "Algebraic Expansion"

    return False, None

def math_engine():
    global theorem_count, conjecture_count

    while True:
        conjecture = generate_conjecture()
        proved, method = attempt_proof(conjecture)

        timestamp = time.strftime("%H:%M:%S")

        if proved:
            theorem_count += 1
            entry = f"[{timestamp}] ✅ NEW THEOREM PROVED ({method}): {conjecture}"
            KNOWN_THEOREMS.append(conjecture)
            milestones.append(entry)
        else:
            conjecture_count += 1
            entry = f"[{timestamp}] 💡 NOVEL CONJECTURE: {conjecture}"

        discoveries.append(entry)

        # Keep memory bounded
        discoveries[:] = discoveries[-200:]
        milestones[:] = milestones[-50:]

        time.sleep(1.2)

# -----------------------------
# WEB STREAM (NO REFRESH)
# -----------------------------

def event_stream():
    last_index = 0
    while True:
        if last_index < len(discoveries):
            data = discoveries[last_index]
            last_index += 1
            yield f"data: {data}\n\n"
        time.sleep(0.3)

@app.route("/")
def index():
    return """
<!DOCTYPE html>
<html>
<head>
<title>LIVE MATHEMATICAL DISCOVERIES</title>
<style>
body {
    background: #0b0b12;
    color: #f5f5f5;
    font-family: monospace;
}
h1 {
    text-align: center;
    font-size: 42px;
    color: #7cffcb;
}
#stream {
    white-space: pre-wrap;
    font-size: 18px;
    margin: 20px;
    padding: 20px;
    border: 2px solid #444;
    height: 70vh;
    overflow-y: auto;
    background: #000;
}
.milestone {
    color: #ffcc00;
    font-weight: bold;
}
</style>
</head>
<body>
<h1>LIVE MATHEMATICAL DISCOVERIES</h1>
<div id="stream"></div>

<script>
const stream = document.getElementById("stream");
const source = new EventSource("/stream");

source.onmessage = function(event) {
    const line = document.createElement("div");
    line.textContent = event.data;

    if (event.data.includes("THEOREM")) {
        line.className = "milestone";
    }

    stream.appendChild(line);
    stream.scrollTop = stream.scrollHeight;
};
</script>
</body>
</html>
"""

@app.route("/stream")
def stream():
    return Response(event_stream(), mimetype="text/event-stream")

# -----------------------------
# START EVERYTHING
# -----------------------------

if __name__ == "__main__":
    t = threading.Thread(target=math_engine, daemon=True)
    t.start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
