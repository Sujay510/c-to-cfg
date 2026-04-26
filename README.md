# CFG Project — C to Control Flow Graph

Converts any C source code into a Control Flow Graph (CFG),
runs static analysis, and applies optimizations.

---

## What This Does

- **Phase 1** — Parses C code and builds a CFG
- **Phase 2** — Runs static analysis on the CFG
  - Reaching Definitions Analysis
  - Live Variable Analysis
- **Phase 3** — Applies optimizations on the CFG
  - Constant Folding
  - Constant Propagation
  - Dead Code Elimination
  - Unreachable Code Removal

---

## Project Structure

```
cfg_project/
├── main.py                          ← run this
├── requirements.txt
├── samples/
│   └── sample.c                     ← your C code here
└── src/
    ├── parser.py                    ← C → AST
    ├── cfg_builder.py               ← AST → CFG
    ├── visualizer.py                ← CFG → PNG
    ├── analysis/
    │   ├── reaching_definitions.py  ← Phase 2
    │   └── live_variables.py        ← Phase 2
    └── optimization/
        ├── constant_folding.py      ← Phase 3
        ├── constant_propagation.py  ← Phase 3
        ├── dead_code_elimination.py ← Phase 3
        └── unreachable_code.py      ← Phase 3
```

---

## Requirements

- Python 3.10+
- Graphviz (software)
- Git

---

## Installation

### Step 1 — Install Graphviz

**Windows**
```powershell
winget install graphviz
```
After installing, add `C:\Program Files\Graphviz\bin`
to your system PATH and restart your terminal.

**Linux**
```bash
sudo apt install graphviz -y
```

**Mac**
```bash
brew install graphviz
```

Verify:
```bash
dot -version
```

---

### Step 2 — Clone the Repo

```bash
git clone https://github.com/YOUR_USERNAME/cfg-project.git
cd cfg-project
```

Switch to Phase 3 branch:
```bash
git checkout phase3/optimizations
```

---

### Step 3 — Create Virtual Environment

**Windows**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

> If activation fails run this first:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

**Linux / Mac**
```bash
python3 -m venv venv
source venv/bin/activate
```

---

### Step 4 — Install Dependencies

```bash
pip install -r requirements.txt
```

> Windows only — if matplotlib fails:
> ```powershell
> pip install matplotlib==3.9.2 --only-binary=:all:
> ```

---

## How to Run

Put your C code in `samples/sample.c` then run:

### Run specific phase

**Windows**
```powershell
# Phase 1 only — builds and shows CFG
python main.py --phase 1

# Phase 2 only — CFG + static analysis
python main.py --phase 2

# Phase 3 only — CFG + analysis + optimizations
python main.py --phase 3

# All phases together
python main.py
```

**Linux / Mac**
```bash
python3 main.py --phase 1
python3 main.py --phase 2
python3 main.py --phase 3
python3 main.py
```

---

## Output Files

| File | Created by | What it shows |
|------|-----------|---------------|
| `cfg_output.png` | Phase 1 | Original CFG |
| `cfg_optimized.png` | Phase 3 | Optimized CFG |

Both files open automatically after running.

---

## Phase 1 — C to CFG

Parses C source code and builds a Control Flow Graph.

**What it handles:**

| Feature | Status |
|---------|--------|
| `if / else` | ✅ |
| `for` loop | ✅ |
| `while` loop | ✅ |
| `do while` loop | ✅ |
| `switch / case` | ✅ |
| Multiple functions | ✅ |
| Function calls | ✅ |
| `break / continue` | ✅ |
| `#include` (auto removed) | ✅ |
| `/* */` and `//` comments | ✅ |

**Example output — CFG image:**
```
          START
         /     \
  FUNCTION foo  FUNCTION main
       |              |
  RETURN x+1      a = 5
       |           b = a + 2
   END foo              |
                   IF (b > 5)
                  /          \
              True            False
           b=foo(b)         b=(b-1)
                 \          /
                   MERGE
                     |
                  FOR INIT ...
```

---

## Phase 2 — Static Analysis

Analyzes the CFG without running the code.

### Reaching Definitions
Tracks which variable assignments can reach
each point in the program.

```
OUT[B] = GEN[B] ∪ (IN[B] - KILL[B])
IN[B]  = ∪ OUT[P]  for all predecessors P
```

Detects: **uninitialized variables**

### Live Variable Analysis
Tracks whether a variable's current value
will be used in the future.

```
IN[B]  = USE[B] ∪ (OUT[B] - DEF[B])
OUT[B] = ∪ IN[S]  for all successors S
```

Detects: **dead assignments**

**Example terminal output:**
```
==================================================
  REACHING DEFINITIONS ANALYSIS
==================================================

Block 4: FUNCTION main
  GEN  : {'a', 'b'}
  KILL : {'a', 'b'}
  IN   : {}
  OUT  : {'a', 'b'}

✅ No uninitialized variables found.

==================================================
  LIVE VARIABLE ANALYSIS
==================================================

⚠️  DEAD ASSIGNMENT WARNINGS:
  ✗  Block 4: 'a' assigned but never used
```

---

## Phase 3 — Optimizations

Uses Phase 2 results to improve the CFG.

### 1. Constant Folding
Evaluates constant expressions at compile time.

```c
// Before
int x = 3 + 5;

// After
int x = 8;
```

### 2. Constant Propagation
Replaces variables with their constant values
where possible.

```c
// Before
int x = 10;
int y = x + 5;

// After
int x = 10;
int y = 10 + 5;  → then folded → int y = 15;
```

### 3. Dead Code Elimination
Removes assignments to variables that are
never used again (uses Live Variable Analysis).

```c
// Before
a = 6;      ← a never used after this
return b;

// After
return b;   ← a=6 removed
```

### 4. Unreachable Code Removal
Removes CFG nodes that have no path from START
(detected via BFS/DFS traversal).

```c
// Before
return x;
int y = 5;   ← never reached

// After
return x;    ← y=5 block removed
```

**Example terminal output:**
```
==================================================
  PHASE 3: OPTIMIZATIONS
==================================================

==================================================
  CONSTANT FOLDING
==================================================
✅ 1 expression(s) folded:
  ✓ Block 4: 'b = a + 2' → 'b = 7'

==================================================
  CONSTANT PROPAGATION
==================================================
  No constants to propagate.

==================================================
  DEAD CODE ELIMINATION
==================================================
✅ 1 dead assignment(s) removed:
  ✗ Block 14: removed 'a = 6' — 'a' is dead

==================================================
  UNREACHABLE CODE REMOVAL
==================================================
  No unreachable code found.

==================================================
  TOTAL OPTIMIZATIONS APPLIED: 2
==================================================
```

---

## Tech Stack

| Tool | Purpose |
|------|---------|
| **Python 3.10+** | Primary language |
| **pycparser** | Parse C code into AST |
| **NetworkX** | Graph data structure |
| **Graphviz** | Render CFG as PNG |
| **pydot** | Python → Graphviz bridge |

---

## Roadmap

- [x] Phase 1 — C to CFG
- [x] Phase 2 — Static Analysis
- [x] Phase 3 — Optimizations
- [ ] Bonus — Web Dashboard (Streamlit/Flask)
