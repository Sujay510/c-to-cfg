import networkx as nx
import re


def evaluate_expression(expr: str):
    """
    Try to evaluate a constant expression like
    '3 + 5', '10 * 2', '8 / 4' etc.
    Returns result as string if possible, else None.
    """
    # Only allow safe characters
    safe = re.match(r'^[\d\s\+\-\*\/\%\(\)\.]+$', expr)
    if not safe:
        return None
    try:
        result = eval(expr)
        # Only return if result is int or float
        if isinstance(result, (int, float)):
            return str(int(result))
    except Exception:
        return None
    return None


def fold_expression(line: str) -> tuple:
    """
    Given an instruction line like:
      'x = 3 + 5'
    Try to fold the RHS.
    Returns (new_line, was_changed).
    """
    if "=" not in line:
        return line, False

    parts = line.split("=", 1)
    lhs = parts[0].strip()
    rhs = parts[1].strip()

    result = evaluate_expression(rhs)
    if result is not None and result != rhs:
        new_line = f"{lhs} = {result}"
        return new_line, True

    return line, False


def constant_folding(G: nx.DiGraph) -> tuple:
    """
    Walk all CFG nodes and fold constant expressions.
    Returns (modified_G, list of changes made).
    """
    changes = []

    for node in G.nodes:
        label = G.nodes[node].get("label", "")
        lines = label.split("\n")
        new_lines = []
        node_changed = False

        for line in lines:
            new_line, changed = fold_expression(line)
            new_lines.append(new_line)
            if changed:
                node_changed = True
                changes.append(
                    f"Block {node}: "
                    f"'{line}' → '{new_line}'"
                )

        if node_changed:
            G.nodes[node]["label"] = "\n".join(new_lines)

    return G, changes


def print_constant_folding(changes: list):
    print("\n" + "=" * 50)
    print("  CONSTANT FOLDING")
    print("=" * 50)

    if changes:
        print(f"\n✅ {len(changes)} expression(s) folded:\n")
        for c in changes:
            print(f"  ✓ {c}")
    else:
        print("\n  No constant expressions found to fold.")