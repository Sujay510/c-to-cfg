import networkx as nx
import re
from typing import Dict


KEYWORDS = {
    "int", "float", "char", "void", "return",
    "if", "while", "for", "else", "break",
    "continue", "START", "END", "MERGE",
    "FUNCTION", "WHILE", "FOR", "IF", "CALL",
    "LOOP", "EXIT", "INIT", "COND", "NEXT",
    "RETURN", "BREAK", "CONTINUE", "DO",
    "SWITCH", "CASE", "DEFAULT"
}

SKIP_PREFIXES = (
    "IF", "WHILE", "FOR", "RETURN",
    "BREAK", "CONTINUE", "CALL",
    "FUNCTION", "END", "START",
    "MERGE", "LOOP", "DO",
    "SWITCH", "CASE", "DEFAULT",
    "FOR COND", "FOR NEXT", "FOR INIT",
    "FOR EXIT", "LOOP EXIT"
)


def dead_code_elimination(G: nx.DiGraph,
                          OUT_lv: Dict) -> tuple:
    """
    Remove dead assignments from CFG blocks.

    A variable assigned in a line is dead if:
      - it is NOT in OUT_lv[block], AND
      - it is NOT used by any LATER line in the same block
        (intra-block liveness check).

    This catches cases like:
        a = 5          ← dead if 'a' is immediately overwritten
        a = 8          ← the real live assignment
    """
    changes = []

    for node in G.nodes:
        label = G.nodes[node].get("label", "")
        lines = label.split("\n")
        live_out = set(OUT_lv.get(node, set()))

        # ── Intra-block backward liveness pass ───────────────
        # live_after[i] = set of vars live just AFTER line i
        n = len(lines)
        live_after = [set() for _ in range(n + 1)]
        live_after[n] = set(live_out)

        for i in range(n - 1, -1, -1):
            line = lines[i].strip()
            live = set(live_after[i + 1])

            if "=" in line and not any(
                line.startswith(k) for k in SKIP_PREFIXES
            ):
                parts = line.split("=", 1)
                lhs_raw = parts[0].strip()
                rhs = parts[1].strip()

                lhs_var = re.sub(
                    r'\b(int|float|char|double|long)\b',
                    '', lhs_raw
                ).strip()
                lhs_var = re.sub(
                    r'\[.*?\]', '', lhs_var
                ).strip()

                used = set(re.findall(r'\b[a-zA-Z_]\w*\b', rhs))
                used -= KEYWORDS

                if (lhs_var and lhs_var.isidentifier()
                        and lhs_var not in KEYWORDS):
                    live.discard(lhs_var)

                live |= used
            else:
                used = set(
                    re.findall(r'\b[a-zA-Z_]\w*\b', line)
                )
                used -= KEYWORDS
                live |= used

            live_after[i] = live

        # ── Remove dead assignments ───────────────────────────
        new_lines = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            should_keep = True

            if "=" in stripped and not any(
                stripped.startswith(k) for k in SKIP_PREFIXES
            ):
                parts = stripped.split("=", 1)
                lhs_raw = parts[0].strip()

                lhs_var = re.sub(
                    r'\b(int|float|char|double|long)\b',
                    '', lhs_raw
                ).strip()
                lhs_var = re.sub(
                    r'\[.*?\]', '', lhs_var
                ).strip()

                if (lhs_var
                        and lhs_var.isidentifier()
                        and lhs_var not in KEYWORDS
                        and lhs_var not in live_after[i + 1]):
                    should_keep = False
                    changes.append(
                        f"Block {node}: "
                        f"removed '{stripped}' "
                        f"— '{lhs_var}' is dead"
                    )

            if should_keep:
                new_lines.append(line)

        final_label = "\n".join(new_lines).strip()
        G.nodes[node]["label"] = (
            final_label if final_label else "Empty"
        )

    return G, changes


def print_dead_code_elimination(changes: list):
    print("\n" + "=" * 50)
    print("  DEAD CODE ELIMINATION")
    print("=" * 50)
    if changes:
        print(
            f"\n✅ {len(changes)} dead "
            f"assignment(s) removed:\n"
        )
        for c in changes:
            print(f"  ✗ {c}")
    else:
        print("\n  No dead assignments found.")