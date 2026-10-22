# sat-solver

A modern, lightweight **SAT Solver built from scratch in Python**, evolving from basic backtracking paradigms to a complete **CDCL (Conflict-Driven Clause Learning)** engine.

This project demonstrates the practical implementation of core Boolean Satisfiability algorithms, benchmarked against structured DIMACS CNF planning instances (such as Hanoi Tower SAT encodings) and applied to classic CSP and planning problems including N-Queens and Graph Coloring.

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

## 📊 Benchmark & Performance (Bounded Model Checking)

The solver was benchmarked on planning instances (Hanoi Towers encoded into CNF). These benchmarks test the efficiency of **VSIDS**, **Phase Saving**, and **LBD Pruning** on deep search trees (up to 31 time-steps).

| Benchmark | Variables | Clauses | Conflicts | Parse Time | Solve Time (PyPy3) | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Hanoi 4 (15 steps)** | 718 | 4,934 | 3,805 | 0.076s | **0.84s** | SAT |
| **Hanoi 5 (31 steps)** | 1,931 | 14,468 | 59,262 | 0.079s | **9.37s** | SAT |

### ⚡ Execution Engines: CPython vs. PyPy3

Executing under **PyPy3 (JIT)** provides a significant speedup by compiling unit propagation and watching lists to native machine instructions:

| Benchmark | CPython Solve Time | PyPy3 JIT Solve Time | Speedup |
| :--- | :--- | :--- | :--- |
| **Hanoi 4** | 1.70s | **0.84s** | **2.0x** |
| **Hanoi 5** | 25.89s | **9.37s** | **2.8x** |

---

## 🛠️ Usage

### Running the Solver

Pass any standard DIMACS `.cnf` file directly from the command line:

```bash
python solver.py path/to/benchmark.cnf
```

### Output Format

```text
Problem: 1931 variables, 14468 clauses
conflicts:  59262
Parse time: 0.0791s
Solve time: 9.3707s
SATISFIABLE
True
```

### ⚡ Recommended: PyPy3

For deep search instances, executing under PyPy3 offers maximum performance:

```bash
pypy3 solver.py hanoi5.cnf
```

---

## 🧩 Applications & Reductions

This repository contains propositional reductions and encodings for logic and planning problems:

* **Bounded Model Checking / Planning:** Encodes temporal state transitions and disk placement rules (Hanoi Towers).
* **N-Queens Problem:** Generates non-attacking placement constraints for arbitrary $N$.
* **Graph Coloring:** Translates $k$-colorability constraints for arbitrary undirected graphs into SAT instances.

---

## 📜 License

Distributed under the MIT License. Feel free to use, modify, and extend!