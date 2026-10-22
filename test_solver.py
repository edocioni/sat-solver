import random
import pytest
from solver import solve_raw, parse_dimacs, solve
from encoders import pigeonhole, nqueens, graph_coloring, write_dimacs

def random_3sat(numvars, numclauses, rng):
    clauses=[]
    for _ in range(numclauses):
        vs=rng.sample(range(1, numvars+1), 3)
        clauses.append([v if rng.random()<0.5 else -v for v in vs])
    return clauses

def brute_force(clauses, numvars):
    for bits in range(1<<numvars):
        if all(any(bool((bits>>(abs(l)-1))&1)==(l>0) for l in c) for c in clauses):
            return True
    return False

def satisfies(clauses, val):
    return all(any(val[l]==1 for l in c) for c in clauses)

def test_empty_clause():
    assert solve_raw([[1, 2], []], 2) is None

def test_conflicting_units():
    assert solve_raw([[1], [-1]], 1) is None

def test_unit_chain_unsat():
    assert solve_raw([[1], [-1, 2], [-2, 3], [-3]], 3) is None

def test_tautology_ignored():
    result=solve_raw([[1, -1], [2]], 2)
    assert result is not None and result[2]==1

def test_no_clauses():
    assert solve_raw([], 3) is not None

def test_satlib_trailer(tmp_path):
    path=tmp_path/"a.cnf"
    path.write_text("p cnf 2 2\n1 2 0\n-1 2 0\n%\n0\n")
    clauses, numvars, has_empty=parse_dimacs(str(path), verbose=False)
    assert not has_empty
    assert solve(clauses, numvars, verbose=False) is not None

@pytest.mark.parametrize("seed", range(300))
def test_random_vs_brute_force(seed):
    rng=random.Random(seed)
    numvars=rng.randint(5, 14)
    clauses=random_3sat(numvars, int(numvars*4.26), rng)
    result=solve_raw(clauses, numvars)
    expected=brute_force(clauses, numvars)
    assert (result is not None)==expected
    if result is not None:
        assert satisfies(clauses, result)

@pytest.mark.parametrize("seed", range(40))
def test_random_vs_pysat(seed):
    pysat=pytest.importorskip("pysat.solvers")
    rng=random.Random(1000+seed)
    numvars=rng.randint(60, 120)
    clauses=random_3sat(numvars, int(numvars*4.26), rng)
    with pysat.Minisat22(bootstrap_with=clauses) as s:
        expected=s.solve()
    result=solve_raw(clauses, numvars)
    assert (result is not None)==expected
    if result is not None:
        assert satisfies(clauses, result)

@pytest.mark.parametrize("n", [2, 3, 4, 5, 6])
def test_pigeonhole_unsat(n):
    clauses, numvars=pigeonhole(n)
    assert solve_raw(clauses, numvars) is None

@pytest.mark.parametrize("n,expected", [(2, False), (3, False), (4, True), (6, True), (8, True)])
def test_nqueens(n, expected):
    clauses, numvars=nqueens(n)
    result=solve_raw(clauses, numvars)
    assert (result is not None)==expected
    if result is not None:
        assert satisfies(clauses, result)

def test_graph_coloring():
    edges=[(u, v) for u in range(4) for v in range(u+1, 4)]
    clauses, numvars=graph_coloring(4, edges, 3)
    assert solve_raw(clauses, numvars) is None
    clauses, numvars=graph_coloring(4, edges, 4)
    assert solve_raw(clauses, numvars) is not None

def test_dimacs_roundtrip(tmp_path):
    clauses, numvars=pigeonhole(4)
    path=tmp_path/"php.cnf"
    write_dimacs(clauses, numvars, str(path))
    parsed, nv, has_empty=parse_dimacs(str(path), verbose=False)
    assert nv==numvars and not has_empty
    assert solve(parsed, nv, verbose=False) is None