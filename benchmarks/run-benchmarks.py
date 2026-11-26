import os
import re
import sys
import time
import shutil
import platform
import tempfile
import statistics
import subprocess
from pathlib import Path
from solver import parse_dimacs
import encoders

timeout=int(sys.argv[1]) if len(sys.argv)>1 else 120
runs=int(sys.argv[2]) if len(sys.argv)>2 else 3
root=Path(__file__).resolve().parent
out=[]

def log(line=""):
    print(line, flush=True)
    out.append(line)

def sh(cmd):
    try:
        p=subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return (p.stdout+p.stderr).strip()
    except Exception:
        return "n/a"

def fmt_time(t):
    return "timeout" if t is None else f"{t:.2f}s"

engines=[("CPython", sys.executable)]
pypy=shutil.which("pypy3") or shutil.which("pypy")
if pypy:
    engines.append(("PyPy3", pypy))

try:
    from pysat.solvers import Minisat22
except ImportError:
    Minisat22=None

def run_solver(exe, path):
    try:
        p=subprocess.run([exe, str(root/"solver.py"), str(path)], capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"time":None, "status":"timeout", "conflicts":None, "vars":None, "clauses":None, "valid":None}
    text=p.stdout
    if p.returncode!=0:
        return {"time":None, "status":"ERROR: "+p.stderr.strip().splitlines()[-1] if p.stderr.strip() else "ERROR", "conflicts":None, "vars":None, "clauses":None, "valid":None}
    m_time=re.search(r"Solve time: ([\d.]+)s", text)
    m_conf=re.search(r"conflicts:\s+(\d+)", text)
    m_prob=re.search(r"Problem: (\d+) variables, (\d+) clauses", text)
    status="UNSAT" if "UNSATISFIABLE" in text else "SAT" if "SATISFIABLE" in text else "?"
    valid=None
    if status=="SAT":
        valid=text.strip().splitlines()[-1].strip()=="True"
    return {
        "time":float(m_time.group(1)) if m_time else None,
        "status":status,
        "conflicts":int(m_conf.group(1)) if m_conf else None,
        "vars":int(m_prob.group(1)) if m_prob else None,
        "clauses":int(m_prob.group(2)) if m_prob else None,
        "valid":valid,
    }

def run_minisat(path):
    if Minisat22 is None:
        return None, None
    clauses, numvars, has_empty=parse_dimacs(str(path), verbose=False)
    raw=[c.literals for c in clauses]
    s=Minisat22(bootstrap_with=raw)
    start=time.perf_counter()
    result=s.solve()
    elapsed=time.perf_counter()-start
    s.delete()
    return ("SAT" if result else "UNSAT"), elapsed

def bench_instance(label, path, expected, runs):
    row={"label":label, "engines":{}}
    for name, exe in engines:
        print(f"  running {label} with {name}...", flush=True)
        results=[run_solver(exe, path) for _ in range(runs)]
        good=[r for r in results if r["time"] is not None]
        last=results[-1]
        row["engines"][name]={
            "time":statistics.median([r["time"] for r in good]) if len(good)==len(results) else None,
            "status":last["status"],
            "conflicts":last["conflicts"],
            "valid":last["valid"],
        }
        row["vars"]=last["vars"] or row.get("vars")
        row["clauses"]=last["clauses"] or row.get("clauses")
    print(f"  running {label} with MiniSat...", flush=True)
    ms_status, ms_time=run_minisat(path)
    row["minisat"]=(ms_status, ms_time)
    row["expected"]=expected
    return row

def print_header():
    cols=["Instance","Vars","Clauses","Status"]
    for name, _ in engines:
        cols+=[f"{name} time", f"{name} conflicts"]
    cols+=["MiniSat time"]
    log("| "+" | ".join(cols)+" |")
    log("|"+"|".join([" --- "]*len(cols))+"|")

def print_row(row):
    first=row["engines"][engines[0][0]]
    flags=[]
    for name, _ in engines:
        e=row["engines"][name]
        if e["status"] in ("SAT","UNSAT") and row["expected"] and e["status"]!=row["expected"]:
            flags.append(f"{name}:MISMATCH")
        if e["valid"] is False:
            flags.append(f"{name}:INVALID MODEL")
        if e["status"].startswith("ERROR"):
            flags.append(f"{name}:{e['status']}")
    ms_status, ms_time=row["minisat"]
    if ms_status and first["status"] in ("SAT","UNSAT") and ms_status!=first["status"]:
        flags.append("MINISAT DISAGREES")
    status=first["status"]+(" ["+", ".join(flags)+"]" if flags else "")
    cells=[row["label"], str(row.get("vars") or "?"), str(row.get("clauses") or "?"), status]
    for name, _ in engines:
        e=row["engines"][name]
        cells+=[fmt_time(e["time"]), str(e["conflicts"]) if e["conflicts"] is not None else "-"]
    cells+=[fmt_time(ms_time) if ms_time is not None else "n/a"]
    log("| "+" | ".join(cells)+" |")

