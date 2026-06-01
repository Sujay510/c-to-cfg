import subprocess
import os
from typing import Any
import networkx as nx


def visualize_cfg(G: nx.DiGraph,
                  output_path: str = "cfg_output.png"):

    dot_path = output_path.replace(".png", ".dot")

    lines = []
    lines.append("digraph CFG {")
    lines.append(
        '    graph [rankdir=TB, splines=ortho,'
        ' nodesep=1.0, ranksep=1.2,'
        ' bgcolor=white, fontname="Arial"];'
    )
    lines.append(
        '    node  [shape=ellipse, style=filled,'
        ' fillcolor=white, color=black,'
        ' fontname="Arial", fontsize=11,'
        ' penwidth=1.5, margin="0.4,0.2"];'
    )
    lines.append(
        '    edge  [color=black, arrowsize=0.9,'
        ' penwidth=1.3, fontname="Arial",'
        ' fontsize=10];'
    )
    lines.append("")

    # ── Nodes ────────────────────────────────────────────────
    for n in G.nodes:
        raw_label = G.nodes[n].get("label", str(n))

        # Escape special chars for DOT
        dot_label = (raw_label
                     .replace('"', '\\"')
                     .replace('\n', '\\n'))

        # Style by content
        if raw_label in ("START",):
            lines.append(
                f'    N{n} [label="{dot_label}",'
                f' fillcolor="#c8c8c8",'
                f' fontsize=13, fontweight=bold,'
                f' width=1.6, height=0.7];'
            )
        elif raw_label.startswith("END ") or raw_label == "END":
            lines.append(
                f'    N{n} [label="{dot_label}",'
                f' fillcolor="#c8c8c8",'
                f' fontsize=13, fontweight=bold,'
                f' width=1.6, height=0.7];'
            )
        elif raw_label.startswith("FUNCTION "):
            lines.append(
                f'    N{n} [label="{dot_label}",'
                f' fillcolor="#f0f0f0",'
                f' fontsize=11, fontweight=bold];'
            )
        elif raw_label.startswith("IF "):
            lines.append(
                f'    N{n} [label="{dot_label}",'
                f' fillcolor="#ffffff"];'
            )
        elif any(raw_label.startswith(k) for k in
                 ["WHILE", "FOR COND", "DO WHILE",
                  "FOR INIT", "FOR NEXT", "FOR EXIT",
                  "LOOP EXIT"]):
            lines.append(
                f'    N{n} [label="{dot_label}",'
                f' fillcolor="#ffffff"];'
            )
        elif raw_label in ("MERGE", "BREAK",
                           "CONTINUE", "SWITCH EXIT"):
            lines.append(
                f'    N{n} [label="{dot_label}",'
                f' fillcolor="#eeeeee"];'
            )
        else:
            lines.append(
                f'    N{n} [label="{dot_label}"];'
            )

    lines.append("")

    # ── Edges ────────────────────────────────────────────────
    for u, v in G.edges:
        u_label = G.nodes[u].get("label", "")
        out_edges = list(G.successors(u))

        is_branch = (
            len(out_edges) == 2
            and any(u_label.startswith(k) for k in
                    ["IF ", "WHILE ", "FOR COND",
                     "DO WHILE", "SWITCH"])
        )

        if is_branch:
            edge_label = (
                "True" if v == out_edges[0] else "False"
            )
            lines.append(
                f'    N{u} -> N{v}'
                f' [label=" {edge_label} "];'
            )
        else:
            lines.append(f'    N{u} -> N{v};')

    lines.append("}")

    # ── Write DOT ────────────────────────────────────────────
    with open(dot_path, "w") as f:
        f.write("\n".join(lines))
    print(f"DOT written: {dot_path}")

    # ── Render ───────────────────────────────────────────────
    try:
        result = subprocess.run(
            ["dot", "-Tpng", "-Gdpi=200",
             dot_path, "-o", output_path],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print(f"CFG saved → {output_path} ✅")
        else:
            print(f"Graphviz error:\n{result.stderr}")
            return
    except FileNotFoundError:
        print("ERROR: dot not found in PATH")
        return

    # ── Open image ───────────────────────────────────────────
    try:
        os.startfile(output_path)
    except Exception:
        print(f"Open manually: {output_path}")