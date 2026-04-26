import networkx as nx
import re
from typing import Dict


def extract_constants(G: nx.DiGraph,
                      IN: Dict) -> Dict:
    """
    For each block, find variables that are
    assigned a constant value and that constant
    reaches this block.
    Returns dict: {node: {var: constant_value}}
    """
    const_map = {}

    for node in G.nodes:
        const_map[node] = {}
        label = G.nodes[node].get("label", "")
        lines = label.split("\n")

        for line in lines:
            if "=" not in line:
                continue
            parts = line.split("=", 1)
            lhs = parts[0].strip()
            rhs = parts[1].strip()

            # Clean type keywords from lhs
            lhs = re.sub(
                r'\b(int|float|char|double)\b', '', lhs
            ).strip()

            # Check if rhs is a pure constant
            if re.match(r'^\d+(\.\d+)?$', rhs):
                if lhs.isidentifier():
                    const_map[node][lhs] = rhs

    return const_map


def propagate_constants(G: nx.DiGraph,
                        IN: Dict) -> tuple:
    """
    Replace variable uses with their constant values
    where possible using Reaching Definitions (IN sets).
    """
    const_map = extract_constants(G, IN)
    changes = []

    for node in G.nodes:
        label = G.nodes[node].get("label", "")
        lines = label.split("\n")
        new_lines = []
        node_changed = False

        # Build constant env from IN reaching this block
        env = {}
        for pred in G.predecessors(node):
            for var, val in const_map[pred].items():
                env[var] = val

        for line in lines:
            new_line = line

            if "=" in line:
                parts = line.split("=", 1)
                lhs = parts[0].strip()
                rhs = parts[1].strip()

                # Replace variables in RHS with constants
                new_rhs = rhs
                for var, val in env.items():
                    # Replace whole word only
                    new_rhs = re.sub(
                        rf'\b{re.escape(var)}\b',
                        val, new_rhs
                    )

                if new_rhs != rhs:
                    new_line = f"{lhs} = {new_rhs}"
                    node_changed = True
                    changes.append(
                        f"Block {node}: "
                        f"'{line}' → '{new_line}'"
                    )

            new_lines.append(new_line)

        if node_changed:
            G.nodes[node]["label"] = "\n".join(new_lines)

    return G, changes


def print_constant_propagation(changes: list):
    print("\n" + "=" * 50)
    print("  CONSTANT PROPAGATION")
    print("=" * 50)

    if changes:
        print(f"\n✅ {len(changes)} propagation(s) done:\n")
        for c in changes:
            print(f"  ✓ {c}")
    else:
        print("\n  No constants to propagate.")