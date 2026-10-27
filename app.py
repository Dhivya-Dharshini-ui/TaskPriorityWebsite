from flask import Flask, request, jsonify, render_template_string
import sqlite3, os, time
from datetime import date

app = Flask(__name__)
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tasks.db')
RANK = {'High': 3, 'Medium': 2, 'Low': 1}


def db_connect():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_db():
    with db_connect() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS tasks (
            task_id TEXT PRIMARY KEY, description TEXT NOT NULL,
            priority TEXT NOT NULL, deadline TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending')''')
        if conn.execute('SELECT COUNT(*) FROM tasks').fetchone()[0] == 0:
            examples = [
                ('Complete project proposal','High'),('Prepare presentation slides','Medium'),
                ('Study data structures','High'),('Submit programming assignment','High'),
                ('Review database concepts','Low'),('Practice binary search','Medium'),
                ('Complete lab record','High'),('Prepare for examination','High'),
                ('Test website functionality','Medium'),('Write project documentation','Low'),
                ('Review Python programming','Medium'),('Complete sorting algorithms','High'),
                ('Prepare class notes','Low'),('Study operating systems','Medium'),
                ('Finish software engineering work','High'),('Debug application code','High'),
                ('Update project report','Medium'),('Practice SQL queries','Low'),
                ('Complete weekly assignment','Medium'),('Prepare demonstration','High'),
                ('Review algorithm complexity','Low'),('Test priority queue','Medium'),
                ('Organize project files','Low'),('Complete practical exercises','Medium'),
                ('Finalize project submission','High')]
            for i, (desc, priority) in enumerate(examples):
                conn.execute('INSERT INTO tasks VALUES (?, ?, ?, ?, ?)',
                    (f'T{101+i}', desc, priority, f'2026-11-{i%28+1:02d}', 'Pending'))


def get_tasks():
    with db_connect() as conn:
        return [dict(r) for r in conn.execute('SELECT * FROM tasks').fetchall()]


def sort_key(task, field):
    if field == 'deadline':
        return (task['deadline'], task['task_id'])
    if field == 'id':
        return task['task_id']
    return (-RANK[task['priority']], task['deadline'], task['task_id'])


def insertion_sort(items, key):
    arr, comparisons = items.copy(), 0
    for i in range(1, len(arr)):
        current, j = arr[i], i - 1
        while j >= 0:
            comparisons += 1
            if key(arr[j]) <= key(current):
                break
            arr[j+1] = arr[j]
            j -= 1
        arr[j+1] = current
    return arr, comparisons


def merge_sort(items, key):
    comparisons = 0
    def divide(arr):
        nonlocal comparisons
        if len(arr) <= 1:
            return arr
        mid = len(arr)//2
        left, right = divide(arr[:mid]), divide(arr[mid:])
        out, i, j = [], 0, 0
        while i < len(left) and j < len(right):
            comparisons += 1
            if key(left[i]) <= key(right[j]):
                out.append(left[i]); i += 1
            else:
                out.append(right[j]); j += 1
        return out + left[i:] + right[j:]
    return divide(items.copy()), comparisons


