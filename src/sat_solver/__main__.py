import sys
import time

from .solver import parse_dimacs, solve, validate_solution


def main():
    if len(sys.argv) < 2:
        print("Usage: sat-solver <path_to_dimacs.cnf>")
        return 1

    filename = sys.argv[1]
    start = time.perf_counter()
    clauses, numvars, has_empty = parse_dimacs(filename)
    originals = list(clauses)
    parse_time = time.perf_counter() - start

    start = time.perf_counter()
    result = None if has_empty else solve(clauses, numvars)
    solve_time = time.perf_counter() - start

    print(f"Parse time: {parse_time:.4f}s")
    print(f"Solve time: {solve_time:.4f}s")
    if result is None:
        print("UNSATISFIABLE")
    else:
        print("SATISFIABLE")
        print(validate_solution(originals, result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
