import networkx as nx
import re
from typing import Dict


KEYWORDS = {
    "int", "float", "char", "double", "long",
    "void", "return", "if", "while", "for",
    "else", "break", "continue", "main", "foo",
    "START", "END", "MERGE", "FUNCTION", "WHILE",
    "FOR", "IF", "CALL", "LOOP", "EXIT", "INIT",
    "COND", "NEXT", "RETURN", "BREAK", "CONTINUE",
    "SWITCH", "CASE", "DEFAULT", "DO"
}

SKIP_PREFIXES = (
    "IF", "WHILE", "FOR", "RETURN",
    "FUNCTION", "END", "START", "MERGE",
    "BREAK", "CONTINUE", "CALL", "LOOP",
    "SWITCH", "CASE", "DO"
)


def get_const_value(rhs: str):
    """Return rhs if it is a pure integer/float constant."""
    rhs = rhs.strip()
    if re.match(r'^\-?\d+(\.\d+)?$', rhs):
        return rhs
    return None


def collect_block_constants(label: str) -> dict:
    """
    Walk a block's lines top-to-bottom, simulating execution.
    Return dict of {var: const_value} for variables that hold
    a known constant by the END of the block.
    Last write wins; a non-const assignment invalidates.

    KEY FIX: When we see  lhs = expr(rhs_vars),
    we substitute known constants into rhs FIRST (using the
    env at that point), then check if the result is a constant.
    This means  b = a + b  with a=5, b=3  → b = 5 + 3 → b=8.
    """
    env = {}
    for line in label.split("\n"):
        stripped = line.strip()
        if "=" not in stripped:
            continue
        if any(stripped.startswith(k) for k in SKIP_PREFIXES):
            continue
        parts = stripped.split("=", 1)
        if len(parts) < 2:
            continue

        lhs = re.sub(
            r'\b(int|float|char|double|long)\b', '', parts[0]
        ).strip()
        rhs = parts[1].strip()

        if not (lhs and lhs.isidentifier() and lhs not in KEYWORDS):
            continue

        # Substitute known constants into rhs BEFORE reading lhs
        # This handles b = a + b correctly: read old b from env
        subst_rhs = rhs
        for var, val in env.items():
            subst_rhs = re.sub(
                rf'\b{re.escape(var)}\b', val, subst_rhs
            )

        # Now evaluate and update lhs
        val = get_const_value(subst_rhs)
        if val:
            env[lhs] = val
        else:
            # Try folding numeric expression
            try:
                safe = re.match(r'^[\d\s\+\-\*\/\%\(\)\.]+$',
                                subst_rhs.strip())
                if safe:
                    result = eval(subst_rhs.strip())
                    env[lhs] = str(int(result))
                else:
                    env.pop(lhs, None)
            except Exception:
                env.pop(lhs, None)
    return env


def propagate_constants(G: nx.DiGraph, IN_rd: Dict) -> tuple:
    """
    Constant Propagation — iterates until convergence.

    For each node:
      1. Build 'env' from predecessor block constants
         (intersection: var must have SAME const in ALL preds).
      2. Walk lines top-to-bottom:
         - Substitute constants from env + local_env into RHS
           BEFORE updating local_env with the LHS result.
         - This correctly handles  b = a + b  where b is on
           both sides: we use the OLD value of b from env.
      3. Update local_env AFTER substitution (new value of lhs).

    KEY FIX vs original:
    - Old code updated local_env[lhs] and then substituted,
      which could cause the new lhs value to bleed back into
      the same line's rhs.
    - New code: snapshot combined_env BEFORE the line executes,
      substitute from snapshot, THEN update local_env.
    """
    changes = []
    max_passes = 10

    for pass_num in range(max_passes):
        pass_changes = []

        for node in G.nodes:
            label = G.nodes[node].get("label", "")
            lines = label.split("\n")

            # ── Build predecessor constant environment ────────
            preds = list(G.predecessors(node))
            if preds:
                pred_envs = [
                    collect_block_constants(
                        G.nodes[p].get("label", "")
                    )
                    for p in preds
                ]
                # Intersection: only vars where ALL preds agree
                env = {}
                for var, val in pred_envs[0].items():
                    if all(pe.get(var) == val
                           for pe in pred_envs[1:]):
                        env[var] = val
            else:
                env = {}

            # local_env tracks constants defined so far in block
            local_env = {}
            new_lines = []

            for line in lines:
                stripped = line.strip()
                new_line = line

                if "=" in stripped and not any(
                    stripped.startswith(k)
                    for k in SKIP_PREFIXES
                ):
                    parts = stripped.split("=", 1)
                    lhs_raw = parts[0]
                    rhs = parts[1].strip()

                    lhs = re.sub(
                        r'\b(int|float|char|double|long)\b',
                        '', lhs_raw
                    ).strip()

                    # ── SNAPSHOT env before this line executes ─
                    # combined_env is used for substitution.
                    # local_env values (intra-block) override
                    # predecessor values.
                    combined_env = {**env, **local_env}

                    new_rhs = rhs
                    for var, val in combined_env.items():
                        new_rhs = re.sub(
                            rf'\b{re.escape(var)}\b',
                            val, new_rhs
                        )

                    if new_rhs != rhs:
                        new_line = (
                            f"{lhs_raw.rstrip()} = {new_rhs}"
                        )
                        pass_changes.append(
                            f"Block {node}: "
                            f"'{stripped}'"
                            f" → '{new_line.strip()}'"
                        )

                    # ── Update local_env AFTER substitution ────
                    # Use new_rhs (post-substitution) to determine
                    # if lhs now holds a constant.
                    if (lhs and lhs.isidentifier()
                            and lhs not in KEYWORDS):
                        final_val = get_const_value(new_rhs)
                        if final_val is None:
                            # Try folding the substituted rhs
                            try:
                                safe = re.match(
                                    r'^[\d\s\+\-\*\/\%\(\)\.]+$',
                                    new_rhs.strip()
                                )
                                if safe:
                                    result = eval(new_rhs.strip())
                                    final_val = str(int(result))
                            except Exception:
                                pass
                        if final_val:
                            local_env[lhs] = final_val
                        else:
                            # lhs is no longer a known constant
                            local_env.pop(lhs, None)
                            env.pop(lhs, None)

                new_lines.append(new_line)

            new_label = "\n".join(new_lines)
            if new_label != label:
                G.nodes[node]["label"] = new_label

        changes.extend(pass_changes)
        if not pass_changes:
            break  # Converged

    return G, changes


def print_constant_propagation(changes: list):
    print("\n" + "=" * 50)
    print("  CONSTANT PROPAGATION")
    print("=" * 50)
    if changes:
        print(f"\n✅ {len(changes)} propagation(s):\n")
        for c in changes:
            print(f"  ✓ {c}")
    else:
        print("\n  No constants to propagate.")