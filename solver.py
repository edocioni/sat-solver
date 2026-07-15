def evaluate_clause(clause, assignments):
    unresolved = False
    for n in clause:
        if n > 0:
            desired_value = True
        else:
            desired_value = False
        if abs(n) in assignments:
            if assignments[abs(n)] == desired_value:
                return True
        else:
            unresolved = True
    
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
    
def unit_propagate_step(clauses, assignments):
    for clause in clauses:
        unresolved_literal=None
        unresolved_count=0
        satisfied=False
        for n in clause:
            desired_value=n>0
            if abs(n) in assignments:
                if assignments[abs(n)]==desired_value:
                    satisfied=True
                    break
            else:
                unresolved_count+=1
                unresolved_literal=n
        if not satisfied and unresolved_count==1:
            var=abs(unresolved_literal)
            value=unresolved_literal>0
            assignments[var]=value
            return var
    return None


def unit_propagate(clauses, assignments):
    trail=[]
    while True:
        var = unit_propagate_step(clauses, assignments)
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

def analyze_conflict(clauses, assignments):
    for clause in clauses:
        if evaluate_clause(clause, assignments)==False:
            learned_clause=[-n for n in clause]
            return learned_clause
    return None

def validate_solution(clauses, solution):
    for clause in clauses:
        clause_satisfied = False
        for n in clause:
            desired_value = n > 0
            if abs(n) in solution and solution[abs(n)] == desired_value:
                clause_satisfied = True
                break
        if not clause_satisfied:
            return False
    return True


def solve(clauses, assignments):
    formula_evaluation=evaluate_formula(clauses, assignments)

    if formula_evaluation==True:
        return assignments.copy()
    elif formula_evaluation==False:
        return None

    prop_trail=unit_propagate(clauses, assignments)
    if evaluate_formula(clauses, assignments)==False:
        learned_clause=analyze_conflict(clauses, assignments)
        clauses.append(learned_clause)
        for var in prop_trail:
            del assignments[var]
        return None

    var_to_assign=find_unassigned_variable(clauses, assignments)
    if var_to_assign is None:
        result=assignments.copy() if evaluate_formula(clauses, assignments) else None
        for var in prop_trail:
            del assignments[var]
        return result

    assignments[var_to_assign]=True
    result=solve(clauses, assignments)
    del assignments[var_to_assign]
    if result is not None:
        for var in prop_trail:
            del assignments[var]
        return result

    assignments[var_to_assign]=False
    result=solve(clauses, assignments)
    del assignments[var_to_assign]

    for var in prop_trail:
        del assignments[var]

    return result