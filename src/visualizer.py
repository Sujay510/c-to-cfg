import subprocess
import os
from typing import List
from .basic_blocks import BasicBlock


def make_label(block: BasicBlock) -> str:
    """Make clean short label for each block."""
    if block.label == "Entry":
        return "START"
    if block.label == "Exit":
        return "END"
    if block.label.startswith("FuncExit:"):
        fname = block.label.split(":")[1]
        return f"END {fname}"

    if not block.instructions:
        return block.label or f"Block {block.id}"

    replacements = {
        "DECL ":     "Decl ",
        "FOR_INIT ": "FOR INIT:\\n",
        "FOR_COND ": "FOR COND:\\n",
        "FOR_INC ":  "FOR NEXT:\\n",
        "WHILE ":    "WHILE ",
        "DO_WHILE ": "DO WHILE:\\n",
        "CALL ":     "CALL:\\n",
        "RETURN ":   "RETURN ",
        "UNARY ":    "",
    }

    lines = []
    for instr in block.instructions[:3]:
        clean = instr
        for old, new in replacements.items():
            clean = clean.replace(old, new)
        lines.append(clean)

    if len(block.instructions) > 3:
        lines.append(f"+{len(block.instructions) - 3} more")

    return "\\n".join(lines)


def visualize_cfg(blocks: List[BasicBlock],
                  output_path: str = "cfg_output.png"):

    dot_path = output_path.replace(".png", ".dot")

    lines = []
    lines.append("digraph CFG {")
    lines.append(
        '    graph [rankdir=TB, splines=ortho,'
        ' nodesep=1.2, ranksep=1.4,'
        ' bgcolor=white, fontname="Arial"];'
    )
    lines.append(
        '    node  [shape=ellipse, style=filled,'
        ' fillcolor=white, color=black,'
        ' fontname="Arial", fontsize=11,'
        ' penwidth=1.5, margin="0.35,0.2"];'
    )
    lines.append(
        '    edge  [color=black, arrowsize=0.9,'
        ' penwidth=1.3, fontname="Arial",'
        ' fontsize=10];'
    )
    lines.append("")

    # ── Nodes ────────────────────────────────────────────────
    for block in blocks:
        label = make_label(block)
        node_id = f"B{block.id}"

        is_special = (
            block.label in ("Entry", "Exit")
            or block.label.startswith("FuncExit:")
            or block.label.startswith("Func:")
        )

        if block.label == "Entry":
            lines.append(
                f'    {node_id} [label="{label}",'
                f' fillcolor="#c8c8c8",'
                f' fontsize=13, fontweight=bold,'
                f' width=1.6, height=0.7];'
            )
        elif block.label == "Exit":
            lines.append(
                f'    {node_id} [label="{label}",'
                f' fillcolor="#c8c8c8",'
                f' fontsize=13, fontweight=bold,'
                f' width=1.6, height=0.7];'
            )
        elif block.label.startswith("FuncExit:"):
            lines.append(
                f'    {node_id} [label="{label}",'
                f' fillcolor="#e8e8e8",'
                f' fontsize=11, fontweight=bold];'
            )
        elif block.label.startswith("Func:"):
            fname = block.label.split(":")[1]
            lines.append(
                f'    {node_id} [label="{label}",'
                f' fillcolor="#f0f0f0",'
                f' fontsize=11, fontweight=bold];'
            )
        else:
            lines.append(
                f'    {node_id} [label="{label}"];'
            )

    lines.append("")

    # ── Edges ────────────────────────────────────────────────
    for block in blocks:
        successors = block.successors
        node_label = make_label(block)

        is_branch = (
            len(successors) == 2
            and any(k in node_label for k in
                    ["IF", "WHILE", "FOR COND",
                     "DO WHILE", "SWITCH"])
        )

        for i, succ in enumerate(successors):
            edge_label = ""
            if is_branch:
                edge_label = "True" if i == 0 else "False"

            if edge_label:
                lines.append(
                    f'    B{block.id} -> B{succ}'
                    f' [label=" {edge_label} "];'
                )
            else:
                lines.append(
                    f'    B{block.id} -> B{succ};'
                )

    lines.append("}")

    # ── Write DOT file ───────────────────────────────────────
    dot_content = "\n".join(lines)
    with open(dot_path, "w") as f:
        f.write(dot_content)
    print(f"DOT file written: {dot_path}")

    # ── Render PNG via graphviz ───────────────────────────────
    try:
        result = subprocess.run(
            ["dot", "-Tpng", "-Gdpi=200",
             dot_path, "-o", output_path],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"CFG saved to {output_path} ✅")
        else:
            print(f"Graphviz error:\n{result.stderr}")
            return
    except FileNotFoundError:
        print("ERROR: graphviz dot not in PATH")
        return

    # ── Auto open image ──────────────────────────────────────
    try:
        os.startfile(output_path)
    except Exception:
        print(f"Open manually: {output_path}")