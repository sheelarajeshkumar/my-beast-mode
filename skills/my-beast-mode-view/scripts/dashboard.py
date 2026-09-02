#!/usr/bin/env python3
"""Build a private, dependency-free RTK savings dashboard."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
from pathlib import Path
import re
import shlex
import sqlite3
import subprocess
import tempfile
import webbrowser


def database_candidates(explicit: str | None) -> list[Path]:
    candidates = [explicit, os.environ.get("RTK_DB_PATH")]
    home = Path.home()
    candidates += [
        home / "Library/Application Support/rtk/history.db",
        home / ".local/share/rtk/history.db",
    ]
    for key in ("LOCALAPPDATA", "APPDATA"):
        if os.environ.get(key):
            candidates.append(Path(os.environ[key]) / "rtk/history.db")
    return [Path(item).expanduser() for item in candidates if item]


def find_database(explicit: str | None) -> Path:
    candidates = database_candidates(explicit)
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    attempted = "\n".join(f"  - {path}" for path in candidates)
    raise FileNotFoundError(f"RTK history database not found. Tried:\n{attempted}")


def command_family(command: str) -> str:
    try:
        parts = shlex.split(command)
    except ValueError:
        parts = command.split()
    if parts and Path(parts[0]).name == "rtk":
        parts = parts[1:]
    return Path(parts[0]).name if parts else "other"


class ProjectNamer:
    def __init__(self, aliases: dict[str, str] | None = None, privacy: bool = False):
        self.aliases = aliases or {}
        self.privacy = privacy
        self.private_names: dict[str, str] = {}

    def __call__(self, path: str) -> str:
        if not path:
            return "Unknown project"
        if path in self.aliases:
            return self.aliases[path]
        if self.privacy:
            if path not in self.private_names:
                self.private_names[path] = f"Project {len(self.private_names) + 1:02d}"
            return self.private_names[path]
        home = str(Path.home())
        return "~" + path[len(home) :] if path == home or path.startswith(home + os.sep) else path


def load_aliases(path: str | None) -> dict[str, str]:
    if not path:
        return {}
    value = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not all(isinstance(key, str) and isinstance(label, str) for key, label in value.items()):
        raise ValueError("aliases must be a JSON object of path-to-label strings")
    return {key: " ".join(label.split())[:80] for key, label in value.items()}


def memory_path(explicit: str | None) -> Path:
    return Path(explicit or os.environ.get("MY_BEAST_MODE_MEMORY", "~/.my-beast-mode/memory.jsonl")).expanduser()


def safe_int(value: object) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def read_memories(path: Path, namer: ProjectNamer, privacy: bool = False) -> tuple[list[list[object]], int]:
    if not path.is_file():
        return [], 0
    starts: dict[str, dict[str, object]] = {}
    finishes: dict[str, dict[str, object]] = {}
    invalid = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
            session = event["session"]
            if event.get("event") == "start":
                starts[session] = event
            elif event.get("event") == "finish":
                finishes[session] = event
        except (json.JSONDecodeError, KeyError, TypeError):
            invalid += 1
            continue
    sessions = []
    for session, start in starts.items():
        finish = finishes.get(session, {})
        started, ended = str(start.get("timestamp", "")), str(finish.get("timestamp", ""))
        duration = 0
        if ended:
            try:
                duration = max(0, int((dt.datetime.fromisoformat(ended) - dt.datetime.fromisoformat(started)).total_seconds()))
            except (TypeError, ValueError):
                pass
        sessions.append([
            started,
            ended,
            namer(str(start.get("project", ""))),
            start.get("task_type", "other"),
            start.get("orchestrator", "host"),
            start.get("agent", "unknown"),
            finish.get("outcome", "incomplete"),
            "" if privacy else finish.get("summary", start.get("summary", "")),
            safe_int(finish.get("files_changed", 0)),
            safe_int(finish.get("checks_passed", 0)),
            safe_int(finish.get("checks_failed", 0)),
            duration,
            start.get("skill_version", "legacy"),
        ])
    return sorted(sessions, key=lambda row: row[0], reverse=True), invalid


def read_records(db_path: Path, namer: ProjectNamer) -> list[list[object]]:
    uri = f"file:{db_path.as_posix()}?mode=ro&immutable=1"
    with sqlite3.connect(uri, uri=True) as db:
        columns = {row[1] for row in db.execute("PRAGMA table_info(commands)")}
        required = {"timestamp", "project_path", "rtk_cmd", "input_tokens", "output_tokens", "saved_tokens"}
        if not required <= columns:
            missing = ", ".join(sorted(required - columns))
            raise RuntimeError(f"Unsupported RTK history schema; missing: {missing}")
        elapsed = "COALESCE(exec_time_ms, 0)" if "exec_time_ms" in columns else "0"
        rows = db.execute(
            f"SELECT timestamp, project_path, rtk_cmd, input_tokens, output_tokens, saved_tokens, {elapsed} "
            "FROM commands ORDER BY timestamp"
        )
        return [
            [timestamp, namer(project), command_family(command), raw, optimized, saved, elapsed_ms]
            for timestamp, project, command, raw, optimized, saved, elapsed_ms in rows
        ]


def safe_tool(value: object) -> str:
    parts = re.findall(r"[A-Za-z0-9_.+-]+", str(value))[:2]
    return " ".join(parts) or "other"


def discover(days: int) -> dict[str, object]:
    try:
        result = subprocess.run(
            ["rtk", "discover", "--all", "--since", str(days), "--format", "json", "--limit", "20"],
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )
        raw = json.loads(result.stdout)
        opportunities = [[
            safe_tool(item.get("rtk_equivalent")),
            safe_tool(item.get("category")),
            safe_int(item.get("count")),
            safe_int(item.get("estimated_savings_tokens")),
            round(float(item.get("estimated_savings_pct", 0)), 1),
        ] for item in raw.get("supported", []) if isinstance(item, dict)]
        opportunities.sort(key=lambda item: item[3], reverse=True)
        total, adopted = safe_int(raw.get("total_commands")), safe_int(raw.get("already_rtk"))
        return {
            "available": True,
            "days": days,
            "sessions": safe_int(raw.get("sessions_scanned")),
            "total_commands": total,
            "already_rtk": adopted,
            "coverage_pct": round(100 * adopted / total, 1) if total else 0,
            "missed_commands": sum(item[2] for item in opportunities),
            "potential_saved": sum(item[3] for item in opportunities),
            "opportunities": opportunities[:12],
        }
    except (FileNotFoundError, subprocess.SubprocessError, json.JSONDecodeError, TypeError, ValueError):
        return {"available": False, "days": days, "opportunities": []}


def data_health(db_path: Path, records: list[list[object]], memory_invalid: int, coverage: dict[str, object]) -> dict[str, object]:
    parse_failures = 0
    with sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro&immutable=1", uri=True) as db:
        if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='parse_failures'").fetchone():
            parse_failures = safe_int(db.execute("SELECT COUNT(*) FROM parse_failures").fetchone()[0])
    try:
        version = subprocess.run(["rtk", "--version"], capture_output=True, text=True, timeout=3, check=True).stdout.strip()[:40]
    except (FileNotFoundError, subprocess.SubprocessError):
        version = "unavailable"
    return {
        "rtk_version": version,
        "records": len(records),
        "first_record": records[0][0] if records else "",
        "last_record": records[-1][0] if records else "",
        "parse_failures": parse_failures,
        "invalid_memory_lines": memory_invalid,
        "discover_available": bool(coverage.get("available")),
        "retention_days": 90,
    }


def safe_json(value: object) -> str:
    return json.dumps(value, separators=(",", ":")).replace("</", "<\\/")


def render(
    records: list[list[object]],
    db_path: Path,
    memories: list[list[object]],
    memory: Path,
    coverage: dict[str, object],
    health: dict[str, object],
    privacy: bool,
) -> str:
    generated = dt.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")
    source = "hidden (privacy mode)" if privacy else ProjectNamer()(str(db_path))
    data = safe_json(records)
    memory_data = safe_json(memories)
    memory_source = "hidden (privacy mode)" if privacy else ProjectNamer()(str(memory))
    coverage_data = safe_json(coverage)
    health_data = safe_json(health)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>My Beast Mode · RTK Savings</title>
<style>
:root{{--bg:#090d18;--panel:#111827;--soft:#1c2638;--text:#edf4ff;--muted:#98a9c3;--green:#62f5b5;--cyan:#5dd7ff;--purple:#a78bfa;--line:#26344d}}
*{{box-sizing:border-box}} body{{margin:0;background:radial-gradient(circle at 80% 0,#17213d 0,transparent 35%),var(--bg);color:var(--text);font:15px/1.5 system-ui,sans-serif}}
main{{max-width:1400px;margin:auto;padding:32px 20px 64px}} header{{display:flex;justify-content:space-between;gap:20px;align-items:end;flex-wrap:wrap}} h1{{font-size:clamp(28px,5vw,48px);line-height:1;margin:0}} h2{{font-size:18px;margin:0 0 18px}} .eyebrow,.meta,small{{color:var(--muted)}} .eyebrow{{text-transform:uppercase;letter-spacing:.14em;font-weight:700}} .filters{{display:flex;gap:6px;background:var(--panel);border:1px solid var(--line);padding:5px;border-radius:12px;flex-wrap:wrap}} button{{color:var(--muted);background:transparent;border:0;padding:8px 12px;border-radius:8px;cursor:pointer;font:inherit}} button.active,button:hover{{background:var(--soft);color:var(--text)}} .action{{color:var(--cyan);border-left:1px solid var(--line);border-radius:0}} .kpis,.memory-kpis,.health-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:26px 0}} .memory-kpis{{margin:0 0 18px}} .health-grid{{grid-template-columns:repeat(2,1fr);margin:0}} .card,.panel{{background:color-mix(in srgb,var(--panel) 92%,transparent);border:1px solid var(--line);border-radius:16px}} .card{{padding:20px}} .memory-kpis .card,.mini{{background:var(--soft);padding:14px;border-radius:12px}} .value{{font-size:clamp(24px,4vw,36px);font-weight:750;margin-top:5px}} .memory-kpis .value{{font-size:24px}} .saved,.success,.good{{color:var(--green)}} .failed,.warning{{color:#fb7185}} .grid{{display:grid;grid-template-columns:1.4fr 1fr;gap:14px}} .panel{{padding:20px;min-width:0}} .signals{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:14px}} .signal{{padding:12px 14px;background:var(--panel);border:1px solid var(--line);border-radius:12px}} #trend{{width:100%;height:230px;display:block}} .axis{{stroke:#33415d;stroke-width:1}} .trend{{fill:none;stroke:var(--green);stroke-width:3;stroke-linejoin:round}} .area{{fill:url(#fade)}} .bars{{display:grid;gap:12px}} .bar-head{{display:flex;justify-content:space-between;gap:12px}} .bar-track{{height:8px;background:var(--soft);border-radius:10px;overflow:hidden}} .bar-fill{{height:100%;background:linear-gradient(90deg,var(--cyan),var(--purple));border-radius:inherit}} .table-panel{{margin-top:14px;overflow:hidden}} .scroll{{overflow:auto}} table{{border-collapse:collapse;width:100%;min-width:1100px}} th,td{{padding:12px 14px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap}} th{{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.07em}} th:first-child,td:first-child,th:last-child,td:last-child{{text-align:left}} #rows tr{{cursor:pointer}} tbody tr:hover,tbody tr.selected{{background:var(--soft)}} .project,.summary{{max-width:330px;overflow:hidden;text-overflow:ellipsis}} .pill{{display:inline-block;background:#1b3041;color:var(--cyan);padding:2px 7px;border-radius:99px;margin:2px;font-size:12px}} .empty{{padding:50px;text-align:center;color:var(--muted)}} footer{{margin-top:16px;color:var(--muted);font-size:12px;overflow-wrap:anywhere}} @media(max-width:800px){{.kpis,.memory-kpis{{grid-template-columns:repeat(2,1fr)}}.grid{{grid-template-columns:1fr}}.signals{{grid-template-columns:1fr 1fr}}}} @media(max-width:460px){{.kpis,.memory-kpis,.health-grid,.signals{{grid-template-columns:1fr}}}}
</style></head><body><main>
<header><div><div class="eyebrow">Local RTK analytics</div><h1>My Beast Mode</h1><div class="meta">Token optimization by project · updated {html.escape(generated)}</div></div>
<div class="filters" aria-label="Dashboard controls"><button data-days="7">7d</button><button data-days="30" class="active">30d</button><button data-days="90">90d</button><button data-days="0">All</button><button id="share-png" class="action">Share PNG</button><button id="share-json" class="action">Share JSON</button></div></header>
<section class="kpis"><div class="card"><small>Tokens saved</small><div id="saved" class="value saved">—</div></div><div class="card"><small>Compression</small><div id="rate" class="value">—</div></div><div class="card"><small>Raw output</small><div id="raw" class="value">—</div></div><div class="card"><small>Optimized output</small><div id="optimized" class="value">—</div></div><div class="card"><small>Commands optimized</small><div id="commands" class="value">—</div></div><div class="card"><small>Active projects</small><div id="projects" class="value">—</div></div><div class="card"><small>Average saved / command</small><div id="average" class="value">—</div></div><div class="card"><small>Active days</small><div id="active-days" class="value">—</div></div></section>
<section id="signals" class="signals" aria-label="Trend and health signals"></section>
<section class="grid"><div class="panel"><h2>Daily tokens saved</h2><svg id="trend" role="img" aria-label="Daily saved-token trend"></svg></div><div class="panel"><h2 id="detail-title">How RTK optimized output</h2><div id="categories" class="bars"></div></div></section>
<section class="panel table-panel"><h2>Project detail</h2><div class="scroll"><table><thead><tr><th>Project</th><th>Raw</th><th>Optimized</th><th>Saved</th><th>Savings</th><th>Avg saved</th><th>Avg time</th><th>Commands</th><th>Days</th><th>Beast runs</th><th>Last active</th><th>How</th></tr></thead><tbody id="rows"></tbody></table></div><div id="empty" class="empty" hidden>No RTK activity in this period.</div></section>
<section class="grid table-panel"><div class="panel"><h2>Missed-savings coverage · {safe_int(coverage.get('days'))} days</h2><div class="memory-kpis"><div class="card"><small>RTK coverage</small><div id="coverage-rate" class="value">—</div></div><div class="card"><small>Potential savings</small><div id="potential-saved" class="value saved">—</div></div><div class="card"><small>Missed commands</small><div id="missed-commands" class="value">—</div></div><div class="card"><small>Sessions scanned</small><div id="scanned-sessions" class="value">—</div></div></div><div class="scroll"><table><thead><tr><th>Use instead</th><th>Category</th><th>Count</th><th>Potential</th><th>Estimate</th></tr></thead><tbody id="opportunity-rows"></tbody></table></div><div id="coverage-empty" class="empty" hidden>RTK discover data is unavailable.</div></div><div class="panel"><h2>Data health</h2><div id="health-grid" class="health-grid"></div></div></section>
<section class="panel table-panel"><h2>Beast Mode memory</h2><div class="memory-kpis"><div class="card"><small>Recorded runs</small><div id="memory-runs" class="value">—</div></div><div class="card"><small>Completion rate</small><div id="memory-rate" class="value">—</div></div><div class="card"><small>Average duration</small><div id="memory-duration" class="value">—</div></div><div class="card"><small>Checks passed</small><div id="memory-checks" class="value success">—</div></div></div><h2>Agent comparison</h2><div class="scroll"><table><thead><tr><th>Agent</th><th>Runs</th><th>Completion</th><th>Avg duration</th><th>Tokens saved</th><th>Compression</th><th>Checks</th></tr></thead><tbody id="agent-rows"></tbody></table></div><h2 style="margin-top:22px">Recent sessions</h2><div class="scroll"><table><thead><tr><th>Started</th><th>Project</th><th>Task</th><th>Agent</th><th>Orchestrator</th><th>Duration</th><th>Outcome</th><th>Files</th><th>Checks</th><th>Saved</th><th>Compression</th><th>Commands</th><th>Memory</th></tr></thead><tbody id="memory-rows"></tbody></table></div><div id="memory-empty" class="empty" hidden>No Beast Mode memory in this period. New uses will appear after the skill records them.</div></section>
<footer>Private local report · RTK: {html.escape(source)} · memory: {html.escape(memory_source)} · RTK estimates tokens from text size; values are optimization analytics, not API billing records.</footer>
</main><script>
const records={data};
const memories={memory_data};
const coverage={coverage_data};
const health={health_data};
const privacyMode={str(privacy).lower()};
const fmt=n=>Intl.NumberFormat(undefined,{{notation:'compact',maximumFractionDigits:1}}).format(n||0);
const esc=s=>String(s).replace(/[&<>"']/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));
let days=30,selected='',lastAggregate=null;
const dateOf=value=>String(value).slice(0,10);
const totals=rows=>rows.reduce((sum,row)=>{{sum.raw+=row[3];sum.opt+=row[4];sum.saved+=row[5];sum.ms+=row[6]||0;sum.count++;return sum}},{{raw:0,opt:0,saved:0,ms:0,count:0}});
function sessionMetric(memory){{
 const end=memory[1]||new Date().toISOString(),project=memory[2];
 // ponytail: linear interval correlation; index sessions when memory reaches thousands of runs.
 return totals(records.filter(row=>row[0]>=memory[0]&&row[0]<=end&&row[1]===project));
}}
function aggregate(){{
 const cutoff=days?new Date(Date.now()-days*864e5).toISOString().slice(0,10):'',previousCutoff=days?new Date(Date.now()-days*2*864e5).toISOString().slice(0,10):'';
 const filtered=records.filter(r=>!cutoff||dateOf(r[0])>=cutoff),previous=days?records.filter(r=>dateOf(r[0])>=previousCutoff&&dateOf(r[0])<cutoff):[],memoryFiltered=memories.filter(m=>!cutoff||dateOf(m[0])>=cutoff),projects=new Map(),daily=new Map(),allCats=new Map(),memoryByProject=new Map();
 for(const [timestamp,project,family,raw,opt,saved,elapsed] of filtered){{
  const date=dateOf(timestamp),p=projects.get(project)||{{project,raw:0,opt:0,saved:0,ms:0,count:0,cats:new Map(),dates:new Set(),last:''}};p.raw+=raw;p.opt+=opt;p.saved+=saved;p.ms+=elapsed||0;p.count++;p.dates.add(date);p.last=timestamp;p.cats.set(family,(p.cats.get(family)||0)+saved);projects.set(project,p);
  daily.set(date,(daily.get(date)||0)+saved);allCats.set(family,(allCats.get(family)||0)+saved);
 }}
 for(const memory of memoryFiltered)memoryByProject.set(memory[2],(memoryByProject.get(memory[2])||0)+1);
 return {{items:[...projects.values()].sort((a,b)=>b.saved-a.saved),daily:[...daily].sort(),cats:allCats,filtered,previous,memoryFiltered,memoryByProject,sessionRows:memoryFiltered.map(memory=>[memory,sessionMetric(memory)])}};
}}
function categoryRows(cats){{
 const items=[...cats].sort((a,b)=>b[1]-a[1]).slice(0,8),max=Math.max(1,...items.map(x=>x[1]));
 return items.length?items.map(([name,n])=>`<div><div class="bar-head"><span>${{esc(name)}}</span><strong>${{fmt(n)}} saved</strong></div><div class="bar-track"><div class="bar-fill" style="width:${{Math.max(2,n/max*100)}}%"></div></div></div>`).join(''):'<div class="empty">No command categories yet.</div>';
}}
function drawTrend(points){{
 const svg=document.querySelector('#trend'),w=700,h=230,p=18,max=Math.max(1,...points.map(x=>x[1]));
 if(!points.length){{svg.innerHTML='';return}}
 const xy=points.map(([d,n],i)=>[p+(w-p*2)*(points.length===1?.5:i/(points.length-1)),h-p-(h-p*2)*n/max]);
 const line=xy.map((v,i)=>(i?'L':'M')+v.join(',')).join(' '),area=`${{line}} L${{xy.at(-1)[0]}},${{h-p}} L${{xy[0][0]}},${{h-p}} Z`;
 svg.setAttribute('viewBox',`0 0 ${{w}} ${{h}}`);svg.innerHTML=`<defs><linearGradient id="fade" x2="0" y2="1"><stop stop-color="#62f5b5" stop-opacity=".25"/><stop offset="1" stop-color="#62f5b5" stop-opacity="0"/></linearGradient></defs><line class="axis" x1="${{p}}" y1="${{h-p}}" x2="${{w-p}}" y2="${{h-p}}"/><path class="area" d="${{area}}"/><path class="trend" d="${{line}}"/><text x="${{p}}" y="14" fill="#98a9c3">${{fmt(max)}}</text>`;
}}
function duration(seconds){{if(!seconds)return '—';if(seconds<60)return `${{seconds}}s`;if(seconds<3600)return `${{Math.round(seconds/60)}}m`;return `${{(seconds/3600).toFixed(1)}}h`}}
function signalRows(a){{
 const current=totals(a.filtered),prior=totals(a.previous),items=[];
 if(days&&prior.raw){{const nowRate=current.raw?current.saved/current.raw*100:0,priorRate=prior.saved/prior.raw*100,delta=nowRate-priorRate;items.push([delta>=-5?'good':'warning',`Compression ${{delta>=0?'+':''}}${{delta.toFixed(1)}} points vs prior ${{days}}d`]);items.push([current.raw<=prior.raw*1.2?'good':'warning',`Raw output ${{current.raw<=prior.raw*1.2?'within':'above'}} prior-period range`])}}
 const failed=a.memoryFiltered.filter(m=>m[6]==='failed').length,incomplete=a.memoryFiltered.filter(m=>m[6]==='incomplete').length;
 items.push([failed?'warning':'good',failed?`${{failed}} failed Beast Mode run${{failed===1?'':'s'}}`:'No failed Beast Mode runs']);items.push([incomplete?'warning':'good',incomplete?`${{incomplete}} incomplete session${{incomplete===1?'':'s'}}`:'All sessions closed']);
 if(coverage.available&&coverage.potential_saved)items.push(['warning',`${{fmt(coverage.potential_saved)}} potential tokens in missed RTK usage`]);
 return items.slice(0,4).map(([kind,text])=>`<div class="signal ${{kind}}">${{esc(text)}}</div>`).join('');
}}
function agentRows(a){{
 const groups=new Map();
 for(const [memory,stats] of a.sessionRows){{const key=memory[5]||'unknown',group=groups.get(key)||{{runs:0,complete:0,duration:0,saved:0,raw:0,checks:0}};group.runs++;group.complete+=memory[6]!=='incomplete';group.duration+=memory[11];group.saved+=stats.saved;group.raw+=stats.raw;group.checks+=memory[9];groups.set(key,group)}}
 return [...groups].sort((x,y)=>y[1].saved-x[1].saved).map(([agent,g])=>`<tr><td>${{esc(agent)}}</td><td>${{g.runs}}</td><td>${{(g.complete/g.runs*100).toFixed(1)}}%</td><td>${{duration(Math.round(g.duration/Math.max(1,g.complete)))}}</td><td class="saved">${{fmt(g.saved)}}</td><td>${{g.raw?(g.saved/g.raw*100).toFixed(1):0}}%</td><td>${{g.checks}}</td></tr>`).join('');
}}
function healthCards(a){{
 const incomplete=a.memoryFiltered.filter(m=>m[6]==='incomplete').length,items=[['RTK version',health.rtk_version],['Tracked records',health.records.toLocaleString()],['History window',`${{dateOf(health.first_record)||'—'}} → ${{dateOf(health.last_record)||'—'}}`],['Retention',`${{health.retention_days}} days`],['Parse failures',health.parse_failures],['Invalid memory lines',health.invalid_memory_lines],['Incomplete sessions',incomplete],['Discover',health.discover_available?'available':'unavailable'],['Privacy mode',privacyMode?'on':'off']];
 return items.map(([label,value])=>`<div class="mini"><small>${{esc(label)}}</small><div><strong>${{esc(value)}}</strong></div></div>`).join('');
}}
function render(){{
 const a=aggregate(),raw=a.items.reduce((n,p)=>n+p.raw,0),optimized=a.items.reduce((n,p)=>n+p.opt,0),saved=a.items.reduce((n,p)=>n+p.saved,0),activeDays=new Set(a.filtered.map(r=>dateOf(r[0]))).size;lastAggregate=a;
 document.querySelector('#saved').textContent=fmt(saved);document.querySelector('#rate').textContent=raw?`${{(saved/raw*100).toFixed(1)}}%`:'0%';document.querySelector('#raw').textContent=fmt(raw);document.querySelector('#optimized').textContent=fmt(optimized);document.querySelector('#commands').textContent=a.filtered.length.toLocaleString();document.querySelector('#projects').textContent=a.items.length.toLocaleString();document.querySelector('#average').textContent=fmt(a.filtered.length?saved/a.filtered.length:0);document.querySelector('#active-days').textContent=activeDays.toLocaleString();drawTrend(a.daily);
 document.querySelector('#signals').innerHTML=signalRows(a);document.querySelector('#health-grid').innerHTML=healthCards(a);
 const chosen=a.items.find(p=>p.project===selected);document.querySelector('#detail-title').textContent=chosen?`How · ${{chosen.project}}`:'How RTK optimized output';document.querySelector('#categories').innerHTML=categoryRows(chosen?chosen.cats:a.cats);
 document.querySelector('#rows').innerHTML=a.items.map(p=>{{const cats=[...p.cats].sort((x,y)=>y[1]-x[1]).slice(0,3).map(x=>`<span class="pill">${{esc(x[0])}}</span>`).join('');return `<tr data-project="${{esc(p.project)}}" class="${{p.project===selected?'selected':''}}"><td class="project" title="${{esc(p.project)}}">${{esc(p.project)}}</td><td>${{fmt(p.raw)}}</td><td>${{fmt(p.opt)}}</td><td class="saved">${{fmt(p.saved)}}</td><td>${{p.raw?(p.saved/p.raw*100).toFixed(1):0}}%</td><td>${{fmt(p.count?p.saved/p.count:0)}}</td><td>${{duration(Math.round(p.ms/Math.max(1,p.count)/1000))}}</td><td>${{p.count.toLocaleString()}}</td><td>${{p.dates.size}}</td><td>${{a.memoryByProject.get(p.project)||0}}</td><td>${{dateOf(p.last)}}</td><td>${{cats}}</td></tr>`}}).join('');document.querySelector('#empty').hidden=!!a.items.length;
 document.querySelectorAll('#rows tr').forEach(row=>row.onclick=()=>{{selected=selected===row.dataset.project?'':row.dataset.project;render()}});
 const completed=a.memoryFiltered.filter(m=>m[6]!=='incomplete'),checks=a.memoryFiltered.reduce((n,m)=>n+m[9],0),avgDuration=completed.length?completed.reduce((n,m)=>n+m[11],0)/completed.length:0;
 document.querySelector('#memory-runs').textContent=a.memoryFiltered.length.toLocaleString();document.querySelector('#memory-rate').textContent=a.memoryFiltered.length?`${{(completed.length/a.memoryFiltered.length*100).toFixed(1)}}%`:'0%';document.querySelector('#memory-duration').textContent=duration(Math.round(avgDuration));document.querySelector('#memory-checks').textContent=checks.toLocaleString();document.querySelector('#agent-rows').innerHTML=agentRows(a);
 document.querySelector('#memory-rows').innerHTML=a.sessionRows.slice(0,25).map(([m,s])=>`<tr><td>${{new Date(m[0]).toLocaleString()}}</td><td class="project" title="${{esc(m[2])}}">${{esc(m[2])}}</td><td><span class="pill">${{esc(m[3])}}</span></td><td>${{esc(m[5])}}</td><td>${{esc(m[4])}}</td><td>${{duration(m[11])}}</td><td class="${{m[6]==='success'?'success':m[6]==='failed'?'failed':''}}">${{esc(m[6])}}</td><td>${{m[8]}}</td><td>${{m[9]}} passed${{m[10]?`, ${{m[10]}} failed`:''}}</td><td class="saved">${{fmt(s.saved)}}</td><td>${{s.raw?(s.saved/s.raw*100).toFixed(1):0}}%</td><td>${{s.count}}</td><td class="summary" title="${{esc(m[7])}}">${{esc(m[7]||'Hidden in privacy mode')}}</td></tr>`).join('');document.querySelector('#memory-empty').hidden=!!a.memoryFiltered.length;
 document.querySelector('#coverage-rate').textContent=coverage.available?`${{coverage.coverage_pct}}%`:'—';document.querySelector('#potential-saved').textContent=coverage.available?fmt(coverage.potential_saved):'—';document.querySelector('#missed-commands').textContent=coverage.available?coverage.missed_commands.toLocaleString():'—';document.querySelector('#scanned-sessions').textContent=coverage.available?coverage.sessions.toLocaleString():'—';document.querySelector('#opportunity-rows').innerHTML=(coverage.opportunities||[]).map(o=>`<tr><td>${{esc(o[0])}}</td><td>${{esc(o[1])}}</td><td>${{o[2].toLocaleString()}}</td><td class="saved">${{fmt(o[3])}}</td><td>${{o[4]}}%</td></tr>`).join('');document.querySelector('#coverage-empty').hidden=!!coverage.available;
}}
function shareData(){{const a=lastAggregate,t=totals(a.filtered);return {{generated_at:new Date().toISOString(),period_days:days||'all',privacy:true,rtk:{{raw:t.raw,optimized:t.opt,saved:t.saved,savings_pct:t.raw?+(t.saved/t.raw*100).toFixed(1):0,commands:t.count,projects:a.items.length}},memory:{{runs:a.memoryFiltered.length,completed:a.memoryFiltered.filter(m=>m[6]!=='incomplete').length,checks_passed:a.memoryFiltered.reduce((n,m)=>n+m[9],0)}},coverage:{{days:coverage.days,coverage_pct:coverage.coverage_pct,potential_saved:coverage.potential_saved,missed_commands:coverage.missed_commands}},health:{{rtk_version:health.rtk_version,records:health.records,first_record:health.first_record,last_record:health.last_record,parse_failures:health.parse_failures,invalid_memory_lines:health.invalid_memory_lines,retention_days:health.retention_days,discover_available:health.discover_available}}}}}}
function download(blob,name){{const link=document.createElement('a');link.href=URL.createObjectURL(blob);link.download=name;link.click();setTimeout(()=>URL.revokeObjectURL(link.href),1000)}}
document.querySelector('#share-json').onclick=()=>download(new Blob([JSON.stringify(shareData(),null,2)],{{type:'application/json'}}),'my-beast-mode-summary.json');
document.querySelector('#share-png').onclick=()=>{{const data=shareData(),canvas=document.createElement('canvas');canvas.width=1200;canvas.height=630;const c=canvas.getContext('2d');c.fillStyle='#090d18';c.fillRect(0,0,1200,630);c.fillStyle='#edf4ff';c.font='700 48px system-ui';c.fillText('My Beast Mode',56,82);c.fillStyle='#98a9c3';c.font='18px system-ui';c.fillText(`${{data.period_days}}-day private summary`,56,116);const cards=[['Tokens saved',fmt(data.rtk.saved)],['Compression',data.rtk.savings_pct+'%'],['Commands',data.rtk.commands.toLocaleString()],['Projects',data.rtk.projects.toLocaleString()],['Beast runs',data.memory.runs.toLocaleString()],['Checks passed',data.memory.checks_passed.toLocaleString()],['RTK coverage',(data.coverage.coverage_pct||0)+'%'],['Potential',fmt(data.coverage.potential_saved)]];cards.forEach(([label,value],i)=>{{const x=56+(i%4)*274,y=160+Math.floor(i/4)*150;c.fillStyle='#111827';c.fillRect(x,y,250,120);c.fillStyle='#98a9c3';c.font='16px system-ui';c.fillText(label,x+18,y+32);c.fillStyle=label==='Tokens saved'||label==='Potential'?'#62f5b5':'#edf4ff';c.font='700 30px system-ui';c.fillText(value,x+18,y+78)}});c.fillStyle='#98a9c3';c.font='14px system-ui';c.fillText('Sanitized export · no project paths, prompts, commands, or memory summaries',56,585);canvas.toBlob(blob=>download(blob,'my-beast-mode-summary.png'),'image/png')}};
document.querySelectorAll('[data-days]').forEach(b=>b.onclick=()=>{{days=+b.dataset.days;selected='';document.querySelectorAll('[data-days]').forEach(x=>x.classList.toggle('active',x===b));render()}});render();
</script></body></html>"""


