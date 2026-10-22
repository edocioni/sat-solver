import sys
import time
from collections import deque
from dataclasses import dataclass

@dataclass(eq=False)
class Clause:
    literals:list[int]
    watch1:int=0
    watch2:int=1

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

def assign(val, level, reason, trail, lit, current_level, antecedent):
    var=abs(lit)
    val[lit]=1
    val[-lit]=-1
    level[var]=current_level
    reason[var]=antecedent
    trail.append(var)

def unit_propagate(watches, val, level, reason, trail, current_level, prop_queue):
    while prop_queue:
        p=prop_queue.popleft()
        false_lit=-p
        watch_list=watches[false_lit]
        kept=[]
        for index in range(len(watch_list)):
            entry=watch_list[index]
            if val[entry[0]]==1:
                kept.append(entry)
                continue
            clause=entry[1]
            literals=clause.literals
            if literals[clause.watch1]==false_lit:
                other_watch_index=clause.watch2
            else:
                other_watch_index=clause.watch1
            other_lit=literals[other_watch_index]
            if val[other_lit]==1:
                kept.append((other_lit, clause))
                continue
            found_new_watch=False
            for k in range(len(literals)):
                if k!=other_watch_index:
                    lit_k=literals[k]
                    if val[lit_k]!=-1:
                        if literals[clause.watch1]==false_lit:
                            clause.watch1=k
                        else:
                            clause.watch2=k
                        watches[lit_k].append((other_lit, clause))
                        found_new_watch=True
                        break
            if found_new_watch:
                continue
            kept.append((other_lit, clause))
            if val[other_lit]==0:
                assign(val, level, reason, trail, other_lit, current_level, clause)
                prop_queue.append(other_lit)
            else:
                kept.extend(watch_list[index+1:])
                watches[false_lit]=kept
                return clause
        watches[false_lit]=kept
    return None          

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

def analyze_conflict(conflict_clause, level, reason, current_level, assignment_list):
    if conflict_clause is None:
        return None
    learned_clause = list(conflict_clause.literals)
    assignments_order=assignment_list
    index=len(assignments_order)-1
    while True:
        current_level_literals=[]
        for literal in learned_clause:
            var=abs(literal)
            if level[var]==current_level:
                current_level_literals.append(literal)
        if len(current_level_literals)<=1:
            break
        vars_in_clause={abs(x) for x in learned_clause}
        while index>=0 and assignments_order[index] not in vars_in_clause:
            index-=1
        if index<0:
            break
        var_to_resolve=assignments_order[index]
        index-=1
        antecedent=reason[var_to_resolve]
        if antecedent is None:
            break   
        resolved_literal=[lit for lit in learned_clause if abs(lit)==var_to_resolve][0]
        learned_clause=set(learned_clause) | set(antecedent.literals)
        learned_clause.discard(resolved_literal)
        learned_clause.discard(-resolved_literal)
        learned_clause=list(learned_clause)
    learned_clause=[lit for lit in learned_clause if level[abs(lit)]>0]
    levels=sorted(set(level[abs(lit)] for lit in learned_clause), reverse=True)
    backjump_level=levels[1] if len(levels)>1 else 0
    return learned_clause, backjump_level

def solve(clauses, numvars, current_level=0):
    watches=init_watches(clauses, numvars)
    val=[0]*(2*numvars+1)
    level=[0]*(numvars+1)
    reason=[None]*(numvars+1)
    trail=[]
    prop_queue=deque()
    for clause in clauses:
        if len(clause.literals)==1:
            unit_lit=clause.literals[0]
            if val[unit_lit]==0:
                assign(val, level, reason, trail, unit_lit, 0, clause)
                prop_queue.append(unit_lit)
    conflict_clause=unit_propagate(watches, val, level, reason, trail, 0, prop_queue)
    if conflict_clause is not None:
        return None
    activity={v: 0.0 for v in range(1, numvars+1)}
    for clause in clauses:
        for n in clause.literals:
            activity[abs(n)]+=1.0
    var_inc=1.0
    decay=0.95
    conflicts=0
    while True:
        unassigned=[v for v in range(1, numvars+1) if val[v]==0]
        if not unassigned:
            print("conflicts: ", conflicts)
            return val[:]
        var_to_assign=max(unassigned, key=activity.get)
        current_level+=1
        assign(val, level, reason, trail, var_to_assign, current_level, None)
        prop_queue=deque([var_to_assign])
        while True:
            conflict_clause=unit_propagate(watches, val, level, reason, trail, current_level, prop_queue)
            if conflict_clause is None:
                break
            if current_level==0:
                return None
            conflicts+=1
            assignments_list=[v for v in trail if level[v]==current_level]
            result=analyze_conflict(conflict_clause, level, reason, current_level, assignments_list)
            if result is None:
                return None
            learned_clause, backjump_level=result
            if not learned_clause:
                return None
            for lit in learned_clause:
                activity[abs(lit)]+=var_inc
            var_inc/=decay
            if var_inc>1e100:
                for v in activity:
                    activity[v]*=1e-100
                var_inc*=1e-100
            uip_lits=[lit for lit in learned_clause if level[abs(lit)]==current_level]
            assert len(uip_lits)==1
            assert_lit=uip_lits[0]
            rest=[lit for lit in learned_clause if lit!=assert_lit]
            rest.sort(key=lambda lit: level[abs(lit)], reverse=True)
            learned_clause=[assert_lit]+rest
            kept_trail=[]
            for var in trail:
                if level[var]>backjump_level:
                    val[var]=0
                    val[-var]=0
                    reason[var]=None
                else:
                    kept_trail.append(var)
            trail[:]=kept_trail
            current_level=backjump_level
            new_clause=Clause(literals=learned_clause)
            clauses.append(new_clause)
            if len(new_clause.literals)>=2:
                watches[new_clause.literals[new_clause.watch1]].append((new_clause.literals[new_clause.watch2], new_clause))
                watches[new_clause.literals[new_clause.watch2]].append((new_clause.literals[new_clause.watch1], new_clause))
            else:
                new_clause.watch2=0
                watches[new_clause.literals[0]].append((new_clause.literals[0], new_clause))
            assign(val, level, reason, trail, assert_lit, current_level, new_clause)
            prop_queue=deque([assert_lit])