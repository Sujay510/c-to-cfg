import networkx as nx
import re


def evaluate_expression(expr: str):
    """
    Evaluate constant arithmetic expressions.
    e.g. '3 + 5' → '8', '10 * 2' → '20'
    """
    safe = re.match(
        r'^[\d\s\+\-\*\/\%\(\)\.]+$', expr.strip()
    )
    if not safe:
        return None
    try:
        result = eval(expr.strip())
        if isinstance(result, (int, float)):
            return str(int(result))
    except Exception:
        return None
    return None


def fold_line(line: str) -> tuple:
    """
    Try to fold a single instruction line.
    Returns (new_line, changed).
    """
    if "=" not in line:
        return line, False

    skip = ("IF", "WHILE", "FOR", "RETURN",
            "FUNCTION", "END", "START", "MERGE",
            "BREAK", "CONTINUE", "CALL", "LOOP",
            "SWITCH", "CASE", "DO")
    stripped = line.strip()
    if any(stripped.startswith(k) for k in skip):
        return line, False

    parts = stripped.split("=", 1)
    if len(parts) < 2:
        return line, False

    lhs = parts[0].strip()
    rhs = parts[1].strip()

    result = evaluate_expression(rhs)
    if result is not None and result != rhs.strip():
        new_line = f"{lhs} = {result}"
        return new_line, True

    return line, False


def constant_folding(G: nx.DiGraph) -> tuple:
    """
    Walk all CFG nodes and fold constant expressions.
    Runs multiple passes until no more changes.
    """
    total_changes = []
    max_passes = 5

    for pass_num in range(max_passes):
        pass_changes = []

        for node in G.nodes:
            label = G.nodes[node].get("label", "")
            lines = label.split("\n")
            new_lines = []
            node_changed = False

            for line in lines:
                new_line, changed = fold_line(line)
                new_lines.append(new_line)
                if changed:
                    node_changed = True
                    pass_changes.append(
                        f"Block {node}: "
                        f"'{line.strip()}'"
                        f" → '{new_line.strip()}'"
                    )

            if node_changed:
                G.nodes[node]["label"] = \
                    "\n".join(new_lines)

        total_changes.extend(pass_changes)
        if not pass_changes:
            break

    return G, total_changes


def print_constant_folding(changes: list):
    print("\n" + "=" * 50)
    print("  CONSTANT FOLDING")
    print("=" * 50)
    if changes:
        print(f"\n✅ {len(changes)} expression(s) folded:\n")
        for c in changes:
            print(f"  ✓ {c}")
    else:
        print("\n  No constant expressions to fold.")