def share_report(records: list[list[object]], memories: list[list[object]], coverage: dict[str, object], health: dict[str, object]) -> dict[str, object]:
    projects: dict[str, list[int]] = {}
    for row in records:
        values = projects.setdefault(str(row[1]), [0, 0, 0, 0])
        values[0] += safe_int(row[3])
        values[1] += safe_int(row[4])
        values[2] += safe_int(row[5])
        values[3] += 1
    project_rows = []
    for index, (_, values) in enumerate(sorted(projects.items(), key=lambda item: item[1][2], reverse=True), 1):
        project_rows.append({
            "project": f"Project {index:02d}",
            "raw": values[0],
            "optimized": values[1],
            "saved": values[2],
            "savings_pct": round(100 * values[2] / values[0], 1) if values[0] else 0,
            "commands": values[3],
        })
    raw, optimized, saved = sum(row[3] for row in records), sum(row[4] for row in records), sum(row[5] for row in records)
    outcomes: dict[str, int] = {}
    agents: dict[str, int] = {}
    for memory in memories:
        outcomes[str(memory[6])] = outcomes.get(str(memory[6]), 0) + 1
        agents[str(memory[5])] = agents.get(str(memory[5]), 0) + 1
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "privacy": True,
        "rtk": {"raw": raw, "optimized": optimized, "saved": saved, "savings_pct": round(100 * saved / raw, 1) if raw else 0, "commands": len(records)},
        "projects": project_rows,
        "memory": {"runs": len(memories), "outcomes": outcomes, "agents": agents, "checks_passed": sum(row[9] for row in memories)},
        "coverage": {key: coverage.get(key) for key in ("available", "days", "coverage_pct", "potential_saved", "missed_commands", "sessions")},
        "health": health,
    }


