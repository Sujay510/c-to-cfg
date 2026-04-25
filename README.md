# CFG Project — C to Control Flow Graph

Converts any C source code into a Control Flow Graph (CFG)
and runs static analysis on it.

---

## What This Does

- **Phase 1** — Parses C code and builds a CFG
- **Phase 2** — Runs static analysis on the CFG
  - Reaching Definitions Analysis
  - Live Variable Analysis

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
    └── analysis/
        ├── reaching_definitions.py  ← Phase 2
        └── live_variables.py        ← Phase 2
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

Switch to Phase 2 branch:
```bash
git checkout phase2/static-analysis
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

1. Put your C code in `samples/sample.c`
2. Run:

**Windows**
```powershell
python main.py
```

**Linux / Mac**
```bash
python3 main.py
```

---

## Output

### Terminal Output
```
==================================================
  PHASE 1: C TO CFG
==================================================
Parsing sample.c ...
Building CFG ...

==================================================
  PHASE 2: STATIC ANALYSIS
==================================================

==================================================
  REACHING DEFINITIONS ANALYSIS
==================================================

Block 0: START
  GEN  : {}
  KILL : {}
  IN   : {}
  OUT  : {}

Block 4: FUNCTION main
  GEN  : {'a', 'b'}
  KILL : {'a', 'b'}
  IN   : {}
  OUT  : {'a', 'b'}

✅ No uninitialized variables found.

==================================================
  LIVE VARIABLE ANALYSIS
==================================================

Block 4: FUNCTION main
  USE  : {}
  DEF  : {'a', 'b'}
  IN   : {'a', 'b'}
  OUT  : {'a', 'b'}

⚠️  DEAD ASSIGNMENT WARNINGS:
  ✗  Block 4: 'b' assigned but never used
```

### Image Output
- `cfg_output.png` — CFG image, opens automatically

---

## Phase 2 — Static Analysis Explained

### Reaching Definitions
Tracks which variable assignments can reach each
point in the program.

```
OUT[B] = GEN[B] ∪ (IN[B] - KILL[B])
IN[B]  = ∪ OUT[P]  for all predecessors P
```

Detects: **uninitialized variables**

---

### Live Variable Analysis
Tracks whether a variable's value will be
used in the future.

```
IN[B]  = USE[B] ∪ (OUT[B] - DEF[B])
OUT[B] = ∪ IN[S]  for all successors S
```

Detects: **dead assignments** (assigned but never used)

---

## Supported C Features

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
- [ ] Phase 3 — Optimizations
