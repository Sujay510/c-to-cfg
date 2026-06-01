import streamlit as st
import tempfile
import os
import re
import copy
import networkx as nx

from src.parser import parse_c_code
from src.cfg_builder import CFGBuilder
from src.visualizer import visualize_cfg

from src.analysis.reaching_definitions import (
    reaching_definitions
)
from src.analysis.live_variables import (
    live_variable_analysis
)
from src.optimization.constant_folding import (
    constant_folding
)
from src.optimization.constant_propagation import (
    propagate_constants
)
from src.optimization.dead_code_elimination import (
    dead_code_elimination
)
from src.optimization.unreachable_code import (
    remove_unreachable
)
from src.code_generator import generate_optimized_c


# ── Page Config ──────────────────────────────────────────
st.set_page_config(
    page_title="CFG Analyzer",
    page_icon="🔷",
    layout="wide"
)


# ── Default Sample C Code ─────────────────────────────────
DEFAULT_CODE = """\
#include <stdio.h>

int foo(int x) {
    return x + 1;
}

int main() {
    int a = 5;
    a = a + 3;
    int b = a + 2;

    if (b > 5) {
        b = foo(b);
    } else {
        b = b - 1;
    }

    for (int i = 0; i < 3; i++) {
        b = b + i;
    }

    while (a < 10) {
        a = a + 1;
        if (a == 7) continue;
        if (a == 9) break;
        b = b + a;
    }
    int z = 0;
    return b;
}
"""


# ── Helper: render CFG to bytes ───────────────────────────
def render_cfg_to_bytes(G: nx.DiGraph,
                        filename: str) -> bytes:
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, filename)
        visualize_cfg(G, output_path=path)
        if os.path.exists(path):
            with open(path, "rb") as f:
                return f.read()
    return b""


# ── Helper: build fresh copy of graph ────────────────────
def deep_copy_graph(G: nx.DiGraph) -> nx.DiGraph:
    G2 = nx.DiGraph()
    for n, data in G.nodes(data=True):
        G2.add_node(n, **{k: v for k, v in data.items()})
    for u, v in G.edges():
        G2.add_edge(u, v)
    return G2


# ── Header ───────────────────────────────────────────────
st.title("🔷 C Control Flow Graph Analyzer")
st.markdown(
    "Paste any C code → get CFG, "
    "static analysis and optimizations instantly."
)
st.divider()


# ── Sidebar ──────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Options")

    phase = st.radio(
        "Select Phase:",
        [
            "Phase 1 — CFG Only",
            "Phase 2 — CFG + Analysis",
            "Phase 3 — CFG + Optimizations",
        ]
    )

    st.divider()
    st.markdown("### 📖 What Each Phase Does")
    st.markdown("""
**Phase 1 — CFG**
- Parses C code
- Builds Control Flow Graph
- Shows CFG image

**Phase 2 — Analysis**
- Reaching Definitions
  - Detects uninitialized variables
- Live Variable Analysis
  - Detects dead assignments

**Phase 3 — Optimizations**
- Constant Folding
- Constant Propagation
- Dead Code Elimination
- Unreachable Code Removal
- Shows optimized CFG + C code
""")

    st.divider()
    st.markdown("### 💡 Tips")
    st.markdown("""
- `#include` is auto removed
- Comments are auto removed
- Works with multiple functions
- Supports all C control flow
""")


# ── C Code Input ──────────────────────────────────────────
st.markdown("### 📝 Paste Your C Code")
code = st.text_area(
    label="C Code Input",
    value=DEFAULT_CODE,
    height=350,
    label_visibility="collapsed",
    placeholder="Paste your C code here..."
)

col_btn1, col_btn2 = st.columns([1, 5])
with col_btn1:
    analyze = st.button(
        "🚀 Analyze",
        type="primary",
        use_container_width=True
    )
with col_btn2:
    clear = st.button(
        "🗑️ Clear",
        use_container_width=False
    )

if clear:
    st.rerun()

st.divider()


