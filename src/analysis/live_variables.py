import networkx as nx
import re
from typing import Dict, Set


def extract_use_def(G: nx.DiGraph):
    """
    For each block compute:
    USE = variables used before being defined in this block
    DEF = variables defined in this block
    """
    use = {}
    defs = {}

    for node in G.nodes:
        label = G.nodes[node].get("label", "")
        lines = label.split("\n")

        block_use  = set()
        block_def  = set()

        KEYWORDS = {"int", "float", "char", "return",
                    "if", "while", "for", "else",
                    "break", "continue", "void",
                    "START", "END", "MERGE", "FUNCTION",
                    "RETURN", "WHILE", "FOR", "IF",
                    "CALL", "LOOP", "EXIT", "INIT",
                    "COND", "NEXT"}

        for line in lines:
            line = line.strip()

            if "=" in line and not line.startswith("IF") \
               and not line.startswith("WHILE") \
               and not line.startswith("FOR"):

                parts = line.split("=", 1)
                lhs = parts[0].strip()
                rhs = parts[1].strip() if len(parts) > 1 \
                    else ""

                # Clean lhs
                lhs_var = lhs.replace("int", "").strip()
                lhs_var = lhs_var.replace("float","").strip()
                lhs_var = lhs_var.replace("char", "").strip()

                # Variables used on rhs
                rhs_vars = re.findall(
                    r'\b[a-zA-Z_]\w*\b', rhs
                )
                for v in rhs_vars:
                    if v not in KEYWORDS \
                       and v not in block_def:
                        block_use.add(v)

                # Variable defined on lhs
                if lhs_var and lhs_var.isidentifier() \
                   and lhs_var not in KEYWORDS:
                    block_def.add(lhs_var)

            else:
                # Just a use (e.g. IF condition, RETURN)
                all_vars = re.findall(
                    r'\b[a-zA-Z_]\w*\b', line
                )
                for v in all_vars:
                    if v not in KEYWORDS \
                       and v not in block_def:
                        block_use.add(v)

        use[node]  = block_use
        defs[node] = block_def

    return use, defs


def live_variable_analysis(G: nx.DiGraph):
    """
    Compute Live Variables for all blocks.

    Backward analysis:
      IN[B]  = USE[B] ∪ (OUT[B] - DEF[B])
      OUT[B] = ∪ IN[S] for all successors S
    """
    use, defs = extract_use_def(G)

    IN  = {node: set() for node in G.nodes}
    OUT = {node: set() for node in G.nodes}

    changed = True
    iterations = 0

    while changed:
        changed = False
        iterations += 1

        # Backward — process in reverse order
        for node in reversed(list(G.nodes)):
            # OUT[B] = union of IN of all successors
            succs = list(G.successors(node))
            new_out = set()
            for s in succs:
                new_out |= IN[s]

            # IN[B] = USE[B] ∪ (OUT[B] - DEF[B])
            new_in = use[node] | (new_out - defs[node])

            if new_in != IN[node] or new_out != OUT[node]:
                IN[node]  = new_in
                OUT[node] = new_out
                changed   = True

    print(f"Live Variable Analysis converged in "
          f"{iterations} iterations.")
    return IN, OUT, use, defs


def find_dead_assignments(G: nx.DiGraph,
                          OUT: Dict,
                          defs: Dict) -> list:
    """
    If a variable is defined in a block but NOT
    live in OUT → it is a dead assignment.
    """
    dead = []

    for node in G.nodes:
        for var in defs[node]:
            if var not in OUT[node]:
                label = G.nodes[node].get("label","")
                first = label.split("\n")[0]
                dead.append(
                    f"Block {node} ({first}): "
                    f"'{var}' assigned but never used"
                    f" → Dead Assignment"
                )

    return dead


def print_live_variables(G: nx.DiGraph,
                         IN: Dict,
                         OUT: Dict,
                         use: Dict,
                         defs: Dict):
    print("\n" + "="*50)
    print("  LIVE VARIABLE ANALYSIS")
    print("="*50)

    for node in G.nodes:
        label = G.nodes[node].get("label", "")
        first_line = label.split("\n")[0]
        print(f"\nBlock {node}: {first_line}")
        print(f"  USE  : {use[node]  or '{}'}")
        print(f"  DEF  : {defs[node] or '{}'}")
        print(f"  IN   : {IN[node]   or '{}'}")
        print(f"  OUT  : {OUT[node]  or '{}'}")

    dead = find_dead_assignments(G, OUT, defs)
    if dead:
        print("\n⚠️  DEAD ASSIGNMENT WARNINGS:")
        for d in dead:
            print(f"  ✗  {d}")
    else:
        print("\n✅ No dead assignments found.")