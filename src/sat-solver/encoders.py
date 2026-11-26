import sys

def pigeonhole(n):
    def var(p, h):
        return p*n+h+1
    clauses=[[var(p, h) for h in range(n)] for p in range(n+1)]
    for h in range(n):
        for p in range(n+1):
            for q in range(p+1, n+1):
                clauses.append([-var(p, h), -var(q, h)])
    return clauses, (n+1)*n

def nqueens(n):
    def var(r, c):
        return r*n+c+1
    clauses=[[var(r, c) for c in range(n)] for r in range(n)]
    cells=[(r, c) for r in range(n) for c in range(n)]
    for i, (r1, c1) in enumerate(cells):
        for r2, c2 in cells[i+1:]:
            if r1==r2 or c1==c2 or abs(r1-r2)==abs(c1-c2):
                clauses.append([-var(r1, c1), -var(r2, c2)])
    return clauses, n*n

def graph_coloring(num_nodes, edges, k):
    def var(v, c):
        return v*k+c+1
    clauses=[[var(v, c) for c in range(k)] for v in range(num_nodes)]
    for u, v in edges:
        for c in range(k):
            clauses.append([-var(u, c), -var(v, c)])
    return clauses, num_nodes*k

def write_dimacs(clauses, numvars, path):
    with open(path, "w") as f:
        f.write(f"p cnf {numvars} {len(clauses)}\n")
        for clause in clauses:
            f.write(" ".join(map(str, clause))+" 0\n")

if __name__=="__main__":
    if len(sys.argv)<4 or sys.argv[1] not in ("pigeonhole", "nqueens"):
        print("Usage: python encoders.py <pigeonhole|nqueens> <n> <out.cnf>")
        sys.exit(1)
    n=int(sys.argv[2])
    if sys.argv[1]=="pigeonhole":
        clauses, numvars=pigeonhole(n)
    else:
        clauses, numvars=nqueens(n)
    write_dimacs(clauses, numvars, sys.argv[3])