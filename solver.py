import sys
import time
import heapq
from collections import deque
from dataclasses import dataclass

@dataclass(eq=False, slots=True)
class Clause:
    literals:list[int]
    watch1:int=0
    watch2:int=1
    lbd:int=0
    deleted:bool=False

def evaluate_clause(clause, val):
    unresolved=False
    for n in clause.literals:
        if val[n]==1:
            return True
        if val[n]==0:
            unresolved=True
    if unresolved:
        return None
    else:
        return False

def init_watches(clauses, numvars):
    watches=[[] for _ in range(2*numvars+1)]
    for clause in clauses:
        literals=clause.literals
        if len(literals)>=2:
            watches[literals[clause.watch1]].append((literals[clause.watch2], clause))
            watches[literals[clause.watch2]].append((literals[clause.watch1], clause))
        else:
            clause.watch2=0
            watches[literals[0]].append((literals[0], clause))
    return watches

def unit_propagate(watches, val, level, reason, trail, current_level, prop_queue, saved_phase):
    while prop_queue:
        p=prop_queue.popleft()
        false_lit=-p
        watch_list=watches[false_lit]
        i=0
        j=0
        n=len(watch_list)
        conflict=None
        while i<n:
            entry=watch_list[i]
            clause=entry[1]
            i+=1
            if clause.deleted:
                continue
            if val[entry[0]]==1:
                watch_list[j]=entry
                j+=1
                continue
            literals=clause.literals
            w1=clause.watch1
            if literals[w1]==false_lit:
                other_watch_index=clause.watch2
                is_w1=True
            else:
                other_watch_index=w1
                is_w1=False
            other_lit=literals[other_watch_index]
            if val[other_lit]==1:
                watch_list[j]=(other_lit, clause)
                j+=1
                continue
            found_new_watch=False
            for k, lit_k in enumerate(literals):
                if k!=other_watch_index:
                    if val[lit_k]!=-1:
                        if is_w1:
                            clause.watch1=k
                        else:
                            clause.watch2=k
                        watches[lit_k].append((other_lit, clause))
                        found_new_watch=True
                        break
            if found_new_watch:
                continue
            watch_list[j]=(other_lit, clause)
            j+=1
            if val[other_lit]==0:
                var=abs(other_lit)
                val[other_lit]=1
                val[-other_lit]=-1
                level[var]=current_level
                reason[var]=clause
                saved_phase[var]=1 if other_lit>0 else -1
                trail.append(var)
                prop_queue.append(other_lit)
            else:
                conflict=clause
                while i<n:
                    watch_list[j]=watch_list[i]
                    i+=1
                    j+=1
                break
        del watch_list[j:]
        if conflict is not None:
            return conflict
    return None

def analyze_conflict(conflict_clause, level, reason, current_level, trail, val, seen):
    learned_clause=[]
    path_cnt=0
    idx=len(trail)-1
    clause=conflict_clause
    to_clear=[]
    while True:
        for lit in clause.literals:
            v=abs(lit)
            if not seen[v] and level[v]>0:
                seen[v]=True
                to_clear.append(v)
                if level[v]==current_level:
                    path_cnt+=1
                else:
                    learned_clause.append(lit)
        while idx>=0 and not seen[trail[idx]]:
            idx-=1
        p=trail[idx]
        idx-=1
        path_cnt-=1
        if path_cnt==0:
            assert_lit=-p if val[p]==1 else p
            learned_clause.insert(0, assert_lit)
            break
        clause=reason[p]
    for v in to_clear:
        seen[v]=False
    backjump_level=0
    max_i=1
    for i in range(1, len(learned_clause)):
        lvl=level[abs(learned_clause[i])]
        if lvl>backjump_level:
            backjump_level=lvl
            max_i=i
    if len(learned_clause)>1:
        learned_clause[1], learned_clause[max_i] = learned_clause[max_i], learned_clause[1]
    lbd=len({level[abs(lit)] for lit in learned_clause})
    return learned_clause, backjump_level, lbd