# ── Main Analysis ─────────────────────────────────────────
if analyze:

    # ── Validate input ────────────────────────────────────
    if not code.strip():
        st.error("❌ Please paste some C code first!")
        st.stop()

    # ── Parse C Code ─────────────────────────────────────
    with st.spinner("🔍 Parsing C code ..."):
        try:
            ast = parse_c_code(code)
        except Exception as e:
            st.error(f"❌ Parse Error: {e}")
            st.markdown(
                "**Common fixes:**\n"
                "- Remove unsupported macros\n"
                "- Check balanced `{}` braces\n"
                "- Remove `typedef` / `struct` for now"
            )
            st.stop()

    # ── Build CFG ─────────────────────────────────────────
    with st.spinner("🔨 Building CFG ..."):
        builder = CFGBuilder()
        G_original = builder.build(ast)

    st.success(
        f"✅ CFG built with "
        f"{G_original.number_of_nodes()} nodes "
        f"and {G_original.number_of_edges()} edges."
    )

    # ═════════════════════════════════════════════════════
    # PHASE 1 — CFG
    # ═════════════════════════════════════════════════════
    st.markdown("## Phase 1 — Control Flow Graph")

    with st.spinner("🖼️ Rendering CFG image ..."):
        cfg_bytes = render_cfg_to_bytes(
            G_original, "cfg_output.png"
        )

    if cfg_bytes:
        col_img, col_dl = st.columns([4, 1])
        with col_img:
            st.image(
                cfg_bytes,
                caption="Original CFG",
                use_container_width=True
            )
        with col_dl:
            st.download_button(
                label="⬇️ Download\nCFG",
                data=cfg_bytes,
                file_name="cfg_output.png",
                mime="image/png",
                use_container_width=True
            )
    else:
        st.error("❌ Could not render CFG image.")

    # Show CFG node summary
    with st.expander("📋 View CFG Node Details"):
        node_data = []
        for n in G_original.nodes:
            label = G_original.nodes[n].get("label","")
            first = label.split("\n")[0]
            succs = list(G_original.successors(n))
            preds = list(G_original.predecessors(n))
            node_data.append({
                "Block": f"Block {n}",
                "Label": first,
                "Instructions": len(label.split("\n")),
                "Successors": str(succs),
                "Predecessors": str(preds),
            })
        st.dataframe(
            node_data, use_container_width=True
        )

    # Stop here if phase 1 only
    if phase == "Phase 1 — CFG Only":
        st.divider()
        st.info(
            "Switch to Phase 2 or 3 in the sidebar "
            "for more analysis!"
        )
        st.stop()

    # ═════════════════════════════════════════════════════
    # PHASE 2 — STATIC ANALYSIS
    # ═════════════════════════════════════════════════════
    st.divider()
    st.markdown("## Phase 2 — Static Analysis")

    G_analysis = deep_copy_graph(G_original)

    with st.spinner("🔬 Running static analysis ..."):
        IN_rd, OUT_rd, gen, kill = \
            reaching_definitions(G_analysis)
        IN_lv, OUT_lv, use, defs = \
            live_variable_analysis(G_analysis)

    tab_rd, tab_lv = st.tabs([
        "📊 Reaching Definitions",
        "📊 Live Variable Analysis"
    ])

    # ── Reaching Definitions Tab ──────────────────────────
    with tab_rd:
        st.markdown(
            "**Goal:** For every variable at every point, "
            "determine which assignments could reach that point."
        )
        st.markdown(
            "`OUT[B] = GEN[B] ∪ (IN[B] - KILL[B])`"
            " &nbsp;&nbsp; "
            "`IN[B] = ∪ OUT[P] for all predecessors P`"
        )
        st.markdown("")

        rd_data = []
        warnings_rd = []

        for node in G_analysis.nodes:
            label = G_analysis.nodes[node].get(
                "label", ""
            )
            first = label.split("\n")[0]

            rd_data.append({
                "Block": f"Block {node}",
                "Label": first,
                "GEN":  str(gen.get(node,  set()) or "∅"),
                "KILL": str(kill.get(node, set()) or "∅"),
                "IN":   str(IN_rd.get(node, set()) or "∅"),
                "OUT":  str(OUT_rd.get(node, set()) or "∅"),
            })

            # Detect uninitialized variables
            for line in label.split("\n"):
                if "=" in line and not any(
                    line.strip().startswith(k)
                    for k in ["IF","WHILE","FOR",
                               "RETURN","FUNCTION",
                               "END","START","MERGE"]
                ):
                    rhs = line.split("=", 1)[1]
                    used_vars = re.findall(
                        r'\b[a-zA-Z_]\w*\b', rhs
                    )
                    SKIP = {
                        "int","float","char","void",
                        "return","if","while","for",
                        "else","break","continue"
                    }
                    for v in used_vars:
                        if v not in SKIP and \
                           v not in IN_rd.get(node, set()):
                            warnings_rd.append(
                                f"Block {node} "
                                f"({first}): "
                                f"'{v}' may be "
                                f"uninitialized"
                            )

        st.dataframe(rd_data, use_container_width=True)
        st.markdown("")

        if warnings_rd:
            st.markdown("**⚠️ Warnings:**")
            for w in set(warnings_rd):
                st.warning(f"⚠️ {w}")
        else:
            st.success(
                "✅ No uninitialized variables found."
            )

    # ── Live Variable Analysis Tab ────────────────────────
    with tab_lv:
        st.markdown(
            "**Goal:** Determine if the value currently "
            "held in a variable will be used in the future."
        )
        st.markdown(
            "`IN[B] = USE[B] ∪ (OUT[B] - DEF[B])`"
            " &nbsp;&nbsp; "
            "`OUT[B] = ∪ IN[S] for all successors S`"
        )
        st.markdown("")

        lv_data = []
        dead_list = []

        for node in G_analysis.nodes:
            label = G_analysis.nodes[node].get(
                "label", ""
            )
            first = label.split("\n")[0]

            lv_data.append({
                "Block": f"Block {node}",
                "Label": first,
                "USE": str(use.get(node,  set()) or "∅"),
                "DEF": str(defs.get(node, set()) or "∅"),
                "IN":  str(IN_lv.get(node,  set()) or "∅"),
                "OUT": str(OUT_lv.get(node, set()) or "∅"),
            })

            # Detect dead assignments
            for var in defs.get(node, set()):
                if var not in OUT_lv.get(node, set()):
                    dead_list.append(
                        f"Block {node} ({first}): "
                        f"'{var}' is assigned but "
                        f"never used after this point"
                    )

        st.dataframe(lv_data, use_container_width=True)
        st.markdown("")

        if dead_list:
            st.markdown("**⚠️ Dead Assignments:**")
            for d in set(dead_list):
                st.warning(f"⚠️ {d}")
        else:
            st.success("✅ No dead assignments found.")

    # Stop here if phase 2 only
    if phase == "Phase 2 — CFG + Analysis":
        st.divider()
        st.info(
            "Switch to Phase 3 in the sidebar "
            "to apply optimizations!"
        )
        st.stop()

    # ═════════════════════════════════════════════════════
    # PHASE 3 — OPTIMIZATIONS
    # ═════════════════════════════════════════════════════
    st.divider()
    st.markdown("## Phase 3 — Optimizations")

    G_opt = deep_copy_graph(G_original)

    with st.spinner("⚡ Applying optimizations ..."):

        # 1. Constant Folding
        G_opt, cf_changes = constant_folding(G_opt)

        # 2. Constant Propagation
        G_opt, cp_changes = propagate_constants(
            G_opt, IN_rd
        )

        # 3. Re-fold after propagation
        G_opt, cf2_changes = constant_folding(G_opt)
        cf_changes += cf2_changes

        # 4. Recompute live vars on optimized graph
        IN_lv2, OUT_lv2, _, _ = \
            live_variable_analysis(G_opt)

        # 5. Dead Code Elimination
        G_opt, dce_changes = dead_code_elimination(
            G_opt, OUT_lv2
        )

        # 6. Unreachable Code Removal
        G_opt, ur_changes = remove_unreachable(G_opt)

    total = (
        len(cf_changes) +
        len(cp_changes) +
        len(dce_changes) +
        len(ur_changes)
    )

    # ── Metrics ───────────────────────────────────────────
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total Changes", total)
    m2.metric("Constant Folding", len(cf_changes))
    m3.metric("Constant Propagation", len(cp_changes))
    m4.metric("Dead Code Removed", len(dce_changes))
    m5.metric("Unreachable Removed", len(ur_changes))

    st.markdown("")

    # ── Optimization Details ──────────────────────────────
    if cf_changes:
        with st.expander(
            f"🔁 Constant Folding "
            f"— {len(cf_changes)} change(s)"
        ):
            for c in cf_changes:
                st.code(c, language="text")

    if cp_changes:
        with st.expander(
            f"🔁 Constant Propagation "
            f"— {len(cp_changes)} change(s)"
        ):
            for c in cp_changes:
                st.code(c, language="text")

    if dce_changes:
        with st.expander(
            f"🗑️ Dead Code Eliminated "
            f"— {len(dce_changes)} removed"
        ):
            for c in dce_changes:
                st.code(c, language="text")

    if ur_changes:
        with st.expander(
            f"🗑️ Unreachable Code Removed "
            f"— {len(ur_changes)} removed"
        ):
            for c in ur_changes:
                st.code(c, language="text")

    if total == 0:
        st.info(
            "ℹ️ No optimizations were applicable "
            "to this code."
        )

    # ── Optimized CFG Image ───────────────────────────────
    st.markdown("### Optimized CFG")

    with st.spinner("🖼️ Rendering optimized CFG ..."):
        opt_bytes = render_cfg_to_bytes(
            G_opt, "cfg_optimized.png"
        )

    # Before vs After comparison
    st.markdown("### Before vs After")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**🔵 Original CFG**")
        if cfg_bytes:
            st.image(
                cfg_bytes,
                use_container_width=True
            )
        st.download_button(
            label="⬇️ Download Original CFG",
            data=cfg_bytes,
            file_name="cfg_output.png",
            mime="image/png",
            use_container_width=True
        )

    with c2:
        st.markdown("**🟢 Optimized CFG**")
        if opt_bytes:
            st.image(
                opt_bytes,
                use_container_width=True
            )
        st.download_button(
            label="⬇️ Download Optimized CFG",
            data=opt_bytes,
            file_name="cfg_optimized.png",
            mime="image/png",
            use_container_width=True
        )

    # ── Optimized C Code ──────────────────────────────────
    st.divider()
    st.markdown("### 📄 Optimized C Code")

    with st.spinner("✍️ Generating optimized C code ..."):
        optimized_c = generate_optimized_c(G_opt)

    code_col1, code_col2 = st.columns(2)
    with code_col1:
        st.markdown("**Original C Code**")
        st.code(code, language="c")

    with code_col2:
        st.markdown("**Optimized C Code**")
        st.code(optimized_c, language="c")

    st.download_button(
        label="⬇️ Download Optimized C Code (.c)",
        data=optimized_c,
        file_name="optimized.c",
        mime="text/plain",
        use_container_width=True
    )

    # ── Done ──────────────────────────────────────────────
    st.divider()
    st.success("✅ Analysis complete!")