def write_dashboard(
    db_path: Path,
    output: Path,
    memory: Path,
    aliases: dict[str, str] | None = None,
    privacy: bool = False,
    discover_days: int = 30,
    coverage_override: dict[str, object] | None = None,
) -> tuple[Path, dict[str, object]]:
    namer = ProjectNamer(aliases, privacy)
    records = read_records(db_path, namer)
    memories, invalid = read_memories(memory, namer, privacy)
    coverage = coverage_override if coverage_override is not None else discover(discover_days)
    health = data_health(db_path, records, invalid, coverage)
    output = output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render(records, db_path, memories, memory, coverage, health, privacy), encoding="utf-8")
    return output, share_report(records, memories, coverage, health)


def self_test() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path, output, memory = Path(tmp) / "history.db", Path(tmp) / "dashboard.html", Path(tmp) / "memory.jsonl"
        with sqlite3.connect(db_path) as db:
            db.execute("CREATE TABLE commands(timestamp TEXT, project_path TEXT, rtk_cmd TEXT, input_tokens INTEGER, output_tokens INTEGER, saved_tokens INTEGER)")
            db.executemany("INSERT INTO commands VALUES(?,?,?,?,?,?)", [
                ("2026-09-01T10:00:00Z", "/work/alpha", "rtk git status", 1000, 300, 700),
                ("2026-09-02T10:00:00Z", "/work/beta", "rtk pytest -q", 800, 500, 300),
            ])
            db.commit()
        memory.write_text(
            '{"event":"start","session":"one","timestamp":"2026-09-02T09:00:00+00:00","project":"/work/alpha","task_type":"review","orchestrator":"host","agent":"codex","summary":"Review change"}\n'
            '{"event":"finish","session":"one","timestamp":"2026-09-02T09:05:00+00:00","project":"/work/alpha","outcome":"success","summary":"Review complete","files_changed":1,"checks_passed":2,"checks_failed":0}\n',
            encoding="utf-8",
        )
        coverage = {"available": True, "days": 30, "sessions": 2, "coverage_pct": 75.0, "missed_commands": 3, "potential_saved": 900, "opportunities": [["rtk git", "Git", 3, 900, 75.0]]}
        rendered, report = write_dashboard(db_path, output, memory, coverage_override=coverage)
        page = rendered.read_text(encoding="utf-8")
        assert all(value in page for value in ("/work/alpha", "git", "pytest", "700", "Review complete", "memory-runs", "rtk git", "codex"))
        private, _ = write_dashboard(db_path, Path(tmp) / "private.html", memory, privacy=True, coverage_override=coverage)
        private_page = private.read_text(encoding="utf-8")
        assert "/work/alpha" not in private_page and "Review complete" not in private_page and "Project 01" in private_page
        assert report["projects"][0]["project"] == "Project 01"
    print("self-test passed")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", help="RTK history.db path")
    parser.add_argument("--memory", help="My Beast Mode memory.jsonl path")
    parser.add_argument("--output", default=".my-beast-mode/dashboard.html", help="output HTML path")
    parser.add_argument("--aliases", help="JSON file mapping project paths to display labels")
    parser.add_argument("--privacy", action="store_true", help="hide project paths and memory summaries")
    parser.add_argument("--discover-days", type=int, choices=range(1, 366), default=30, metavar="1..365")
    parser.add_argument("--no-discover", action="store_true", help="skip RTK missed-savings discovery")
    parser.add_argument("--export-json", help="write a sanitized aggregate JSON report")
    parser.add_argument("--open", action="store_true", help="open the dashboard in the default browser")
    parser.add_argument("--self-test", action="store_true", help="run the bundled smoke test")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    coverage = {"available": False, "days": args.discover_days, "opportunities": []} if args.no_discover else None
    output, report = write_dashboard(
        find_database(args.db),
        Path(args.output),
        memory_path(args.memory),
        aliases=load_aliases(args.aliases),
        privacy=args.privacy,
        discover_days=args.discover_days,
        coverage_override=coverage,
    )
    print(output)
    if args.export_json:
        export = Path(args.export_json).expanduser().resolve()
        export.parent.mkdir(parents=True, exist_ok=True)
        export.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(export)
    if args.open:
        webbrowser.open(output.as_uri())


if __name__ == "__main__":
    main()