PAGE = r'''<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>TaskFlow | Task Priority Management</title>
<style>
:root{--bg:#f5f7fc;--card:#fff;--ink:#1d2638;--muted:#7b879b;--line:#e8edf5;--blue:#5367f2;--nav:#171d30;--green:#159a70;--red:#df5362;--amber:#c98b19;--shadow:0 8px 28px #263b5b0a}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px Inter,"Segoe UI",Arial,sans-serif}button,input,select{font:inherit}button{cursor:pointer;transition:.15s}button:active{transform:scale(.98)}.layout{min-height:100vh;display:grid;grid-template-columns:245px minmax(0,1fr)}aside{background:var(--nav);color:#dbe1ef;padding:25px 16px;display:flex;flex-direction:column;gap:30px}.brand{display:flex;align-items:center;gap:11px;padding:0 9px}.logo{height:40px;width:40px;border-radius:13px;background:linear-gradient(135deg,#8994ff,#5367f2);display:grid;place-items:center;color:#fff;font-size:22px;font-weight:900}.brand strong{font-size:19px;color:white;letter-spacing:-.5px}.brand small{display:block;color:#939db7;font-size:10px;letter-spacing:1.4px;text-transform:uppercase;margin-top:3px}.navlabel{font-size:10px;letter-spacing:1.7px;color:#7d87a3;padding:0 12px;margin-bottom:-20px;font-weight:800}.nav{display:grid;gap:7px}.nav button{border:0;background:transparent;color:#b2bbd0;padding:13px 12px;text-align:left;border-radius:10px;display:flex;align-items:center;gap:12px;font-weight:600}.nav button span{width:22px;text-align:center;font-size:17px}.nav button:hover,.nav button.active{background:#2a324b;color:white}.nav button.active{box-shadow:inset 3px 0 #919bff}.sidefoot{margin-top:auto;padding:15px;border:1px solid #303950;background:#20283c;border-radius:13px;color:#aeb7cd;font-size:12px;line-height:1.6}.sidefoot b{display:block;color:#fff;font-size:13px;margin-bottom:5px}.dot{display:inline-block;width:7px;height:7px;background:#36c99a;border-radius:50%;margin-right:7px}.main{min-width:0}.topbar{height:76px;background:white;border-bottom:1px solid var(--line);padding:0 34px;display:flex;align-items:center;justify-content:space-between}.crumb{color:var(--muted)}.crumb b{color:var(--ink)}.topright{display:flex;align-items:center;gap:17px}.today{font-size:12px;color:var(--muted)}.avatar{height:38px;width:38px;border-radius:50%;background:#e9ebff;color:#4d5ee0;display:grid;place-items:center;font-weight:800}.content{max-width:1500px;padding:30px 34px 45px;margin:auto}.heading{display:flex;align-items:flex-end;justify-content:space-between;gap:20px;margin-bottom:24px}.eyebrow{color:var(--blue);font-size:10px;font-weight:800;letter-spacing:1.8px;margin-bottom:9px}.heading h1{font-size:29px;letter-spacing:-1px;margin:0 0 8px}.sub{color:var(--muted);margin:0;line-height:1.6}.btn{border:0;border-radius:9px;padding:11px 15px;font-weight:700;display:inline-flex;align-items:center;justify-content:center;gap:7px}.primary{background:var(--blue);color:#fff;box-shadow:0 5px 12px #5367f226}.primary:hover{background:#4052dc}.light{background:#f5f6fb;color:#46516a;border:1px solid var(--line)}.light:hover{background:#eaedf6}.stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:15px;margin-bottom:22px}.stat,.panel{background:var(--card);border:1px solid var(--line);border-radius:16px;box-shadow:var(--shadow)}.stat{padding:19px 20px}.stathead{display:flex;justify-content:space-between;align-items:center;color:var(--muted);font-size:12px;font-weight:650}.staticon{width:36px;height:36px;border-radius:11px;display:grid;place-items:center;font-size:17px}.ib{background:#eef0ff;color:#5367f2}.ig{background:#e7f8f1;color:#159a70}.ia{background:#fff5df;color:#c18413}.ir{background:#ffedef;color:#df5362}.value{font-size:30px;font-weight:800;letter-spacing:-1px;margin:12px 0 4px}.statfoot{font-size:11px;color:var(--muted)}.statfoot strong{color:var(--green)}.columns{display:grid;grid-template-columns:minmax(0,1.65fr) minmax(270px,.85fr);gap:20px;align-items:start}.panel{margin-bottom:20px;overflow:hidden}.panelhead{padding:20px 22px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:center;gap:15px}.panelhead h2,.right h2{font-size:15px;margin:0 0 5px}.panelhead p,.right .desc{margin:0;color:var(--muted);font-size:12px;line-height:1.6}.panelbody{padding:22px}.tablewrap{overflow-x:auto}table{width:100%;border-collapse:collapse;min-width:650px}th{background:#fafbfe;color:#8994a7;font-size:10px;text-transform:uppercase;letter-spacing:1px;text-align:left;padding:13px 17px}td{padding:14px 17px;border-bottom:1px solid #eff2f7;font-size:12px;vertical-align:middle}tbody tr:last-child td{border-bottom:0}tbody tr:hover{background:#fafbff}.tid{font-weight:800;color:#4c5fe0}.tdesc{font-weight:650;color:#30394b;max-width:240px}.badge{display:inline-flex;align-items:center;gap:5px;border-radius:20px;padding:5px 8px;font-size:10px;font-weight:800;white-space:nowrap}.badge:before{content:"";width:5px;height:5px;border-radius:50%;background:currentColor}.High{background:#fff0f1;color:#d84756}.Medium{background:#fff5df;color:#b77a0b}.Low{background:#e9f8f1;color:#15845f}.Pending{background:#edf1ff;color:#5367d9}.Completed{background:#e7f8f1;color:#15845f}.actions{display:flex;gap:5px}.mini{border:1px solid var(--line);background:white;color:#667187;border-radius:7px;padding:6px 8px;font-size:11px;font-weight:700}.mini:hover{background:#f2f4ff;color:var(--blue)}.right{padding:20px}.right .desc{margin-bottom:17px}.queue{display:grid;gap:9px}.qitem{display:flex;gap:11px;align-items:flex-start;padding:12px;background:#fafbfe;border:1px solid #eff2f7;border-radius:11px}.qnum{height:29px;width:29px;flex-shrink:0;border-radius:9px;display:grid;place-items:center;background:#eceeff;color:#5367f2;font-size:11px;font-weight:800}.qtitle{font-size:12px;font-weight:750;margin:1px 0 6px;line-height:1.4}.qmeta{font-size:10px;color:var(--muted)}.progress-title{display:flex;justify-content:space-between;font-size:12px;margin:20px 0 10px;font-weight:700}.track{height:7px;background:#edf0f6;border-radius:10px;overflow:hidden}.fill{height:100%;background:linear-gradient(90deg,#5367f2,#8d98ff);border-radius:10px}.quick{display:grid;gap:9px}.quick button{display:flex;justify-content:space-between;padding:12px;border:1px solid var(--line);border-radius:10px;background:#fff;color:#46516a;font-size:12px;font-weight:700}.quick button:hover{border-color:#c6ccff;background:#fafaff}.fieldgrid{display:grid;grid-template-columns:1fr 1.6fr;gap:15px}.field{display:flex;flex-direction:column;gap:8px;font-size:12px;font-weight:700;color:#49556a}.field input,.field select,.toolbar input,.toolbar select,.labbar input,.labbar select{width:100%;border:1px solid #dfe5ef;border-radius:9px;background:#fff;padding:11px 12px;color:var(--ink);outline:none;min-width:0}.field input:focus,.field select:focus,.toolbar input:focus,.labbar input:focus,.labbar select:focus{border-color:#8994ff;box-shadow:0 0 0 3px #5367f214}.formactions{display:flex;gap:9px;margin-top:17px;flex-wrap:wrap}.toolbar,.labbar{display:flex;gap:10px;padding:15px 22px;align-items:center;flex-wrap:wrap;border-bottom:1px solid var(--line)}.toolbar input{flex:1;min-width:160px}.toolbar select{width:auto;max-width:180px}.labbar{padding:0;border:0;margin-bottom:15px}.labbar input,.labbar select{width:auto;flex:1;min-width:145px}.result{border:1px solid var(--line);background:#fafbff;border-radius:11px;padding:16px;line-height:1.85;overflow-wrap:anywhere;color:#4b5870;font-size:12px}.result h3{color:var(--ink);margin-top:0}.empty{text-align:center;color:var(--muted);padding:28px}.footer{text-align:center;color:#9aa4b7;font-size:11px;padding:10px}.toast{position:fixed;right:25px;bottom:25px;background:#20283b;color:white;padding:14px 18px;border-radius:11px;box-shadow:0 10px 35px #11182733;z-index:20;display:none;max-width:90vw}.hidden{display:none!important}@media(max-width:1100px){.layout{grid-template-columns:210px minmax(0,1fr)}.content{padding:25px 22px}.topbar{padding:0 22px}.stats{grid-template-columns:repeat(2,minmax(0,1fr))}.columns{grid-template-columns:1fr}}@media(max-width:720px){.layout{display:block}aside{padding:14px;gap:15px}.brand{padding:0 5px}.navlabel,.sidefoot{display:none}.nav{display:flex;overflow:auto}.nav button{white-space:nowrap;width:auto;padding:10px}.nav button span{width:auto}.topbar{height:58px;padding:0 15px}.today{display:none}.content{padding:20px 13px}.heading{align-items:flex-start;flex-direction:column}.stats{gap:10px}.stat{padding:14px}.value{font-size:25px}.fieldgrid{grid-template-columns:1fr}.panelhead,.panelbody,.right{padding:16px}.toolbar{padding:12px}.toolbar select{max-width:none;flex:1}.heading h1{font-size:25px}}
</style></head><body><div class="layout">
<aside><div class="brand"><div class="logo">✓</div><div><strong>TaskFlow</strong><small>Productivity suite</small></div></div><div class="navlabel">WORKSPACE</div><nav class="nav"><button class="active" onclick="showPage('dashboard',this)"><span>▦</span> Overview</button><button onclick="showPage('tasks',this)"><span>☷</span> Task manager</button><button onclick="showPage('lab',this)"><span>⌘</span> DSA lab</button><button onclick="showPage('performance',this)"><span>↗</span> Performance</button></nav><div class="navlabel">PROJECT STATUS</div><div class="sidefoot"><b><i class="dot"></i>System operational</b>Tasks are saved in a local SQLite database. Your changes persist between visits.</div></aside>
<div class="main"><header class="topbar"><div class="crumb">Workspace&nbsp; / &nbsp;<b id="crumb">Overview</b></div><div class="topright"><div class="today" id="today"></div><div class="avatar">TF</div></div></header><main class="content">
<section id="dashboard"><div class="heading"><div><div class="eyebrow">YOUR WORKSPACE</div><h1>Good to see you.</h1><p class="sub">Here's what's happening with your tasks today.</p></div><button class="btn primary" onclick="goAdd()">＋ Create new task</button></div>
<div class="stats"><div class="stat"><div class="stathead">Total tasks <span class="staticon ib">▤</span></div><div class="value" id="total">0</div><div class="statfoot">All task records</div></div><div class="stat"><div class="stathead">Pending <span class="staticon ia">◷</span></div><div class="value" id="pending">0</div><div class="statfoot">Tasks awaiting completion</div></div><div class="stat"><div class="stathead">Completed <span class="staticon ig">✓</span></div><div class="value" id="completed">0</div><div class="statfoot"><strong id="rate">0%</strong> completion rate</div></div><div class="stat"><div class="stathead">Overdue <span class="staticon ir">!</span></div><div class="value" id="overdue">0</div><div class="statfoot">Pending past deadline</div></div></div>
<div class="columns"><div><section class="panel"><div class="panelhead"><div><h2>Recent tasks</h2><p>Your latest tasks and current status</p></div><button class="btn light" onclick="showPage('tasks',document.querySelectorAll('.nav button')[1])">View all ↗</button></div><div class="tablewrap"><table><thead><tr><th>Task</th><th>Priority</th><th>Due date</th><th>Status</th></tr></thead><tbody id="recentTable"></tbody></table></div></section><section class="panel"><div class="panelhead"><div><h2>Priority distribution</h2><p>Where your attention is needed</p></div></div><div class="panelbody" id="distribution"></div></section></div>
<div><section class="panel right"><h2>Priority queue</h2><p class="desc">Next tasks ranked by priority and deadline.</p><div id="queue" class="queue"></div><button class="btn light" style="width:100%;margin-top:14px" onclick="loadTasks()">Refresh queue ↻</button></section><section class="panel right"><h2>Quick actions</h2><p class="desc">Jump straight into your workflow.</p><div class="quick"><button onclick="goAdd()"><span>＋ Add a new task</span><span>→</span></button><button onclick="showPage('lab',document.querySelectorAll('.nav button')[2])"><span>⌘ Run search algorithm</span><span>→</span></button><button onclick="showPage('performance',document.querySelectorAll('.nav button')[3])"><span>↗ Compare algorithms</span><span>→</span></button></div><div class="progress-title"><span>Overall completion</span><span id="progressText">0%</span></div><div class="track"><div class="fill" id="progressFill" style="width:0%"></div></div></section></div></div></section>
<section id="tasks" class="hidden"><div class="heading"><div><div class="eyebrow">TASK ORGANIZATION</div><h1>Task manager</h1><p class="sub">Create, prioritize, update, and track your work.</p></div></div><section class="panel"><div class="panelhead"><div><h2 id="formTitle">Create a task</h2><p>Add task details and set a deadline.</p></div></div><div class="panelbody"><form id="taskForm"><div class="fieldgrid"><label class="field">Task ID<input id="taskId" placeholder="e.g. T126" required maxlength="20"></label><label class="field">Description<input id="description" placeholder="What needs to get done?" required maxlength="300"></label><label class="field">Priority<select id="priority"><option>High</option><option selected>Medium</option><option>Low</option></select></label><label class="field">Deadline<input id="deadline" type="date" required></label></div><div class="formactions"><button class="btn primary" id="saveButton" type="submit">＋ Add task</button><button class="btn light hidden" id="cancelButton" type="button" onclick="resetForm()">Cancel</button></div><div id="message" class="sub" style="margin-top:10px"></div></form></div></section><section class="panel"><div class="panelhead"><div><h2>All tasks</h2><p>Search, filter, and manage your tasks.</p></div><button class="btn light" onclick="loadTasks()">↻ Refresh</button></div><div class="toolbar"><input id="searchBox" placeholder="⌕  Search by task or ID"><select id="statusFilter"><option value="All">All statuses</option><option>Pending</option><option>Completed</option></select><select id="sortField"><option value="priority">Priority order</option><option value="deadline">Deadline</option><option value="id">Task ID</option></select></div><div class="tablewrap"><table><thead><tr><th>Task ID</th><th>Description</th><th>Priority</th><th>Deadline</th><th>Status</th><th>Actions</th></tr></thead><tbody id="taskTable"></tbody></table></div></section></section>
<section id="lab" class="hidden"><div class="heading"><div><div class="eyebrow">DATA STRUCTURES & ALGORITHMS</div><h1>DSA lab</h1><p class="sub">Run searching and sorting algorithms on your task data.</p></div></div><section class="panel"><div class="panelhead"><div><h2>Search algorithms</h2><p>Find a task by ID and compare search steps.</p></div></div><div class="panelbody"><div class="labbar"><input id="searchId" placeholder="Task ID, e.g. T101"><button class="btn primary" onclick="runSearch('linear')">Linear search</button><button class="btn light" onclick="runSearch('binary')">Binary search</button></div><div id="searchResult" class="result">Search output will appear here.</div></div></section><section class="panel"><div class="panelhead"><div><h2>Sorting algorithms</h2><p>Sort tasks by priority or deadline.</p></div></div><div class="panelbody"><div class="labbar"><select id="sortAlgorithm"><option value="insertion">Insertion sort</option><option value="merge">Merge sort</option></select><select id="algorithmField"><option value="priority">Priority</option><option value="deadline">Deadline</option></select><button class="btn primary" onclick="runSort()">Run sort</button></div><div id="sortResult" class="result">Sorted tasks will appear here.</div></div></section><section class="panel"><div class="panelhead"><div><h2>Priority queue</h2><p>Highest priority first; deadline breaks ties.</p></div><button class="btn primary" onclick="showQueueLab()">Build queue</button></div><div class="panelbody"><div id="queueLabResult" class="result">Click Build queue to view pending tasks in priority order.</div></div></section></section>
<section id="performance" class="hidden"><div class="heading"><div><div class="eyebrow">ALGORITHM ANALYSIS</div><h1>Performance insights</h1><p class="sub">Compare operation counts and observed execution times.</p></div><button class="btn primary" onclick="performanceReport()">↻ Run benchmark</button></div><section class="panel"><div class="panelhead"><div><h2>Sorting benchmark</h2><p>Measured on your current task records.</p></div></div><div class="tablewrap"><table><thead><tr><th>Sort field</th><th>Algorithm</th><th>Comparisons</th><th>Observed time</th><th>Worst-case complexity</th></tr></thead><tbody id="performanceTable"><tr><td colspan="5" class="empty">Click Run benchmark.</td></tr></tbody></table></div></section><section class="panel"><div class="panelhead"><div><h2>Complexity reference</h2><p>Useful for your project review and viva.</p></div></div><div class="tablewrap"><table><thead><tr><th>Algorithm</th><th>Use</th><th>Worst-case time</th><th>Extra space</th></tr></thead><tbody><tr><td>Linear search</td><td>Unsorted records</td><td>O(n)</td><td>O(1)</td></tr><tr><td>Binary search</td><td>Sorted IDs</td><td>O(log n)</td><td>O(1) search</td></tr><tr><td>Insertion sort</td><td>Small or nearly sorted lists</td><td>O(n²)</td><td>O(1)</td></tr><tr><td>Merge sort</td><td>Larger lists</td><td>O(n log n)</td><td>O(n)</td></tr><tr><td>Priority queue</td><td>Repeated priority selection</td><td>O(log n) per heap removal</td><td>O(n)</td></tr></tbody></table></div><div class="panelbody"><p class="sub">Observed time depends on the computer and dataset size. The comparison count is useful for comparing algorithms consistently.</p></div></section></section><div class="footer">TaskFlow · Task Priority Management System · DSA Micro Project</div>
</main></div></div><div class="toast" id="toast"></div>
<script>
let tasks=[],editingId=null,timer;const $=id=>document.getElementById(id);$('today').textContent=new Date().toLocaleDateString(undefined,{weekday:'short',month:'short',day:'numeric',year:'numeric'});
async function api(url,opts={}){const r=await fetch(url,{headers:{'Content-Type':'application/json'},...opts});const d=await r.json();if(!r.ok)throw Error(d.error||'Request failed');return d}
function esc(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function notify(msg){$('toast').textContent=msg;$('toast').style.display='block';clearTimeout(timer);timer=setTimeout(()=>$('toast').style.display='none',2800)}
function showPage(id,btn){['dashboard','tasks','lab','performance'].forEach(s=>$(s).classList.toggle('hidden',s!==id));document.querySelectorAll('.nav button').forEach(b=>b.classList.remove('active'));if(btn)btn.classList.add('active');$('crumb').textContent=({dashboard:'Overview',tasks:'Task manager',lab:'DSA lab',performance:'Performance'})[id];if(id==='performance')performanceReport();if(id==='dashboard')loadTasks()}
function goAdd(){showPage('tasks',document.querySelectorAll('.nav button')[1]);resetForm();setTimeout(()=>$('taskId').focus(),80)}
async function loadTasks(){try{let d=await api('/api/tasks');tasks=d.tasks;for(let k of ['total','pending','completed','overdue'])$(k).textContent=d.stats[k];let rate=d.stats.total?Math.round(d.stats.completed/d.stats.total*100):0;$('rate').textContent=rate+'%';$('progressText').textContent=rate+'%';$('progressFill').style.width=rate+'%';renderTasks();renderRecent();renderDistribution();renderQueue()}catch(e){notify(e.message)}}
function renderTasks(){let q=$('searchBox').value.toLowerCase(),status=$('statusFilter').value,field=$('sortField').value;let list=tasks.filter(t=>(t.task_id.toLowerCase().includes(q)||t.description.toLowerCase().includes(q))&&(status==='All'||t.status===status));list.sort((a,b)=>{if(field==='deadline')return a.deadline.localeCompare(b.deadline);if(field==='id')return a.task_id.localeCompare(b.task_id);return ({High:3,Medium:2,Low:1}[b.priority]-{High:3,Medium:2,Low:1}[a.priority])||a.deadline.localeCompare(b.deadline)});$('taskTable').innerHTML=list.map(t=>`<tr><td class="tid">${esc(t.task_id)}</td><td class="tdesc">${esc(t.description)}</td><td><span class="badge ${t.priority}">${t.priority}</span></td><td>${esc(t.deadline)}</td><td><span class="badge ${t.status}">${t.status}</span></td><td><div class="actions">${t.status==='Pending'?`<button class="mini" onclick="completeTask('${esc(t.task_id)}')">✓ Done</button>`:''}<button class="mini" onclick="editTask('${esc(t.task_id)}')">Edit</button><button class="mini" onclick="deleteTask('${esc(t.task_id)}')">Delete</button></div></td></tr>`).join('')||'<tr><td colspan="6" class="empty">No tasks match your search.</td></tr>'}
function renderRecent(){let list=[...tasks].sort((a,b)=>b.task_id.localeCompare(a.task_id)).slice(0,6);$('recentTable').innerHTML=list.map(t=>`<tr><td><div class="tid">${esc(t.task_id)}</div><div class="tdesc" style="margin-top:5px">${esc(t.description)}</div></td><td><span class="badge ${t.priority}">${t.priority}</span></td><td>${esc(t.deadline)}</td><td><span class="badge ${t.status}">${t.status}</span></td></tr>`).join('')||'<tr><td colspan="4" class="empty">No tasks yet.</td></tr>'}
function renderDistribution(){let c={High:0,Medium:0,Low:0};tasks.filter(t=>t.status==='Pending').forEach(t=>c[t.priority]++);let max=Math.max(1,...Object.values(c));$('distribution').innerHTML=Object.entries(c).map(([p,n])=>`<div class="progress-title"><span><span class="badge ${p}">${p}</span></span><span>${n} tasks</span></div><div class="track"><div class="fill" style="width:${n/max*100}%;background:${p==='High'?'#e05260':p==='Medium'?'#d99018':'#159a70'}"></div></div>`).join('')}
function renderQueue(){let list=tasks.filter(t=>t.status==='Pending').sort((a,b)=>({High:3,Medium:2,Low:1}[b.priority]-{High:3,Medium:2,Low:1}[a.priority])||a.deadline.localeCompare(b.deadline)).slice(0,5);$('queue').innerHTML=list.map((t,i)=>`<div class="qitem"><div class="qnum">${String(i+1).padStart(2,'0')}</div><div><div class="qtitle">${esc(t.description)}</div><div class="qmeta"><span class="badge ${t.priority}">${t.priority}</span> ${esc(t.task_id)} · Due ${esc(t.deadline)}</div></div></div>`).join('')||'<div class="empty">No pending tasks.</div>'}
$('taskForm').addEventListener('submit',async e=>{e.preventDefault();let data={task_id:$('taskId').value.trim().toUpperCase(),description:$('description').value.trim(),priority:$('priority').value,deadline:$('deadline').value};try{if(editingId){await api('/api/tasks/'+encodeURIComponent(editingId),{method:'PUT',body:JSON.stringify(data)});notify('Task updated successfully')}else{await api('/api/tasks',{method:'POST',body:JSON.stringify(data)});notify('Task created successfully')}resetForm();await loadTasks()}catch(err){$('message').textContent=err.message;$('message').style.color='#df5362'}});
function editTask(id){let t=tasks.find(x=>x.task_id===id);if(!t)return;showPage('tasks',document.querySelectorAll('.nav button')[1]);editingId=id;$('taskId').value=id;$('taskId').disabled=true;$('description').value=t.description;$('priority').value=t.priority;$('deadline').value=t.deadline;$('formTitle').textContent='Edit task · '+id;$('saveButton').textContent='Save changes';$('cancelButton').classList.remove('hidden');window.scrollTo({top:0,behavior:'smooth'})}
function resetForm(){editingId=null;$('taskForm').reset();$('taskId').disabled=false;$('formTitle').textContent='Create a task';$('saveButton').textContent='＋ Add task';$('cancelButton').classList.add('hidden');$('message').textContent=''}
async function completeTask(id){try{await api('/api/tasks/'+encodeURIComponent(id)+'/complete',{method:'PATCH'});notify('Task marked complete');loadTasks()}catch(e){notify(e.message)}}
async function deleteTask(id){if(!confirm('Delete task '+id+'?'))return;try{await api('/api/tasks/'+encodeURIComponent(id),{method:'DELETE'});notify('Task deleted');loadTasks()}catch(e){notify(e.message)}}
async function runSearch(algorithm){let id=$('searchId').value.trim();if(!id){$('searchResult').textContent='Enter a task ID first.';return}try{let d=await api('/api/search?algorithm='+algorithm+'&task_id='+encodeURIComponent(id));$('searchResult').innerHTML=`<h3>${algorithm==='linear'?'Linear search':'Binary search'}</h3><p>${esc(d.message)}</p><p><b>Comparisons:</b> ${d.comparisons} &nbsp; <b>Observed time:</b> ${d.time_ms} ms</p>`+(d.task?`<p><b>${esc(d.task.task_id)}</b> — ${esc(d.task.description)} · ${d.task.priority} · ${esc(d.task.deadline)}</p>`:'')}catch(e){$('searchResult').textContent=e.message}}
async function runSort(){try{let d=await api('/api/sort?algorithm='+$('sortAlgorithm').value+'&field='+$('algorithmField').value);$('sortResult').innerHTML=`<h3>${esc(d.algorithm)} sort by ${esc(d.field)}</h3><p><b>Comparisons:</b> ${d.comparisons} &nbsp; <b>Observed time:</b> ${d.time_ms} ms</p>`+d.tasks.map((t,i)=>`${i+1}. ${esc(t.task_id)} — ${esc(t.description)} — ${t.priority} — ${esc(t.deadline)}`).join('<br>')}catch(e){$('sortResult').textContent=e.message}}
async function showQueueLab(){try{let d=await api('/api/priority-queue');$('queueLabResult').innerHTML='<h3>Priority queue output</h3>'+d.tasks.map((t,i)=>`${i+1}. ${esc(t.task_id)} — ${esc(t.description)} — ${t.priority} — ${esc(t.deadline)}`).join('<br>')||'No pending tasks'}catch(e){$('queueLabResult').textContent=e.message}}
async function performanceReport(){try{let d=await api('/api/performance');$('performanceTable').innerHTML=d.results.map(r=>`<tr><td>${esc(r.field)}</td><td><b>${esc(r.algorithm)}</b></td><td>${r.comparisons}</td><td>${r.time_ms} ms</td><td>${r.algorithm==='Merge Sort'?'O(n log n)':'O(n²)'}</td></tr>`).join('')}catch(e){notify(e.message)}}
$('searchBox').addEventListener('input',renderTasks);$('statusFilter').addEventListener('change',renderTasks);$('sortField').addEventListener('change',renderTasks);loadTasks();
</script></body></html>'''


