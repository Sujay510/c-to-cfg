# CFG Project  C to Control Flow Graph

Converts any C source code into a Control Flow Graph (CFG),
runs static analysis, applies optimizations, and provides
a web dashboard to visualize everything.



## What This Does

| Phase | What it does |
|-------|-------------|
| **Phase 1** | Parses C code and builds a CFG image |
| **Phase 2** | Static analysis  finds bugs in code |
| **Phase 3** | Optimizes CFG and generates optimized C code |
| **Bonus** | Web dashboard  use everything in browser |

## My Contribution

Built as part of the CS202 Programming Paradigms course at IIT Ropar (group of 5).
My specific contributions: CFG construction (cfg_builder.py), live variable analysis,
and reaching definitions dataflow passes.

## Project Structure

```
cfg_project/
├── main.py                          ← run from terminal
├── app.py                           ← run web dashboard
├── requirements.txt
├── samples/
│   └── sample.c                     ← your C code here
└── src/
    ├── parser.py                    ← C → AST
    ├── cfg_builder.py               ← AST → CFG
    ├── visualizer.py                ← CFG → PNG image
    ├── code_generator.py            ← CFG → optimized C code
    ├── analysis/
    │   ├── __init__.py
    │   ├── reaching_definitions.py  ← Phase 2
    │   └── live_variables.py        ← Phase 2
    └── optimization/
        ├── __init__.py
        ├── constant_folding.py      ← Phase 3
        ├── constant_propagation.py  ← Phase 3
        ├── dead_code_elimination.py ← Phase 3
        └── unreachable_code.py      ← Phase 3
```



## Requirements

- Python 3.10+
- Graphviz software
- Git



## Installation

### Step 1  Install Graphviz

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



### Step 2  Clone the Repo

```bash
git clone https://github.com/Sujay510/c-to-cfg
cd c-to-cfg
```



### Step 3  Create Virtual Environment

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

You should see `(venv)` in your terminal.



### Step 4  Install Dependencies

```bash
pip install -r requirements.txt
```

> Windows only  if matplotlib fails:
> ```powershell
> pip install matplotlib==3.9.2 --only-binary=:all:
> pip install pycparser networkx pydot streamlit
> ```



## Option A  Run from Terminal

Put your C code in `samples/sample.c` then:

**Windows**
```powershell
# Phase 1 only  builds CFG image
python main.py --phase 1

# Phase 2  CFG + static analysis
python main.py --phase 2

# Phase 3  CFG + analysis + optimizations
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

### Terminal Output Files

| File | What it is |
|------|-----------|
| `cfg_output.png` | Original CFG image |
| `cfg_optimized.png` | Optimized CFG image |
| `cfg_output.dot` | DOT source file |



## Option B  Run Web Dashboard (Streamlit)

No need to edit any files  just paste C code in the browser!

### Start the dashboard

**Windows**
```powershell
streamlit run app.py
```

**Linux / Mac**
```bash
streamlit run app.py
```

Opens automatically in your browser at:
```
http://localhost:8501
```

### Dashboard Features

| Feature | Description |
|---------|-------------|
| **Code Editor** | Paste any C code directly in browser |
| **Phase Selector** | Choose Phase 1, 2 or 3 from sidebar |
| **CFG Image** | View original CFG with download button |
| **Analysis Tables** | Reaching Defs + Live Vars with warnings |
| **Optimization Metrics** | See how many changes were applied |
| **Before vs After** | Side by side CFG comparison |
| **Optimized C Code** | View original vs optimized code side by side |
| **Download Buttons** | Download CFG images and optimized C file |


## Phase 1  C to CFG

Parses C source code and builds a Control Flow Graph.

**Supported C features:**

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
| `i++` / `i--` | ✅ |
| Arrays `arr[i]` | ✅ |
| Nested loops | ✅ |
| `#include` (auto removed) | ✅ |
| `/* */` and `//` comments | ✅ |



## Phase 2  Static Analysis

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



## Phase 3  Optimizations

Uses Phase 2 results to improve the CFG.

### Constant Folding
```c
// Before          After
int x = 3 + 5; →  int x = 8;
```

### Constant Propagation
```c
// Before              After
int x = 10;            int x = 10;
int y = x + 5;  →     int y = 15;
```

### Dead Code Elimination
```c
// Before          After
a = 6;         →  (removed  a never used again)
return b;          return b;
```

### Unreachable Code Removal
Removes CFG nodes with no path from START
using BFS/DFS traversal.



## Tech Stack

| Tool | Purpose |
|------|---------|
| **Python 3.10+** | Primary language |
| **pycparser** | Parse C code into AST |
| **NetworkX** | Graph data structure |
| **Graphviz** | Render CFG as PNG |
| **pydot** | Python → Graphviz bridge |
| **Streamlit** | Web dashboard |



## Troubleshooting

**`python` not recognized**
- Reinstall Python from python.org
- Check "Add python.exe to PATH" during install
- Restart terminal after installing

**`dot` not recognized**
- Add `C:\Program Files\Graphviz\bin` to PATH
- Restart terminal after adding

**venv activation error on Windows**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Parse error in C file**
- Parser auto-removes `#include`, `#define`, comments
- Check balanced `{}` braces in your C code
- Check the line number shown in the error

**matplotlib build fails**
```powershell
pip install matplotlib==3.9.2 --only-binary=:all:
```

**Streamlit not found**
```powershell
pip install streamlit
streamlit --version
```



## Roadmap

- [x] Phase 1  C to CFG
- [x] Phase 2  Static Analysis
- [x] Phase 3  Optimizations
- [x] Bonus  Web Dashboard (Streamlit)
