#!/usr/bin/env python3
"""Build a private, dependency-free RTK savings dashboard."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
from pathlib import Path
import shlex
import sqlite3
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


def project_label(path: str) -> str:
    if not path:
        return "Unknown project"
    home = str(Path.home())
    return "~" + path[len(home) :] if path == home or path.startswith(home + os.sep) else path


def read_records(db_path: Path) -> list[list[object]]:
    uri = f"file:{db_path.as_posix()}?mode=ro&immutable=1"
    with sqlite3.connect(uri, uri=True) as db:
        columns = {row[1] for row in db.execute("PRAGMA table_info(commands)")}
        required = {"timestamp", "project_path", "rtk_cmd", "input_tokens", "output_tokens", "saved_tokens"}
        if not required <= columns:
            missing = ", ".join(sorted(required - columns))
            raise RuntimeError(f"Unsupported RTK history schema; missing: {missing}")
        rows = db.execute(
            "SELECT timestamp, project_path, rtk_cmd, input_tokens, output_tokens, saved_tokens "
            "FROM commands ORDER BY timestamp"
        )
        return [
            [timestamp[:10], project_label(project), command_family(command), raw, optimized, saved]
            for timestamp, project, command, raw, optimized, saved in rows
        ]


def safe_json(value: object) -> str:
    return json.dumps(value, separators=(",", ":")).replace("</", "<\\/")


def render(records: list[list[object]], db_path: Path) -> str:
    generated = dt.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")
    source = project_label(str(db_path))
    data = safe_json(records)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>My Beast Mode · RTK Savings</title>
<style>
:root{{--bg:#090d18;--panel:#111827;--soft:#1c2638;--text:#edf4ff;--muted:#98a9c3;--green:#62f5b5;--cyan:#5dd7ff;--purple:#a78bfa;--line:#26344d}}
*{{box-sizing:border-box}} body{{margin:0;background:radial-gradient(circle at 80% 0,#17213d 0,transparent 35%),var(--bg);color:var(--text);font:15px/1.5 system-ui,sans-serif}}
main{{max-width:1280px;margin:auto;padding:32px 20px 64px}} header{{display:flex;justify-content:space-between;gap:20px;align-items:end;flex-wrap:wrap}} h1{{font-size:clamp(28px,5vw,48px);line-height:1;margin:0}} h2{{font-size:18px;margin:0 0 18px}} .eyebrow,.meta,small{{color:var(--muted)}} .eyebrow{{text-transform:uppercase;letter-spacing:.14em;font-weight:700}} .filters{{display:flex;gap:6px;background:var(--panel);border:1px solid var(--line);padding:5px;border-radius:12px}} button{{color:var(--muted);background:transparent;border:0;padding:8px 12px;border-radius:8px;cursor:pointer;font:inherit}} button.active,button:hover{{background:var(--soft);color:var(--text)}} .kpis{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:26px 0}} .card,.panel{{background:color-mix(in srgb,var(--panel) 92%,transparent);border:1px solid var(--line);border-radius:16px}} .card{{padding:20px}} .value{{font-size:clamp(24px,4vw,36px);font-weight:750;margin-top:5px}} .saved{{color:var(--green)}} .grid{{display:grid;grid-template-columns:1.4fr 1fr;gap:14px}} .panel{{padding:20px;min-width:0}} #trend{{width:100%;height:230px;display:block}} .axis{{stroke:#33415d;stroke-width:1}} .trend{{fill:none;stroke:var(--green);stroke-width:3;stroke-linejoin:round}} .area{{fill:url(#fade)}} .bars{{display:grid;gap:12px}} .bar-head{{display:flex;justify-content:space-between;gap:12px}} .bar-track{{height:8px;background:var(--soft);border-radius:10px;overflow:hidden}} .bar-fill{{height:100%;background:linear-gradient(90deg,var(--cyan),var(--purple));border-radius:inherit}} .table-panel{{margin-top:14px;overflow:hidden}} .scroll{{overflow:auto}} table{{border-collapse:collapse;width:100%;min-width:860px}} th,td{{padding:12px 14px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap}} th{{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.07em}} th:first-child,td:first-child,th:last-child,td:last-child{{text-align:left}} tbody tr{{cursor:pointer}} tbody tr:hover,tbody tr.selected{{background:var(--soft)}} .project{{max-width:330px;overflow:hidden;text-overflow:ellipsis}} .pill{{display:inline-block;background:#1b3041;color:var(--cyan);padding:2px 7px;border-radius:99px;margin:2px;font-size:12px}} .empty{{padding:50px;text-align:center;color:var(--muted)}} footer{{margin-top:16px;color:var(--muted);font-size:12px;overflow-wrap:anywhere}} @media(max-width:800px){{.kpis{{grid-template-columns:repeat(2,1fr)}}.grid{{grid-template-columns:1fr}}}} @media(max-width:460px){{.kpis{{grid-template-columns:1fr}}}}
</style></head><body><main>
<header><div><div class="eyebrow">Local RTK analytics</div><h1>My Beast Mode</h1><div class="meta">Token optimization by project · updated {html.escape(generated)}</div></div>
<div class="filters" aria-label="Time period"><button data-days="7">7d</button><button data-days="30" class="active">30d</button><button data-days="90">90d</button><button data-days="0">All</button></div></header>
<section class="kpis"><div class="card"><small>Tokens saved</small><div id="saved" class="value saved">—</div></div><div class="card"><small>Compression</small><div id="rate" class="value">—</div></div><div class="card"><small>Commands optimized</small><div id="commands" class="value">—</div></div><div class="card"><small>Active projects</small><div id="projects" class="value">—</div></div></section>
<section class="grid"><div class="panel"><h2>Daily tokens saved</h2><svg id="trend" role="img" aria-label="Daily saved-token trend"></svg></div><div class="panel"><h2 id="detail-title">How RTK optimized output</h2><div id="categories" class="bars"></div></div></section>
<section class="panel table-panel"><h2>Projects</h2><div class="scroll"><table><thead><tr><th>Project</th><th>Raw</th><th>Optimized</th><th>Saved</th><th>Savings</th><th>Commands</th><th>How</th></tr></thead><tbody id="rows"></tbody></table></div><div id="empty" class="empty" hidden>No RTK activity in this period.</div></section>
<footer>Private local report · source: {html.escape(source)} · RTK estimates tokens from text size; values are optimization analytics, not API billing records.</footer>
</main><script>
const records={data};
const fmt=n=>Intl.NumberFormat(undefined,{{notation:'compact',maximumFractionDigits:1}}).format(n||0);
const esc=s=>String(s).replace(/[&<>"']/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));
let days=30, selected='';
function aggregate(){{
 const cutoff=days?new Date(Date.now()-days*864e5).toISOString().slice(0,10):'';
 const filtered=records.filter(r=>!cutoff||r[0]>=cutoff), projects=new Map(), daily=new Map(), allCats=new Map();
 for(const [date,project,family,raw,opt,saved] of filtered){{
  const p=projects.get(project)||{{project,raw:0,opt:0,saved:0,count:0,cats:new Map()}}; p.raw+=raw;p.opt+=opt;p.saved+=saved;p.count++;p.cats.set(family,(p.cats.get(family)||0)+saved);projects.set(project,p);
  daily.set(date,(daily.get(date)||0)+saved);allCats.set(family,(allCats.get(family)||0)+saved);
 }}
 return {{items:[...projects.values()].sort((a,b)=>b.saved-a.saved),daily:[...daily].sort(),cats:allCats,filtered}};
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
function render(){{
 const a=aggregate(),raw=a.items.reduce((n,p)=>n+p.raw,0),saved=a.items.reduce((n,p)=>n+p.saved,0);
 document.querySelector('#saved').textContent=fmt(saved);document.querySelector('#rate').textContent=raw?`${{(saved/raw*100).toFixed(1)}}%`:'0%';document.querySelector('#commands').textContent=a.filtered.length.toLocaleString();document.querySelector('#projects').textContent=a.items.length.toLocaleString();drawTrend(a.daily);
 const chosen=a.items.find(p=>p.project===selected);document.querySelector('#detail-title').textContent=chosen?`How · ${{chosen.project}}`:'How RTK optimized output';document.querySelector('#categories').innerHTML=categoryRows(chosen?chosen.cats:a.cats);
 document.querySelector('#rows').innerHTML=a.items.map(p=>{{const cats=[...p.cats].sort((x,y)=>y[1]-x[1]).slice(0,3).map(x=>`<span class="pill">${{esc(x[0])}}</span>`).join('');return `<tr data-project="${{esc(p.project)}}" class="${{p.project===selected?'selected':''}}"><td class="project" title="${{esc(p.project)}}">${{esc(p.project)}}</td><td>${{fmt(p.raw)}}</td><td>${{fmt(p.opt)}}</td><td class="saved">${{fmt(p.saved)}}</td><td>${{p.raw?(p.saved/p.raw*100).toFixed(1):0}}%</td><td>${{p.count.toLocaleString()}}</td><td>${{cats}}</td></tr>`}}).join('');document.querySelector('#empty').hidden=!!a.items.length;
 document.querySelectorAll('tbody tr').forEach(row=>row.onclick=()=>{{selected=selected===row.dataset.project?'':row.dataset.project;render()}});
}}
document.querySelectorAll('[data-days]').forEach(b=>b.onclick=()=>{{days=+b.dataset.days;selected='';document.querySelectorAll('[data-days]').forEach(x=>x.classList.toggle('active',x===b));render()}});render();
</script></body></html>"""