@app.route('/')
def home():
    return render_template_string(PAGE)


@app.route('/api/tasks', methods=['GET'])
def api_tasks():
    tasks = get_tasks()
    today = date.today().isoformat()
    completed = sum(t['status'] == 'Completed' for t in tasks)
    return jsonify(tasks=tasks, stats={
        'total': len(tasks), 'pending': len(tasks)-completed, 'completed': completed,
        'overdue': sum(t['deadline'] < today and t['status'] == 'Pending' for t in tasks)})


@app.route('/api/tasks', methods=['POST'])
def api_add_task():
    data = request.get_json(silent=True) or {}
    task_id = str(data.get('task_id', '')).strip().upper()
    description = str(data.get('description', '')).strip()
    priority = data.get('priority')
    deadline = str(data.get('deadline', '')).strip()
    if not task_id or not description or not deadline:
        return jsonify(error='Please fill in every field.'), 400
    if priority not in RANK:
        return jsonify(error='Choose a valid priority.'), 400
    try: date.fromisoformat(deadline)
    except ValueError: return jsonify(error='Choose a valid deadline.'), 400
    try:
        with db_connect() as conn:
            conn.execute('INSERT INTO tasks VALUES (?, ?, ?, ?, ?)', (task_id, description, priority, deadline, 'Pending'))
    except sqlite3.IntegrityError:
        return jsonify(error='That task ID already exists. Choose a different ID.'), 409
    return jsonify(message='Task created.'), 201


