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

print(evaluate_clause([1, -2, 3], {2: False}))        
print(evaluate_clause([1, -2, 3], {1: False}))         
print(evaluate_clause([1, -2, 3], {1: False, 2: True, 3: False}))