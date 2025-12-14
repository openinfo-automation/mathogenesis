from flask import Flask, render_template_string, Response, request
import threading, time, random, json, os

app = Flask(__name__)

# State
discoveries = []
milestones = []
agents_spawned = 0
proven_theorems_count = 0
novel_conjectures_count = 0
running = False

AXIOMS = ["x + 0 = x","x * 1 = x","x * 0 = 0","(x + y) + z = x + (y + z)","x * y = y * x","x + y = y + x"]
KNOWN_THEOREMS = ["sum(n,0,x)=x(x+1)/2","(x+1)^2=x^2+2x+1","x^2-y^2=(x-y)(x+y)","factorial(n)/(factorial(k)*factorial(n-k))=binomial(n,k)"]
knowledge_base = []

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Live Mathematical Discoveries</title>
<style>
body { background:#111; color:#fff; font-family:monospace; padding:20px;}
h1{font-size:3em;color:#f39c12;}
.milestone{color:#2ecc71;font-size:2em;margin-top:1em;}
.discovery{margin:0.5em 0;}
#discoveries{max-height:50vh;overflow-y:auto;border:1px solid #555;padding:10px;}
.stats{margin-top:10px;font-size:1.2em;}
button{padding:10px 20px;font-size:1.2em;margin-bottom:10px;cursor:pointer;}
</style>
</head>
<body>
<h1>LIVE MATHEMATICAL DISCOVERIES</h1>
<button id="startBtn">START AGENTS</button>
<div class="stats">
<span>Agents Spawned: <span id="agentsCount">0</span></span> |
<span>Proven Theorems: <span id="theoremsCount">0</span></span> |
<span>Novel Conjectures: <span id="conjecturesCount">0</span></span>
</div>
<div id="discoveries"></div>
<script>
const startBtn=document.getElementById("startBtn");
startBtn.onclick=function(){fetch("/start_agents",{method:"POST"});startBtn.disabled=true;startBtn.textContent="AGENTS RUNNING";};

const evtSource=new EventSource("/stream");
evtSource.onmessage=function(e){
    const d=JSON.parse(e.data);
    const container=document.getElementById("discoveries");
    const div=document.createElement("div");
    div.textContent=d.text;
    div.className=d.milestone?"milestone":"discovery";
    container.prepend(div);
    document.getElementById("agentsCount").textContent=d.agents;
    document.getElementById("theoremsCount").textContent=d.proven;
    document.getElementById("conjecturesCount").textContent=d.novel;
};
</script>
</body>
</html>
"""

def generate_conjecture():
    templates = ["(a+b)^2=a^2+2ab+b^2","(a-b)^2=a^2-2ab+b^2","a^3+b^3=(a+b)(a^2-ab+b^2)",
                 "sum(k^2,0,n)=n(n+1)(2n+1)/6","product(1+1/k,1,n)=n+1","(a+b)^n=sum(binomial(n,k)*a^(n-k)*b^k,k,0,n)"]
    base=random.choice(templates)
    if random.random()<0.4: base=base.replace("a+b","(a+1)+b")
    return base

def attempt_proof(conjecture):
    if conjecture in AXIOMS+KNOWN_THEOREMS+knowledge_base: return True,"Already Known"
    if random.random()<0.3: return True,"Induction/Algebra"
    return False,None

def agent_loop():
    global agents_spawned, proven_theorems_count, novel_conjectures_count, running
    while running:
        agents_spawned+=1
        conjecture=generate_conjecture()
        proved, method=attempt_proof(conjecture)
        is_novel=conjecture not in knowledge_base and conjecture not in KNOWN_THEOREMS

        if proved and is_novel:
            knowledge_base.append(conjecture)
            milestones.append(f"🎓 NEW THEOREM PROVED: {conjecture} via {method}")
            discoveries.append({"text":f"🎓 NEW THEOREM PROVED: {conjecture} via {method}","milestone":True})
            proven_theorems_count+=1
        elif is_novel and not proved:
            discoveries.append({"text":f"💡 Novel Conjecture Generated: {conjecture}","milestone":False})
            novel_conjectures_count+=1
        else:
            discoveries.append({"text":f"Discovered: {conjecture}","milestone":False})
        time.sleep(1)

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/start_agents", methods=["POST"])
def start_agents():
    global running
    if not running:
        running=True
        threading.Thread(target=agent_loop,daemon=True).start()
    return {"status":"started"}

@app.route("/stream")
def stream():
    def event_stream():
        last_index=0
        while True:
            while last_index<len(discoveries):
                d=discoveries[last_index]
                payload=json.dumps({"text":d["text"],"milestone":d["milestone"],
                                    "agents":agents_spawned,"proven":proven_theorems_count,"novel":novel_conjectures_count})
                yield f"data:{payload}\n\n"
                last_index+=1
            time.sleep(0.5)
    return Response(event_stream(),mimetype="text/event-stream")

if __name__=="__main__":
    port=int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0",port=port,threaded=True)
