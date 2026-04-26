import sys
from src.parser import parse_c_file
from src.cfg_builder import CFGBuilder
from src.visualizer import visualize_cfg

from src.analysis.reaching_definitions import (
    reaching_definitions, print_reaching_definitions
)
from src.analysis.live_variables import (
    live_variable_analysis, print_live_variables
)
from src.optimization.constant_folding import (
    constant_folding, print_constant_folding
)
from src.optimization.constant_propagation import (
    propagate_constants, print_constant_propagation
)
from src.optimization.dead_code_elimination import (
    dead_code_elimination, print_dead_code_elimination
)
from src.optimization.unreachable_code import (
    remove_unreachable, print_unreachable_code
)


def run_phase1(G):
    print("\n" + "="*50)
    print("  PHASE 1: C TO CFG")
    print("="*50)
    print("\n=== CFG Nodes ===")
    for n in G.nodes:
        label = G.nodes[n].get("label", "")
        succs = list(G.successors(n))
        print(f"  [{n}] {label!r:35} → {succs}")
    print("\nGenerating CFG image ...")
    visualize_cfg(G, output_path="cfg_output.png")
    print("Saved → cfg_output.png ✅")


def run_phase2(G):
    print("\n" + "="*50)
    print("  PHASE 2: STATIC ANALYSIS")
    print("="*50)

    IN_rd, OUT_rd, gen, kill = reaching_definitions(G)
    print_reaching_definitions(G, IN_rd, OUT_rd, gen, kill)

    IN_lv, OUT_lv, use, defs = live_variable_analysis(G)
    print_live_variables(G, IN_lv, OUT_lv, use, defs)

    return IN_rd, OUT_rd, IN_lv, OUT_lv


def run_phase3(G, OUT_lv, IN_rd):
    print("\n" + "="*50)
    print("  PHASE 3: OPTIMIZATIONS")
    print("="*50)

    total_changes = 0

    # ── 1. Constant Folding ───────────────────────────────
    G, cf_changes = constant_folding(G)
    print_constant_folding(cf_changes)
    total_changes += len(cf_changes)

    # ── 2. Constant Propagation ───────────────────────────
    G, cp_changes = propagate_constants(G, IN_rd)
    print_constant_propagation(cp_changes)
    total_changes += len(cp_changes)

    # ── After propagation, fold again ─────────────────────
    # e.g. 'b = 5 + 2' can now be folded to 'b = 7'
    G, cf2_changes = constant_folding(G)
    if cf2_changes:
        print("\n  [Re-folding after propagation]")
        for c in cf2_changes:
            print(f"  ✓ {c}")
        total_changes += len(cf2_changes)

    # ── Recompute live vars after folding/propagation ─────
    # So DCE uses fresh analysis
    print("\n  [Recomputing Live Variables for DCE...]")
    IN_lv2, OUT_lv2, _, _ = live_variable_analysis(G)

    # ── 3. Dead Code Elimination ──────────────────────────
    G, dce_changes = dead_code_elimination(G, OUT_lv2)
    print_dead_code_elimination(dce_changes)
    total_changes += len(dce_changes)

    # ── 4. Unreachable Code Removal ───────────────────────
    G, ur_changes = remove_unreachable(G)
    print_unreachable_code(ur_changes)
    total_changes += len(ur_changes)

    # ── Summary ───────────────────────────────────────────
    print("\n" + "="*50)
    print(f"  TOTAL OPTIMIZATIONS APPLIED: {total_changes}")
    print("="*50)

    print("\nGenerating optimized CFG image ...")
    visualize_cfg(G, output_path="cfg_optimized.png")
    print("Saved → cfg_optimized.png ✅")

    return G


def print_usage():
    print("""
Usage:
  python main.py            ← runs all phases
  python main.py --phase 1  ← Phase 1 only (CFG)
  python main.py --phase 2  ← Phase 1 + 2 (Analysis)
  python main.py --phase 3  ← Phase 1 + 2 + 3 (Optimizations)
  python main.py --help     ← show this help
""")


def main():
    phase = "all"

    if "--help" in sys.argv or "-h" in sys.argv:
        print_usage()
        return

    if "--phase" in sys.argv:
        idx = sys.argv.index("--phase")
        try:
            phase = sys.argv[idx + 1]
            if phase not in ("1", "2", "3"):
                print("❌ Invalid phase. Use 1, 2 or 3.")
                print_usage()
                return
        except IndexError:
            print("❌ Please provide phase number.")
            print_usage()
            return

    # Always parse and build CFG
    print("Parsing sample.c ...")
    ast = parse_c_file("samples/sample.c")
    print("Building CFG ...")
    builder = CFGBuilder()
    G = builder.build(ast)

    if phase == "1":
        run_phase1(G)

    elif phase == "2":
        run_phase1(G)
        run_phase2(G)

    elif phase == "3":
        run_phase1(G)
        IN_rd, OUT_rd, IN_lv, OUT_lv = run_phase2(G)
        run_phase3(G, OUT_lv, IN_rd)

    else:
        # All phases
        run_phase1(G)
        IN_rd, OUT_rd, IN_lv, OUT_lv = run_phase2(G)
        run_phase3(G, OUT_lv, IN_rd)


if __name__ == "__main__":
    main()