@app.route('/api/tasks/<task_id>', methods=['PUT'])
def api_update_task(task_id):
    data = request.get_json(silent=True) or {}
    description, priority, deadline = str(data.get('description', '')).strip(), data.get('priority'), str(data.get('deadline', '')).strip()
    if not description or priority not in RANK: return jsonify(error='Enter a description and valid priority.'), 400
    try: date.fromisoformat(deadline)
    except ValueError: return jsonify(error='Choose a valid deadline.'), 400
    with db_connect() as conn:
        cur = conn.execute('UPDATE tasks SET description=?, priority=?, deadline=? WHERE task_id=?', (description, priority, deadline, task_id.upper()))
        if not cur.rowcount: return jsonify(error='Task not found.'), 404
    return jsonify(message='Task updated.')


@app.route('/api/tasks/<task_id>/complete', methods=['PATCH'])
def api_complete_task(task_id):
    with db_connect() as conn:
        cur = conn.execute("UPDATE tasks SET status='Completed' WHERE task_id=?", (task_id.upper(),))
        if not cur.rowcount: return jsonify(error='Task not found.'), 404
    return jsonify(message='Task completed.')


@app.route('/api/tasks/<task_id>', methods=['DELETE'])
def api_delete_task(task_id):
    with db_connect() as conn:
        cur = conn.execute('DELETE FROM tasks WHERE task_id=?', (task_id.upper(),))
        if not cur.rowcount: return jsonify(error='Task not found.'), 404
    return jsonify(message='Task deleted.')


