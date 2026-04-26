import networkx as nx
import re
from typing import Dict


def dead_code_elimination(G: nx.DiGraph,
                          OUT_lv: Dict) -> tuple:
    changes = []

    KEYWORDS = {
        "int", "float", "char", "void", "return",
        "if", "while", "for", "else", "break",
        "continue", "START", "END", "MERGE",
        "FUNCTION", "WHILE", "FOR", "IF", "CALL",
        "LOOP", "EXIT", "INIT", "COND", "NEXT",
        "RETURN", "BREAK", "CONTINUE", "DO"
    }

    SKIP_PREFIXES = (
        "IF", "WHILE", "FOR", "RETURN",
        "BREAK", "CONTINUE", "CALL",
        "FUNCTION", "END", "START",
        "MERGE", "LOOP", "DO"
    )

    for node in G.nodes:
        label = G.nodes[node].get("label", "")
        lines = label.split("\n")
        new_lines = []
        live_out = OUT_lv.get(node, set())

        for line in lines:
            stripped = line.strip()
            should_keep = True

            # Only check lines with assignment
            if "=" in stripped and not any(
                stripped.startswith(k)
                for k in SKIP_PREFIXES
            ):
                parts = stripped.split("=", 1)
                lhs = parts[0].strip()

                # Remove type keywords
                lhs_var = re.sub(
                    r'\b(int|float|char|double|long)\b',
                    '', lhs
                ).strip()

                # Clean array brackets
                lhs_var = re.sub(r'\[.*?\]', '', lhs_var).strip()

                if lhs_var and \
                   lhs_var.isidentifier() and \
                   lhs_var not in KEYWORDS and \
                   lhs_var not in live_out:
                    should_keep = False
                    changes.append(
                        f"Block {node}: "
                        f"removed '{stripped}' "
                        f"— '{lhs_var}' is dead"
                    )

            if should_keep:
                new_lines.append(line)

        G.nodes[node]["label"] = (
            "\n".join(new_lines) if new_lines else "Empty"
        )

    return G, changes


def print_dead_code_elimination(changes: list):
    print("\n" + "="*50)
    print("  DEAD CODE ELIMINATION")
    print("="*50)

    if changes:
        print(f"\n✅ {len(changes)} dead assignment(s)"
              f" removed:\n")
        for c in changes:
            print(f"  ✗ {c}")
    else:
        print("\n  No dead assignments found.")