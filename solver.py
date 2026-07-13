def valuta_clausola(clausola, assegnazioni):
    sospesa=False
    for n in clausola:
        if n>0:
            valore_desiderato=True
        else:
            valore_desiderato=False
        if abs(n) in assegnazioni:
            if assegnazioni[abs(n)]==valore_desiderato:
                return True
        else:
            sospesa=True
    
    if sospesa:
        return None
    else:
        return False

print(valuta_clausola([1, -2, 3], {2: False}))        
print(valuta_clausola([1, -2, 3], {1: False}))         
print(valuta_clausola([1, -2, 3], {1: False, 2: True, 3: False}))