@app.route('/api/priority-queue')
def api_priority_queue():
    tasks = [t for t in get_tasks() if t['status'] == 'Pending']
    ordered, _ = merge_sort(tasks, lambda t: sort_key(t, 'priority'))
    return jsonify(tasks=ordered)


@app.route('/api/search')
def api_search():
    task_id = request.args.get('task_id', '').strip().upper()
    algorithm = request.args.get('algorithm', 'linear')
    tasks = get_tasks()
    comparisons, found = 0, None
    start = time.perf_counter()
    if algorithm == 'linear':
        for task in tasks:
            comparisons += 1
            if task['task_id'] == task_id:
                found = task; break
    elif algorithm == 'binary':
        ordered = sorted(tasks, key=lambda t: t['task_id'])
        low, high = 0, len(ordered)-1
        while low <= high:
            mid = (low+high)//2; comparisons += 1
            if ordered[mid]['task_id'] == task_id: found = ordered[mid]; break
            if ordered[mid]['task_id'] < task_id: low = mid+1
            else: high = mid-1
    else: return jsonify(error='Invalid search algorithm.'), 400
    elapsed = (time.perf_counter()-start)*1000
    return jsonify(task=found, message='Task found.' if found else 'Task not found.', comparisons=comparisons, time_ms=round(elapsed, 6))


