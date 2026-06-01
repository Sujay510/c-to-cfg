import networkx as nx
from typing import Dict, Set


def extract_gen_kill(G: nx.DiGraph):
    """
    For each block, compute:
    GEN  = set of variables defined in this block
    KILL = set of variables killed (re-defined) in this block
    """
    gen  = {}   # gen[node]  = set of var names defined here
    kill = {}   # kill[node] = set of var names killed here

    for node in G.nodes:
        label = G.nodes[node].get("label", "")
        lines = label.split("\n")

        block_gen  = set()
        block_kill = set()

        for line in lines:
            line = line.strip()

            # Detect assignments: "x = ..." or "x = 5"
            if "=" in line and not line.startswith("IF") \
               and not line.startswith("WHILE") \
               and not line.startswith("FOR"):
                var = line.split("=")[0].strip()
                # Remove type keywords if present
                var = var.replace("int", "").strip()
                var = var.replace("float", "").strip()
                var = var.replace("char", "").strip()
                if var and var.isidentifier():
                    block_kill.add(var)
                    block_gen.add(var)

        gen[node]  = block_gen
        kill[node] = block_kill

    return gen, kill


def reaching_definitions(G: nx.DiGraph):
    """
    Compute Reaching Definitions for all blocks.

    Forward analysis:
      OUT[B] = GEN[B] ∪ (IN[B] - KILL[B])
      IN[B]  = ∪ OUT[P] for all predecessors P
    """
    gen, kill = extract_gen_kill(G)

    # Initialize IN and OUT as empty sets
    IN  = {node: set() for node in G.nodes}
    OUT = {node: set() for node in G.nodes}

    changed = True
    iterations = 0

    while changed:
        changed = False
        iterations += 1

        for node in G.nodes:
            # IN[B] = union of OUT of all predecessors
            preds = list(G.predecessors(node))
            new_in = set()
            for p in preds:
                new_in |= OUT[p]

            # OUT[B] = GEN[B] ∪ (IN[B] - KILL[B])
            new_out = gen[node] | (new_in - kill[node])

            if new_in != IN[node] or new_out != OUT[node]:
                IN[node]  = new_in
                OUT[node] = new_out
                changed   = True

    print(f"Reaching Definitions converged in "
          f"{iterations} iterations.")
    return IN, OUT, gen, kill


def find_uninitialized(G: nx.DiGraph,
                       IN: Dict, OUT: Dict,
                       gen: Dict) -> list:
    """
    Detect variables used in a block that have
    no reaching definition — potentially uninitialized.
    """
    warnings = []

    for node in G.nodes:
        label = G.nodes[node].get("label", "")
        lines = label.split("\n")

        for line in lines:
            line = line.strip()

            # Look for usage on right side of assignment
            if "=" in line:
                rhs = line.split("=", 1)[1].strip()
                # Extract identifiers from rhs
                import re
                used_vars = re.findall(r'\b[a-zA-Z_]\w*\b',
                                       rhs)
                for var in used_vars:
                    # Skip keywords and function names
                    if var in ("int", "float", "char",
                               "return", "if", "while",
                               "for", "else"):
                        continue
                    # If var not in IN[node] → uninitialized
                    if var not in IN[node]:
                        warnings.append(
                            f"Block {node}: '{var}' "
                            f"may be uninitialized"
                        )

    return warnings


def print_reaching_definitions(G: nx.DiGraph,
                               IN: Dict,
                               OUT: Dict,
                               gen: Dict,
                               kill: Dict):
    print("\n" + "="*50)
    print("  REACHING DEFINITIONS ANALYSIS")
    print("="*50)

    for node in G.nodes:
        label = G.nodes[node].get("label", "")
        first_line = label.split("\n")[0]
        print(f"\nBlock {node}: {first_line}")
        print(f"  GEN  : {gen[node]  or '{}'}")
        print(f"  KILL : {kill[node] or '{}'}")
        print(f"  IN   : {IN[node]   or '{}'}")
        print(f"  OUT  : {OUT[node]  or '{}'}")

    warnings = find_uninitialized(G, IN, OUT, gen)
    if warnings:
        print("\n⚠️  UNINITIALIZED VARIABLE WARNINGS:")
        for w in warnings:
            print(f"  ⚠  {w}")
    else:
        print("\n✅ No uninitialized variables found.")