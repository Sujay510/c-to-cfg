import networkx as nx
import re
from typing import List, Set


class CCodeGenerator:
    """
    Converts an optimized CFG (NetworkX DiGraph)
    back into readable C code.
    """

    def __init__(self, G: nx.DiGraph):
        self.G = G
        self.visited: Set[int] = set()
        self.indent_level = 0
        self.lines: List[str] = []

    def indent(self) -> str:
        return "    " * self.indent_level

    def add(self, line: str):
        self.lines.append(self.indent() + line)

    def generate(self) -> str:
        """Main entry — generate full C code."""
        self.lines = []

        # Add standard header
        self.lines.append("#include <stdio.h>")
        self.lines.append("")

        # Find all function entry nodes
        func_nodes = [
            n for n in self.G.nodes
            if self.G.nodes[n].get("label", "")
               .startswith("FUNCTION ")
        ]

        # Find START node
        start_nodes = [
            n for n in self.G.nodes
            if self.G.nodes[n].get("label", "") == "START"
        ]

        if not start_nodes:
            return "// Could not generate code\n"

        start = start_nodes[0]

        # Process each function
        for func_node in self.G.successors(start):
            label = self.G.nodes[func_node].get(
                "label", ""
            )
            if label.startswith("FUNCTION "):
                fname = label.replace(
                    "FUNCTION ", ""
                ).strip().rstrip("()")
                self._generate_function(
                    func_node, fname
                )
                self.lines.append("")

        return "\n".join(self.lines)

    def _generate_function(self,
                           entry_node: int,
                           fname: str):
        """Generate code for one function."""
        self.visited = set()

        # Determine return type (default int)
        ret_type = "int"

        # Write function signature
        if fname == "main":
            self.add(f"{ret_type} {fname}() {{")
        else:
            self.add(f"{ret_type} {fname}(int x) {{")

        self.indent_level += 1

        # Walk nodes in order
        self._walk_nodes(entry_node)

        self.indent_level -= 1
        self.add("}")

    def _walk_nodes(self, node: int):
        """Walk CFG nodes and generate code."""
        if node in self.visited:
            return
        self.visited.add(node)

        label = self.G.nodes[node].get("label", "")
        lines = [l.strip() for l in label.split("\n")
                 if l.strip()]
        successors = list(self.G.successors(node))

        # Skip structural nodes
        skip_labels = {
            "START", "MERGE", "Empty",
            "LOOP EXIT", "FOR EXIT",
        }
        if label in skip_labels or \
           label.startswith("END ") or \
           label.startswith("FUNCTION "):
            for succ in successors:
                self._walk_nodes(succ)
            return

        # ── IF block ─────────────────────────────────
        if any(l.startswith("IF ") for l in lines):
            cond_line = next(
                l for l in lines if l.startswith("IF ")
            )
            cond = cond_line[3:].strip()
            # Remove outer parens if present
            if cond.startswith("(") and \
               cond.endswith(")"):
                cond = cond[1:-1]

            self.add(f"if ({cond}) {{")
            self.indent_level += 1

            # True branch
            if len(successors) >= 1:
                self._walk_nodes(successors[0])

            self.indent_level -= 1

            # False branch
            if len(successors) >= 2:
                self.add("} else {")
                self.indent_level += 1
                self._walk_nodes(successors[1])
                self.indent_level -= 1

            self.add("}")

        # ── FOR INIT block ───────────────────────────
        elif any(l.startswith("FOR INIT:") for l in lines):
            init_line = next(
                l for l in lines
                if l.startswith("FOR INIT:")
            )
            init = init_line.replace(
                "FOR INIT:", ""
            ).strip()

            # Find FOR COND node
            cond_node = successors[0] \
                if successors else None
            cond = "true"
            inc = ""
            body_node = None
            exit_node = None

            if cond_node is not None:
                cond_label = self.G.nodes[
                    cond_node
                ].get("label", "")
                cond_lines = cond_label.split("\n")
                for cl in cond_lines:
                    if "FOR COND:" in cl:
                        cond = cl.replace(
                            "FOR COND:", ""
                        ).strip().strip("()")

                cond_succs = list(
                    self.G.successors(cond_node)
                )
                for s in cond_succs:
                    s_label = self.G.nodes[s].get(
                        "label", ""
                    )
                    if "FOR EXIT" in s_label or \
                       "LOOP EXIT" in s_label:
                        exit_node = s
                    else:
                        body_node = s

            # Find FOR NEXT in body successors
            if body_node is not None:
                body_succs = list(
                    self.G.successors(body_node)
                )
                for bs in body_succs:
                    bs_label = self.G.nodes[bs].get(
                        "label", ""
                    )
                    if "FOR NEXT:" in bs_label:
                        inc_line = next(
                            (l for l in
                             bs_label.split("\n")
                             if "FOR NEXT:" in l),
                            ""
                        )
                        inc = inc_line.replace(
                            "FOR NEXT:", ""
                        ).strip()

            self.add(
                f"for ({init}; {cond}; {inc}) {{"
            )
            self.indent_level += 1
            if body_node:
                self.visited.add(
                    cond_node
                ) if cond_node else None
                self._walk_nodes(body_node)
            self.indent_level -= 1
            self.add("}")

            # Continue after loop
            if exit_node:
                self._walk_nodes(exit_node)

        # ── WHILE block ──────────────────────────────
        elif any(l.startswith("WHILE ") for l in lines):
            cond_line = next(
                l for l in lines
                if l.startswith("WHILE ")
            )
            cond = cond_line[6:].strip().strip("()")
            self.add(f"while ({cond}) {{")
            self.indent_level += 1

            body_succs = [
                s for s in successors
                if "LOOP EXIT" not in
                self.G.nodes[s].get("label", "") and
                "EXIT" not in
                self.G.nodes[s].get("label", "")
            ]
            exit_succs = [
                s for s in successors
                if "LOOP EXIT" in
                self.G.nodes[s].get("label", "") or
                "EXIT" in
                self.G.nodes[s].get("label", "")
            ]

            for s in body_succs:
                self._walk_nodes(s)

            self.indent_level -= 1
            self.add("}")

            for s in exit_succs:
                self._walk_nodes(s)

        # ── BREAK ────────────────────────────────────
        elif "BREAK" in lines:
            self.add("break;")

        # ── CONTINUE ─────────────────────────────────
        elif "CONTINUE" in lines:
            self.add("continue;")

        # ── RETURN ───────────────────────────────────
        elif any(l.startswith("RETURN ") for l in lines):
            ret_line = next(
                l for l in lines
                if l.startswith("RETURN ")
            )
            val = ret_line[7:].strip()
            self.add(f"return {val};")

        # ── Normal statements ─────────────────────────
        else:
            for line in lines:
                if not line or \
                   line in skip_labels or \
                   line.startswith("FUNCTION ") or \
                   line.startswith("END ") or \
                   line.startswith("FOR NEXT:") or \
                   line.startswith("FOR COND:") or \
                   line.startswith("FOR INIT:"):
                    continue

                # Clean up line
                clean = self._clean_line(line)
                if clean:
                    self.add(f"{clean};")

            # Continue to successors
            for succ in successors:
                self._walk_nodes(succ)

    def _clean_line(self, line: str) -> str:
        """Convert CFG instruction to C statement."""
        line = line.strip()

        # Skip structural keywords
        skip = {
            "MERGE", "Empty", "START",
            "LOOP EXIT", "FOR EXIT",
        }
        if line in skip:
            return ""
        if line.startswith("END ") or \
           line.startswith("FUNCTION "):
            return ""

        # Handle CALL
        if line.startswith("CALL:"):
            return line.replace("CALL:", "").strip()
        if line.startswith("CALL "):
            return line[5:].strip()

        # Handle Decl with assignment
        if line.startswith("Decl ") or \
           line.startswith("DECL "):
            rest = re.sub(
                r'^(Decl|DECL)\s+', '', line
            )
            if "=" in rest:
                var, val = rest.split("=", 1)
                return f"int {var.strip()} = {val.strip()}"
            return f"int {rest.strip()}"

        # Regular assignment
        if "=" in line and \
           not line.startswith("IF") and \
           not line.startswith("WHILE") and \
           not line.startswith("FOR"):
            return line

        return line


def generate_optimized_c(G: nx.DiGraph) -> str:
    """Public function to generate C code from CFG."""
    generator = CCodeGenerator(G)
    return generator.generate()