@app.route('/api/sort')
def api_sort():
    algorithm, field = request.args.get('algorithm', 'merge'), request.args.get('field', 'priority')
    if field not in ('priority', 'deadline'): return jsonify(error='Invalid sort field.'), 400
    key = lambda t: sort_key(t, field)
    start = time.perf_counter()
    if algorithm == 'insertion': result, comparisons = insertion_sort(get_tasks(), key)
    elif algorithm == 'merge': result, comparisons = merge_sort(get_tasks(), key)
    else: return jsonify(error='Invalid sorting algorithm.'), 400
    return jsonify(tasks=result, algorithm=algorithm.title(), field=field, comparisons=comparisons, time_ms=round((time.perf_counter()-start)*1000, 6))


@app.route('/api/performance')
def api_performance():
    tasks, reports = get_tasks(), []
    for field in ('priority', 'deadline'):
        key = lambda t, f=field: sort_key(t, f)
        for name, sorter in [('Insertion Sort', insertion_sort), ('Merge Sort', merge_sort)]:
            start = time.perf_counter(); _, comparisons = sorter(tasks, key)
            reports.append({'field': field, 'algorithm': name, 'comparisons': comparisons, 'time_ms': round((time.perf_counter()-start)*1000, 6)})
    return jsonify(task_count=len(tasks), results=reports)


initialize_db()

if __name__ == '__main__':
    app.run(debug=True)