def parse_dimacs(filename):
    clauses=[]
    current_clause=[]
    numvars=0
    with open(filename, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("c") or line.startswith("%"):
                continue
            if line.startswith("p"):
                tokens = line.split()
                numvars = int(tokens[2])
                numclauses = int(tokens[3])
                print(f"Problem: {numvars} variables, {numclauses} clauses")
                continue
            tokens = line.split()
            for token in tokens:
                val=int(token)
                if val==0:
                    if current_clause:
                        literals=list(dict.fromkeys(current_clause))
                        if not any(-n in literals for n in literals):
                            clauses.append(Clause(literals=literals))
                        current_clause=[]
                else:
                    current_clause.append(val)
    if current_clause:
        literals=list(dict.fromkeys(current_clause))
        if not any(-n in literals for n in literals):
            clauses.append(Clause(literals=literals))
    return clauses,numvars

def validate_solution(clauses, solution):
    for clause in clauses:
        clause_satisfied = False
        for n in clause.literals:
            if solution[n]==1:
                clause_satisfied = True
                break
        if not clause_satisfied:
            return False
    return True

def solve(clauses, numvars, current_level=0):
    watches=init_watches(clauses, numvars)
    val=[0]*(2*numvars+1)
    level=[0]*(numvars+1)
    reason=[None]*(numvars+1)
    saved_phase=[1]*(numvars+1)
    seen=[False]*(numvars+1)
    trail=[]
    prop_queue=deque()
    for clause in clauses:
        if len(clause.literals)==1:
            unit_lit=clause.literals[0]
            if val[unit_lit]==0:
                var=abs(unit_lit)
                val[unit_lit]=1
                val[-unit_lit]=-1
                level[var]=0
                reason[var]=clause
                saved_phase[var]=1 if unit_lit>0 else -1
                trail.append(var)
                prop_queue.append(unit_lit)
    conflict_clause=unit_propagate(watches, val, level, reason, trail, 0, prop_queue, saved_phase)
    if conflict_clause is not None:
        return None
    activity=[0.0]*(numvars+1)
    for clause in clauses:
        for n in clause.literals:
            activity[abs(n)]+=1.0
    heap=[(-activity[v], v) for v in range(1, numvars+1)]
    heapq.heapify(heap)
    var_inc=1.0
    decay=0.95
    conflicts=0
    learned_clauses=[]
    max_learned=500
    restart_inc=100
    next_restart=100
    while True:
        if conflicts>=next_restart:
            next_restart=conflicts+restart_inc
            restart_inc=int(restart_inc*1.5)
            while trail and level[trail[-1]]>0:
                var=trail.pop()
                val[var]=0
                val[-var]=0
                reason[var]=None
                heapq.heappush(heap, (-activity[var], var))
            current_level=0
            prop_queue.clear()
        var_to_assign=None
        while heap:
            neg_act, v = heapq.heappop(heap)
            if val[v]==0:
                if -neg_act!=activity[v]:
                    continue
                var_to_assign=v
                break
        if var_to_assign is None:
            print("conflicts: ", conflicts)
            return val[:]
        current_level+=1
        lit_to_assign=var_to_assign if saved_phase[var_to_assign]==1 else -var_to_assign
        val[lit_to_assign]=1
        val[-lit_to_assign]=-1
        level[var_to_assign]=current_level
        reason[var_to_assign]=None
        saved_phase[var_to_assign]=1 if lit_to_assign>0 else -1
        trail.append(var_to_assign)
        prop_queue.append(lit_to_assign)
        while True:
            conflict_clause=unit_propagate(watches, val, level, reason, trail, current_level, prop_queue, saved_phase)
            if conflict_clause is None:
                break
            if current_level==0:
                return None
            conflicts+=1
            prop_queue.clear()
            learned_clause, backjump_level, lbd=analyze_conflict(conflict_clause, level, reason, current_level, trail, val, seen)
            for lit in learned_clause:
                activity[abs(lit)]+=var_inc
            var_inc/=decay
            if var_inc>1e100:
                for v in range(1, numvars+1):
                    activity[v]*=1e-100
                var_inc*=1e-100
                heap=[(-activity[v], v) for v in range(1, numvars+1) if val[v]==0]
                heapq.heapify(heap)
            while trail and level[trail[-1]]>backjump_level:
                var=trail.pop()
                val[var]=0
                val[-var]=0
                reason[var]=None
                heapq.heappush(heap, (-activity[var], var))
            current_level=backjump_level
            new_clause=Clause(literals=learned_clause, lbd=lbd)
            learned_clauses.append(new_clause)
            if len(learned_clauses)>max_learned:
                learned_clauses.sort(key=lambda c: c.lbd)
                half=len(learned_clauses)//2
                for c in learned_clauses[half:]:
                    if c.lbd>2:
                        c.deleted=True
                learned_clauses=[c for c in learned_clauses if not c.deleted]
                max_learned+=300
            if len(new_clause.literals)>=2:
                watches[new_clause.literals[new_clause.watch1]].append((new_clause.literals[new_clause.watch2], new_clause))
                watches[new_clause.literals[new_clause.watch2]].append((new_clause.literals[new_clause.watch1], new_clause))
            else:
                new_clause.watch2=0
                watches[new_clause.literals[0]].append((new_clause.literals[0], new_clause))
            assert_lit=new_clause.literals[0]
            var_assert=abs(assert_lit)
            val[assert_lit]=1
            val[-assert_lit]=-1
            level[var_assert]=current_level
            reason[var_assert]=new_clause
            saved_phase[var_assert]=1 if assert_lit>0 else -1
            trail.append(var_assert)
            prop_queue.append(assert_lit)

if __name__=="__main__":
    if len(sys.argv)<2:
        print("Usage: python solver.py <path_to_dimacs.cnf>")
        sys.exit(1)
    filename=sys.argv[1]
    start=time.perf_counter()
    clauses, numvars = parse_dimacs(filename)
    originals=list(clauses)
    parse_time=time.perf_counter()-start
    start=time.perf_counter()
    result = solve(clauses, numvars)
    solve_time=time.perf_counter()-start
    print(f"Parse time: {parse_time:.4f}s")
    print(f"Solve time: {solve_time:.4f}s")
    if result is None:
        print("UNSATISFIABLE")
    else:
        print("SATISFIABLE")
        print(validate_solution(originals, result))