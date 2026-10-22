import sys
import time
from collections import deque
from dataclasses import dataclass
from typing import Optional

@dataclass(eq=False)
class Clause:
    literals:list[int]
    watch1:int=0
    watch2:int=1

@dataclass
class Assignment:
    value: bool
    level: int
    antecedent: Optional[Clause] = None
    
def evaluate_clause(clause, assignments):
    unresolved=False
    for n in clause.literals:
        desired_value=n>0
        if abs(n) in assignments:
            if assignments[abs(n)].value==desired_value:
                return True
        else:
            unresolved=True
    
    if unresolved:
        return None
    else:
        return False

def find_unassigned_variable(clauses, assignments):
    for clause in clauses:
        for n in clause.literals:
            if abs(n) not in assignments:
                return abs(n)
    return None
    
def init_watches(clauses, numvars):
    watches={i: [] for i in range(-numvars, numvars+1) if i!=0}
    for clause in clauses:
        if len(clause.literals)>=1:
            watches[clause.literals[clause.watch1]].append(clause)
        if len(clause.literals)>=2:
            watches[clause.literals[clause.watch2]].append(clause)
        else:
            clause.watch2=0
    return watches

def unit_propagate(watches, assignments, current_level, prop_queue):
    while prop_queue:
        p=prop_queue.popleft()
        false_lit=-p
        for clause in list(watches[false_lit]):
            if clause.literals[clause.watch1]==false_lit:
                other_watch_index=clause.watch2
            else:
                other_watch_index=clause.watch1
            other_lit=clause.literals[other_watch_index]
            if abs(other_lit) in assignments and assignments[abs(other_lit)].value==(other_lit>0):
                continue
            found_new_watch=False
            for k in range(len(clause.literals)):
                lit_k=clause.literals[k]
                if k!=other_watch_index:
                    if abs(lit_k) not in assignments or assignments[abs(lit_k)].value==(lit_k>0):
                        if clause.literals[clause.watch1]==false_lit:
                            clause.watch1=k
                        else:
                            clause.watch2=k
                        watches[lit_k].append(clause)
                        watches[false_lit].remove(clause)
                        found_new_watch=True
                        break
            if not found_new_watch:
                if abs(other_lit) not in assignments:
                    assignments[abs(other_lit)]=Assignment(value=(other_lit>0), level=current_level, antecedent=clause)
                    prop_queue.append(other_lit)
                else:
                    return clause
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
            desired_value = n > 0
            if abs(n) in solution and solution[abs(n)].value == desired_value:
                clause_satisfied = True
                break
        if not clause_satisfied:
            return False
    return True

def choose_variable_heuristic(clauses, assignments):
    variable_frequency={}
    for clause in clauses:
        if evaluate_clause(clause, assignments)==True:
            continue
        for n in clause.literals:
            var=abs(n)
            if var not in assignments:
                if var not in variable_frequency:
                    variable_frequency[var]=0
                variable_frequency[var]+=1
    if not variable_frequency:
        return None
    max_var=max(variable_frequency, key=variable_frequency.get)
    return max_var

def analyze_conflict(conflict_clause, assignments, current_level, assignment_list):
    if conflict_clause is None:
        return None
    learned_clause = list(conflict_clause.literals)
    # assignment_list e' gia' in ordine di assegnamento (decisione per prima)
    assignments_order=[v for v in assignment_list if v in assignments]
    while True:
        current_level_literals=[]
        for literal in learned_clause:
            var=abs(literal)
            if assignments[var].level==current_level:
                current_level_literals.append(literal)
        if len(current_level_literals)<=1:
            break
        var_to_resolve=None
        for var in reversed(assignments_order):
            if var in [abs(x) for x in learned_clause]:
                var_to_resolve=var
                break
        if var_to_resolve is None:
            break
        antecedent=assignments[var_to_resolve].antecedent
        if antecedent is None:
            break   
        resolved_literal=[lit for lit in learned_clause if abs(lit)==var_to_resolve][0]
        learned_clause=set(learned_clause) | set(antecedent.literals)
        learned_clause.discard(resolved_literal)
        learned_clause.discard(-resolved_literal)
        learned_clause=list(learned_clause)
    # i letterali di livello 0 sono sempre falsi, inutili nella clausola appresa
    learned_clause=[lit for lit in learned_clause if assignments[abs(lit)].level>0]
    levels=sorted(set(assignments[abs(lit)].level for lit in learned_clause), reverse=True)
    backjump_level=levels[1] if len(levels)>1 else 0
    return learned_clause, backjump_level

def solve(clauses, assignments, numvars, current_level=0):
    watches=init_watches(clauses, numvars)
    prop_queue=deque()
    for clause in clauses:
        if len(clause.literals)==1:
            unit_lit=clause.literals[0]
            var=abs(unit_lit)
            if var not in assignments:
                assignments[var]=Assignment(value=(unit_lit>0), level=0, antecedent=clause)
                prop_queue.append(unit_lit)
    conflict_clause=unit_propagate(watches, assignments, 0, prop_queue)
    if conflict_clause is not None:
        return None
    activity={v: 0.0 for v in range(1, numvars+1)}
    for clause in clauses:
        for n in clause.literals:
            activity[abs(n)]+=1.0
    var_inc=1.0
    decay=0.95
    while True:
        unassigned=[v for v in range(1, numvars+1) if v not in assignments]
        if not unassigned:
            return assignments.copy()
        var_to_assign=max(unassigned, key=activity.get)
        current_level+=1
        assignments[var_to_assign]=Assignment(value=True, level=current_level, antecedent=None)
        prop_queue=deque([var_to_assign])
        while True:
            conflict_clause=unit_propagate(watches, assignments, current_level, prop_queue)
            if conflict_clause is None:
                break
            if current_level==0:
                return None
            assignments_list=[v for v in assignments if assignments[v].level==current_level]
            result=analyze_conflict(conflict_clause, assignments, current_level, assignments_list)
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
            uip_lits=[lit for lit in learned_clause if assignments[abs(lit)].level==current_level]
            assert len(uip_lits)==1
            assert_lit=uip_lits[0]
            rest=[lit for lit in learned_clause if lit!=assert_lit]
            rest.sort(key=lambda lit: assignments[abs(lit)].level, reverse=True)
            learned_clause=[assert_lit]+rest
            for var in list(assignments.keys()):
                if assignments[var].level>backjump_level:
                    del assignments[var]
            current_level=backjump_level
            new_clause=Clause(literals=learned_clause)
            clauses.append(new_clause)
            if len(new_clause.literals)>=1:
                watches[new_clause.literals[new_clause.watch1]].append(new_clause)
            if len(new_clause.literals)>=2:
                watches[new_clause.literals[new_clause.watch2]].append(new_clause)
            else:
                new_clause.watch2=0
            var_assert=abs(assert_lit)
            assignments[var_assert]=Assignment(value=(assert_lit>0), level=current_level, antecedent=new_clause)
            prop_queue=deque([assert_lit])
