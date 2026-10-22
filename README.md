# sat-solver

A modern, lightweight **SAT Solver built from scratch in Python**, evolving from basic backtracking paradigms to a complete **CDCL (Conflict-Driven Clause Learning)** engine.

This project demonstrates the practical implementation of core Boolean Satisfiability algorithms, benchmarked against structured DIMACS CNF benchmarks (such as the Hanoi Tower SAT encodings) and applied to classic CSP problems including Sudoku, N-Queens, and Graph Coloring.

---

## 🚀 Key Features & Algorithmic Highlights

The solver implements a modern CDCL architecture optimized for Python 3:

* **Two-Watched Literals (2WL):** Efficient unit propagation with in-place pointer updating, avoiding redundant scans over satisfied clauses.
* **1UIP Conflict Analysis & Backjumping:** Identifies the First Unique Implication Point to learn non-redundant clauses and backjumps non-chronologically up the decision tree.
* **VSIDS Decision Heuristic with Max-Heap:** Variable State Independent Decaying Sum driven by a dynamic `heapq` Priority Queue for $O(1)$ variable selection.
* **Phase Saving:** Remembers the last assigned polarity for each variable, guiding search towards previously consistent sub-states.
* **LBD-Based Clause Database Reduction:** Measures **Literal Block Distance** (Glucose-style) to periodically prune low-quality learned clauses.
* **Fast Trail Unrolling:** $O(\text{unassigned})$ backtracking utilizing CPython's fast stack `.pop()` operations rather than full-array filtering.
* **Low Memory Footprint:** Built with lightweight `@dataclass(slots=True)` containers to minimize CPython attribute lookup overhead.

---

## 📊 Benchmark & Optimization Progress

The solver was benchmarked on challenging planning instances from SATLIB (Hanoi Towers encoded into CNF). Optimization passes reduced execution time by over **60%** while cutting conflict counts by nearly half.

### Hanoi 4 (`hanoi4.cnf` - 718 variables, 4,934 clauses)

| Version | Solve Time | Conflicts | Speedup |
| :--- | :--- | :--- | :--- |
| **Initial CDCL (Naive)** | 4.41s | 7,004 | Baseline |
| **Phase 1 (Heap + Phase Saving)** | 2.58s | 6,393 | +41.5% |
| **Phase 2 (In-Place 2WL + Trail Pop)** | **1.70s** | **3,805** | **+61.4%** |

### Hanoi 5 (`hanoi5.cnf` - 1,931 variables, 14,468 clauses)

| Version | Solve Time | Conflicts | Speedup |
| :--- | :--- | :--- | :--- |
| **Phase 1 CDCL** | 42.00s | 95,414 | Baseline |
| **Final Optimized Engine** | **25.89s** | **59,262** | **+38.3%** |

---

## 🛠️ Usage

### Running the Solver

Pass any standard DIMACS `.cnf` file directly from the command line:

```bash
python solver.py path/to/benchmark.cnf
```

### Output Format

```text
Problem: 718 variables, 4934 clauses
conflicts:  3805
Parse time: 0.0135s
Solve time: 1.7030s
SATISFIABLE
True
```

### ⚡ Performance Pro-Tip: PyPy3

Since the codebase uses pure Python without external C-extensions, executing it under **PyPy3 (JIT)** provides a massive performance boost (often $5\times$ to $10\times$ speedup):

```bash
pypy3 solver.py hanoi5.cnf
```

---

## 🧩 Applications & Reductions

This repository also contains propositional reductions for common NP-complete and Constraint Satisfaction Problems (CSP):

* **Sudoku Solver:** Encodes $9 \times 9$ board rules (cell, row, column, and block constraints) into CNF.
* **N-Queens Problem:** Generates non-attacking placement constraints for arbitrary $N$.
* **Graph Coloring:** Translates $k$-colorability constraints for arbitrary undirected graphs into SAT instances.

---

## 📜 License

Distributed under the MIT License. Feel free to use, modify, and extend!