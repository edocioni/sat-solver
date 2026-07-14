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
            for abs(n) not in assignments:
                return abs(n)
    return None
    
def solve(clauses, assignments):
    if evaluate_formula(clauses, assignments)==True:
        return assignments
    elif evaluate_formula(clauses, assignments)==False:
        return None
    else:
        new_assignments=assignments.copy()
        new_assignments[find_unassigned_variable(clauses, assignments)]=True
        result=(solve(clauses, new_assignments))
        if(result!=None):
            return result
        else:
            new_assignments=assignments.copy()
            new_assignments[find_unassigned_variable(clauses, assignments)]=False
            result=solve(clauses, new_assignments)
            if(result!=None):
                return result
            else:
                return None