from dataclasses import dataclass

@dataclass
class Assignment:
    value: bool
    level: int
    antecedent: list[int] = None

def evaluate_clause(clause, assignments):
    unresolved=False
    for n in clause:
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

def evaluate_formula(clauses, assignments):
    unresolved=False
    for clause in clauses:
        if evaluate_clause(clause, assignments)==False:
            return False
        elif evaluate_clause(clause, assignments)==None:
            unresolved=True
    if unresolved==True:
        return None
    else:
        return True
        
        
def find_unassigned_variable(clauses, assignments):
    for clause in clauses:
        for n in clause:
            if abs(n) not in assignments:
                return abs(n)
    return None
    
def unit_propagate_step(clauses, assignments, current_level):
    for clause in clauses:
        unresolved_literal=None
        unresolved_count=0
        satisfied=False
        for n in clause:
            desired_value=n>0
            if abs(n) in assignments:
                if assignments[abs(n)].value==desired_value:
                    satisfied=True
                    break
            else:
                unresolved_count+=1
                unresolved_literal=n
        if not satisfied and unresolved_count==1:
            var=abs(unresolved_literal)
            value=unresolved_literal>0
            assignments[var]=Assignment(value=value, level=current_level, antecedent=clause)
            return var
    return None


def unit_propagate(clauses, assignments, current_level):
    trail=[]
    while True:
        var = unit_propagate_step(clauses, assignments, current_level)
        if var is None:
            break
        trail.append(var)
    return trail
    
def parse_dimacs(filename):
    clauses=[]
    current_clause=[]
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
                        clauses.append(current_clause)
                        current_clause=[]
                else:
                    current_clause.append(val)
    return clauses    

def validate_solution(clauses, solution):
    for clause in clauses:
        clause_satisfied = False
        for n in clause:
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
        for n in clause:
            var=abs(n)
            if var not in assignments:
                if var not in variable_frequency:
                    variable_frequency[var]=0
                variable_frequency[var]+=1
    if not variable_frequency:
        return None
    max_var=max(variable_frequency, key=variable_frequency.get)
    return max_var

def analyze_conflict(clauses, assignments, current_level, prop_trail):
    conflict_clause=None
    for clause in clauses:
        if evaluate_clause(clause,assignments)==False:
            conflict_clause=clause
            break
    if conflict_clause is None:
        return None
    learned_clause = list(conflict_clause)
    decision_var=None
    for var,asign in assignments.items():
        if asign.level==current_level and asign.antecedent is None:
            decision_var=var
            break
    if decision_var is not None:
        assignments_order=[decision_var]+prop_trail
    else:
        assignments_order=list(prop_trail)
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
    
        antecedent=assignments[var_to_resolve].antecedent
        resolved_set=set(learned_clause) | set(antecedent)
        resolved_set.discard(var_to_resolve)
        resolved_set.discard(-var_to_resolve)
        learned_clause=list(resolved_set)
    return learned_clause
    
def solve(clauses, assignments, current_level=0):
    formula_evaluation=evaluate_formula(clauses, assignments)

    if formula_evaluation==True:
        return assignments.copy()
    elif formula_evaluation==False:
        return None

    prop_trail=unit_propagate(clauses, assignments, current_level)
    if evaluate_formula(clauses, assignments)==False:
        learned_clause=analyze_conflict(clauses, assignments, current_level, prop_trail)
        if learned_clause is not None:
            clauses.append(learned_clause)
        for var in prop_trail:
            del assignments[var]
        return None

    var_to_assign=choose_variable_heuristic(clauses, assignments)
    if var_to_assign is None:
        var_to_assign=find_unassigned_variable(clauses, assignments)
    if var_to_assign is None:
        result=assignments.copy() if evaluate_formula(clauses, assignments) else None
        for var in prop_trail:
            del assignments[var]
        return result

    nuovo_livello=current_level+1
    assignments[var_to_assign]=Assignment(value=True, level=nuovo_livello, antecedent=None)
    result=solve(clauses, assignments, nuovo_livello)
    del assignments[var_to_assign]
    if result is not None:
        for var in prop_trail:
            del assignments[var]
        return result

    assignments[var_to_assign] = Assignment(value=False, level=nuovo_livello, antecedent=None)
    result=solve(clauses, assignments, nuovo_livello)
    del assignments[var_to_assign]

    for var in prop_trail:
        del assignments[var]

    return result