def run_group(title, items):
    log()
    log(f"## {title}")
    log()
    print_header()
    rows=[]
    for label, path, expected, runs in items:
        if path is None or not Path(path).exists():
            log(f"| {label} | missing file |")
            continue
        row=bench_instance(label, path, expected, runs)
        print_row(row)
        rows.append(row)
    return rows

def summary(title, rows):
    if not rows:
        return
    log()
    log(f"### Summary {title} ({len(rows)} instances)")
    for name, _ in engines:
        times=[r["engines"][name]["time"] for r in rows if r["engines"][name]["time"] is not None]
        confs=[r["engines"][name]["conflicts"] for r in rows if r["engines"][name]["conflicts"] is not None]
        timeouts=sum(1 for r in rows if r["engines"][name]["time"] is None)
        if times:
            line=f"- {name}: mean {statistics.mean(times):.2f}s, median {statistics.median(times):.2f}s, max {max(times):.2f}s, timeouts {timeouts}"
            if confs:
                line+=f", mean conflicts {statistics.mean(confs):.0f}"
            log(line)
    ms=[r["minisat"][1] for r in rows if r["minisat"][1] is not None]
    if ms:
        log(f"- MiniSat: mean {statistics.mean(ms):.4f}s, max {max(ms):.4f}s")

log("# Benchmark results")
log()
log(f"Date: {time.strftime('%Y-%m-%d %H:%M')}  |  timeout per run: {timeout}s")
log(f"OS: {platform.platform()}")
if sys.platform=="win32":
    cpu=sh(["powershell","-NoProfile","-Command","(Get-CimInstance Win32_Processor).Name"])
    ram=sh(["powershell","-NoProfile","-Command","[math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB)"])
    log(f"CPU: {cpu}  |  RAM: {ram} GB  |  logical cores: {os.cpu_count()}")
else:
    log(f"CPU: {platform.processor() or 'n/a'}  |  logical cores: {os.cpu_count()}")
for name, exe in engines:
    log(f"{name}: {sh([exe,'--version']).splitlines()[0] if sh([exe,'--version']) else 'n/a'}")
if not pypy:
    log("PyPy3: not found in PATH (skipped)")
if Minisat22 is None:
    log("MiniSat: python-sat not installed (skipped)")

log()
log("## Tests")
p=subprocess.run([sys.executable,"-m","pytest","-q","-p","no:cacheprovider",str(root/"test_solver.py")], capture_output=True, text=True, cwd=root)
tail=[l for l in p.stdout.strip().splitlines() if l.strip()]
log(tail[-1] if tail else "pytest: no output")

try:
    with tempfile.TemporaryDirectory() as tmp:
        tmp=Path(tmp)
        for n in (6,7,8,9):
            clauses, numvars=encoders.pigeonhole(n)
            encoders.write_dimacs(clauses, numvars, str(tmp/f"php{n}.cnf"))
        for n in (8,12,20):
            clauses, numvars=encoders.nqueens(n)
            encoders.write_dimacs(clauses, numvars, str(tmp/f"q{n}.cnf"))

        def find(name):
            return next(root.rglob(name), None)

        php_sizes=(6,7,8,9) if timeout>=300 else (6,7,8)
        run_group(f"Hanoi (planning, SAT, median of {runs} runs)", [
            ("hanoi4", find("hanoi4.cnf"), "SAT", runs),
            ("hanoi5", find("hanoi5.cnf"), "SAT", runs),
        ])
        run_group(f"Pigeonhole (UNSAT, median of {runs} runs)", [(f"php{n}", tmp/f"php{n}.cnf", "UNSAT", runs) for n in php_sizes])
        run_group(f"N-Queens (SAT, median of {runs} runs)", [(f"queens{n}", tmp/f"q{n}.cnf", "SAT", runs) for n in (8,12,20)])
        uf=sorted(root.rglob("uf250-*.cnf"))[:10]
        uuf=sorted(root.rglob("uuf250-*.cnf"))[:10]
        uf_rows=run_group("SATLIB uf250 (SAT)", [(p.name, p, "SAT", 1) for p in uf] or [("uf250", None, "SAT", 1)])
        summary("uf250", uf_rows)
        uuf_rows=run_group("SATLIB uuf250 (UNSAT)", [(p.name, p, "UNSAT", 1) for p in uuf] or [("uuf250", None, "UNSAT", 1)])
        summary("uuf250", uuf_rows)
    log()
    log("Done.")
except KeyboardInterrupt:
    log()
    log("Interrupted: partial results above.")
finally:
    (root/"bench_results.txt").write_text("\n".join(out), encoding="utf-8")