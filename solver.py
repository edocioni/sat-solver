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
            return True
    return False

def unit_propagate(clauses, assignments):
    new_assignments=assignments.copy()
    while unit_propagate_step(clauses, new_assignments):
        pass
    return new_assignments

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
        for n in clause:
            if evaluate_clause(clause, assignments)==False:
                learned_clause=[n*-1 for n in clause]
                return learned_clause
    return None

def validate_solution(clauses, solution):
    for clause in clauses:
        clause_satisfied = False
        for n in clause:
            desired_value = n > 0
            if solution[abs(n)] == desired_value:
                clause_satisfied = True
                break
        if not clause_satisfied:
            return False
    return True

def solve(clauses, assignments):
    formula_evaluation=evaluate_formula(clauses, assignments)
    if formula_evaluation==True:
        return assignments
    elif formula_evaluation==False:
        return None
        
    new_assignments=assignments.copy()
    new_assignments=unit_propagate(clauses, new_assignments)
    
    if evaluate_formula(clauses, new_assignments)==False:
        learned_clause=analyze_conflict(clauses, new_assignments)
        clauses.append(learned_clause)
        return None

    var_to_assign=find_unassigned_variable(clauses, new_assignments)
    if var_to_assign is None:
        return new_assignments if evaluate_formula(clauses, new_assignments) else None

    assignments_true=new_assignments.copy()
    assignments_true[var_to_assign]=True
    result=solve(clauses, assignments_true)
    if result is not None:
        return result
        
    assignments_false=new_assignments.copy()
    assignments_false[var_to_assign]=False
    result=solve(clauses, assignments_false)
    if result is not None:
        return result
        
    return None