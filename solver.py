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
    return clauses,numvars

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
    assignments_order=[v for v in assignments_order if v in assignments]
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
        learned_clause=set(learned_clause) | set(antecedent)
        learned_clause.discard(resolved_literal)
        learned_clause.discard(-resolved_literal)
        learned_clause=list(learned_clause)
    levels=sorted(set(assignments[abs(lit)].level for lit in learned_clause if abs(lit) in assignments), reverse=True)
    backjump_level=levels[1] if len(levels)>1 else 0
    return learned_clause, backjump_level


def solve(clauses, assignments, numvars, current_level=0):
    formula_evaluation=evaluate_formula(clauses, assignments)

    if formula_evaluation==True:
        for var_num in range(1, numvars+1):
            if var_num not in assignments:
                assignments[var_num]=Assignment(value=True, level=-1, antecedent=None)
        return assignments.copy()
    elif formula_evaluation==False:
        return None

    prop_trail=unit_propagate(clauses, assignments, current_level)

    if evaluate_formula(clauses, assignments)==False:
        assignments_list=[v for v in assignments if assignments[v].level==current_level]
        result=analyze_conflict(clauses, assignments, current_level, assignments_list)

        if result is not None:
            learned_clause, backjump_level=result
            clauses.append(learned_clause)
            for var in list(assignments.keys()):
                if assignments[var].level>backjump_level:
                    del assignments[var]
            return solve(clauses, assignments, numvars, backjump_level)

        for var in prop_trail:
            if var in assignments:
                del assignments[var]
        return None

    var_to_assign=choose_variable_heuristic(clauses, assignments)
    if var_to_assign is None:
        var_to_assign=find_unassigned_variable(clauses, assignments)
    if var_to_assign is None:
        result=assignments.copy() if evaluate_formula(clauses, assignments) else None
        for var in prop_trail:
            if var in assignments:
                del assignments[var]
        return result

    new_level=current_level+1

    assignments[var_to_assign]=Assignment(value=True, level=new_level, antecedent=None)
    result=solve(clauses, assignments, numvars, new_level)
    if var_to_assign in assignments:
        del assignments[var_to_assign]
    if result is not None:
        for var in prop_trail:
            if var in assignments:
                del assignments[var]
        return result

    assignments[var_to_assign]=Assignment(value=False, level=new_level, antecedent=None)
    result=solve(clauses, assignments, numvars, new_level)
    if var_to_assign in assignments:
        del assignments[var_to_assign]

    for var in prop_trail:
        if var in assignments:
            del assignments[var]

    return result

def solve_updated(clauses, assignments, numvars, current_level=0):
    while True:
        unit_propagate(clauses, assignments, current_level)
        formula_evaluation=evaluate_formula(clauses, assignments)
        if formula_evaluation==True:
            for var_num in range(1, numvars+1):
                if var_num not in assignments:
                    assignments[var_num]=Assignment(value=True, level=-1, antecedent=None)
            return assignments.copy()
        elif formula_evaluation==False:
            if current_level==0:
                return None
            assignments_list=[v for v in assignments if assignments[v].level==current_level]
            result=analyze_conflict(clauses, assignments, current_level, assignments_list)
            if result is not None:
                learned_clause, backjump_level=result
                clauses.append(learned_clause)
                for var in list(assignments.keys()):
                    if assignments[var].level>backjump_level:
                        del assignments[var]
                current_level=backjump_level
                continue
        var_to_assign=choose_variable_heuristic(clauses, assignments)
        if var_to_assign is None:
            var_to_assign=find_unassigned_variable(clauses, assignments)
        if var_to_assign is None:
            return None
        current_level+=1
        assignments[var_to_assign]=Assignment(value=True, level=current_level, antecedent=None)
            

clauses, numvars = parse_dimacs("uf20-0999.cnf")
result = solve_updated(clauses, {}, numvars)
if result is None:
    print("UNSATISFIABLE")
else:
    print("SATISFIABLE")
    print(validate_solution(clauses, result))