def write_dashboard(db_path: Path, output: Path) -> Path:
    records = read_records(db_path)
    output = output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render(records, db_path), encoding="utf-8")
    return output


def self_test() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path, output = Path(tmp) / "history.db", Path(tmp) / "dashboard.html"
        with sqlite3.connect(db_path) as db:
            db.execute("CREATE TABLE commands(timestamp TEXT, project_path TEXT, rtk_cmd TEXT, input_tokens INTEGER, output_tokens INTEGER, saved_tokens INTEGER)")
            db.executemany("INSERT INTO commands VALUES(?,?,?,?,?,?)", [
                ("2026-09-01T10:00:00Z", "/work/alpha", "rtk git status", 1000, 300, 700),
                ("2026-09-02T10:00:00Z", "/work/beta", "rtk pytest -q", 800, 500, 300),
            ])
            db.commit()
        page = write_dashboard(db_path, output).read_text(encoding="utf-8")
        assert "/work/alpha" in page and "git" in page and "pytest" in page and "700" in page
    print("self-test passed")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", help="RTK history.db path")
    parser.add_argument("--output", default=".my-beast-mode/dashboard.html", help="output HTML path")
    parser.add_argument("--open", action="store_true", help="open the dashboard in the default browser")
    parser.add_argument("--self-test", action="store_true", help="run the bundled smoke test")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    output = write_dashboard(find_database(args.db), Path(args.output))
    print(output)
    if args.open:
        webbrowser.open(output.as_uri())


if __name__ == "__main__":
    main()
