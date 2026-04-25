from src.parser import parse_c_file
from src.cfg_builder import CFGBuilder
from src.visualizer import visualize_cfg
from src.analysis.reaching_definitions import (
    reaching_definitions,
    print_reaching_definitions
)
from src.analysis.live_variables import (
    live_variable_analysis,
    print_live_variables
)


def main():
    print("Parsing sample.c ...")
    ast = parse_c_file("samples/sample.c")

    print("Building CFG ...")
    builder = CFGBuilder()
    G = builder.build(ast)

    print("\n=== CFG Nodes ===")
    for n in G.nodes:
        label = G.nodes[n].get("label", "")
        succs = list(G.successors(n))
        print(f"  [{n}] {label!r:30} → {succs}")

    # ── Phase 2: Static Analysis ──────────────────────────
    print("\n" + "="*50)
    print("  PHASE 2: STATIC ANALYSIS")
    print("="*50)

    # Reaching Definitions
    IN_rd, OUT_rd, gen, kill = reaching_definitions(G)
    print_reaching_definitions(G, IN_rd, OUT_rd, gen, kill)

    # Live Variable Analysis
    IN_lv, OUT_lv, use, defs = live_variable_analysis(G)
    print_live_variables(G, IN_lv, OUT_lv, use, defs)

    # ── Visualize CFG ─────────────────────────────────────
    print("\nGenerating CFG image ...")
    visualize_cfg(G, output_path="cfg_output.png")


if __name__ == "__main__":
    main()