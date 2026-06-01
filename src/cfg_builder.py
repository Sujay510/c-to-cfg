from pycparser import c_ast
import networkx as nx


def expr_to_str(expr):
    if expr is None:
        return ""
    if isinstance(expr, c_ast.ID):
        return expr.name
    elif isinstance(expr, c_ast.Constant):
        return expr.value
    elif isinstance(expr, c_ast.BinaryOp):
        return (f"({expr_to_str(expr.left)} "
                f"{expr.op} "
                f"{expr_to_str(expr.right)})")
    elif isinstance(expr, c_ast.UnaryOp):
        return f"{expr.op}{expr_to_str(expr.expr)}"
    elif isinstance(expr, c_ast.Assignment):
        return (f"{expr_to_str(expr.lvalue)} "
                f"{expr.op} "
                f"{expr_to_str(expr.rvalue)}")
    elif isinstance(expr, c_ast.FuncCall):
        args = ""
        if expr.args:
            args = ", ".join(
                expr_to_str(a) for a in expr.args.exprs
            )
        return f"{expr.name.name}({args})"
    elif isinstance(expr, c_ast.ArrayRef):
        return (f"{expr_to_str(expr.name)}"
                f"[{expr_to_str(expr.subscript)}]")
    elif isinstance(expr, c_ast.StructRef):
        return (f"{expr_to_str(expr.name)}"
                f"{expr.type}"
                f"{expr_to_str(expr.field)}")
    elif isinstance(expr, c_ast.Cast):
        return f"({expr_to_str(expr.expr)})"
    elif isinstance(expr, c_ast.ExprList):
        return ", ".join(expr_to_str(e) for e in expr.exprs)
    elif isinstance(expr, c_ast.DeclList):
        return ", ".join(expr_to_str(d) for d in expr.decls)
    elif isinstance(expr, c_ast.Decl):
        if expr.init:
            return f"{expr.name} = {expr_to_str(expr.init)}"
        return expr.name
    else:
        return type(expr).__name__


class CFGBuilder:
    def __init__(self):
        self.G = nx.DiGraph()
        self.node_id = 0

    def new_block(self, statements):
        nid = self.node_id
        self.node_id += 1
        label = "\n".join(statements) if statements else "Empty"
        self.G.add_node(nid, label=label)
        return nid

    def build(self, ast):
        start = self.new_block(["START"])

        for ext in ast.ext:
            if isinstance(ext, c_ast.FuncDef):
                func_entry = self.new_block(
                    [f"FUNCTION {ext.decl.name}"]
                )
                self.G.add_edge(start, func_entry)
                end = self.process_block(
                    ext.body, func_entry, loop_stack=[]
                )
                func_end = self.new_block(
                    [f"END {ext.decl.name}"]
                )
                self.G.add_edge(end, func_end)

        return self.G

    def process_block(self, block, prev, loop_stack=None):
        if loop_stack is None:
            loop_stack = []

        current_stmts = []

        if isinstance(block, c_ast.Compound):
            stmts = block.block_items or []
        else:
            stmts = [block]

        for stmt in stmts:

            # ── IF ───────────────────────────────────────────
            if isinstance(stmt, c_ast.If):
                if current_stmts:
                    node = self.new_block(current_stmts)
                    self.G.add_edge(prev, node)
                    prev = node
                    current_stmts = []

                cond = expr_to_str(stmt.cond)
                cond_node = self.new_block([f"IF ({cond})"])
                self.G.add_edge(prev, cond_node)

                true_end = self.process_block(
                    stmt.iftrue, cond_node, loop_stack
                )

                if stmt.iffalse:
                    false_end = self.process_block(
                        stmt.iffalse, cond_node, loop_stack
                    )
                else:
                    false_end = cond_node

                merge = self.new_block(["MERGE"])
                self.G.add_edge(true_end, merge)
                self.G.add_edge(false_end, merge)
                prev = merge

            # ── WHILE ────────────────────────────────────────
            elif isinstance(stmt, c_ast.While):
                if current_stmts:
                    node = self.new_block(current_stmts)
                    self.G.add_edge(prev, node)
                    prev = node
                    current_stmts = []

                cond = expr_to_str(stmt.cond)
                cond_node = self.new_block([f"WHILE ({cond})"])
                self.G.add_edge(prev, cond_node)

                exit_node = self.new_block(["LOOP EXIT"])
                loop_stack.append((cond_node, exit_node))

                body_end = self.process_block(
                    stmt.stmt, cond_node, loop_stack
                )
                self.G.add_edge(body_end, cond_node)
                self.G.add_edge(cond_node, exit_node)

                loop_stack.pop()
                prev = exit_node

            # ── FOR ──────────────────────────────────────────
            elif isinstance(stmt, c_ast.For):
                if current_stmts:
                    node = self.new_block(current_stmts)
                    self.G.add_edge(prev, node)
                    prev = node
                    current_stmts = []

                init     = expr_to_str(stmt.init)
                cond     = expr_to_str(stmt.cond)
                next_exp = expr_to_str(stmt.next)

                init_node = self.new_block(
                    [f"FOR INIT: {init}"]
                )
                self.G.add_edge(prev, init_node)

                cond_node = self.new_block(
                    [f"FOR COND: ({cond})"]
                )
                self.G.add_edge(init_node, cond_node)

                exit_node = self.new_block(["FOR EXIT"])
                loop_stack.append((cond_node, exit_node))

                body_end = self.process_block(
                    stmt.stmt, cond_node, loop_stack
                )

                next_node = self.new_block(
                    [f"FOR NEXT: {next_exp}"]
                )
                self.G.add_edge(body_end, next_node)
                self.G.add_edge(next_node, cond_node)
                self.G.add_edge(cond_node, exit_node)

                loop_stack.pop()
                prev = exit_node

            # ── DO WHILE ─────────────────────────────────────
            elif isinstance(stmt, c_ast.DoWhile):
                if current_stmts:
                    node = self.new_block(current_stmts)
                    self.G.add_edge(prev, node)
                    prev = node
                    current_stmts = []

                body_entry = self.new_block(["DO"])
                self.G.add_edge(prev, body_entry)

                cond     = expr_to_str(stmt.cond)
                cond_node = self.new_block(
                    [f"WHILE ({cond})"]
                )
                exit_node = self.new_block(["LOOP EXIT"])
                loop_stack.append((cond_node, exit_node))

                body_end = self.process_block(
                    stmt.stmt, body_entry, loop_stack
                )
                self.G.add_edge(body_end, cond_node)
                self.G.add_edge(cond_node, body_entry)
                self.G.add_edge(cond_node, exit_node)

                loop_stack.pop()
                prev = exit_node

            # ── SWITCH ───────────────────────────────────────
            elif isinstance(stmt, c_ast.Switch):
                if current_stmts:
                    node = self.new_block(current_stmts)
                    self.G.add_edge(prev, node)
                    prev = node
                    current_stmts = []

                cond = expr_to_str(stmt.cond)
                switch_node = self.new_block(
                    [f"SWITCH ({cond})"]
                )
                self.G.add_edge(prev, switch_node)

                exit_node = self.new_block(["SWITCH EXIT"])
                loop_stack.append((switch_node, exit_node))

                if stmt.stmt and stmt.stmt.block_items:
                    for case in stmt.stmt.block_items:
                        if isinstance(case, c_ast.Case):
                            case_node = self.new_block(
                                [f"CASE {expr_to_str(case.expr)}"]
                            )
                            self.G.add_edge(
                                switch_node, case_node
                            )
                            case_end = self.process_block(
                                c_ast.Compound(case.stmts),
                                case_node, loop_stack
                            )
                            self.G.add_edge(
                                case_end, exit_node
                            )
                        elif isinstance(case, c_ast.Default):
                            def_node = self.new_block(
                                ["DEFAULT"]
                            )
                            self.G.add_edge(
                                switch_node, def_node
                            )
                            def_end = self.process_block(
                                c_ast.Compound(case.stmts),
                                def_node, loop_stack
                            )
                            self.G.add_edge(
                                def_end, exit_node
                            )

                loop_stack.pop()
                prev = exit_node

            # ── BREAK ────────────────────────────────────────
            elif isinstance(stmt, c_ast.Break):
                node = self.new_block(["BREAK"])
                self.G.add_edge(prev, node)
                if loop_stack:
                    _, break_target = loop_stack[-1]
                    if break_target is not None:
                        self.G.add_edge(node, break_target)
                prev = node

            # ── CONTINUE ─────────────────────────────────────
            elif isinstance(stmt, c_ast.Continue):
                node = self.new_block(["CONTINUE"])
                self.G.add_edge(prev, node)
                if loop_stack:
                    cont_target, _ = loop_stack[-1]
                    self.G.add_edge(node, cont_target)
                prev = node

            # ── RETURN ───────────────────────────────────────
            elif isinstance(stmt, c_ast.Return):
                current_stmts.append(
                    f"RETURN {expr_to_str(stmt.expr)}"
                )

            # ── DECL ─────────────────────────────────────────
            elif isinstance(stmt, c_ast.Decl):
                if stmt.init:
                    current_stmts.append(
                        f"{stmt.name} = {expr_to_str(stmt.init)}"
                    )
                else:
                    current_stmts.append(f"Decl {stmt.name}")

            # ── ASSIGNMENT ───────────────────────────────────
            elif isinstance(stmt, c_ast.Assignment):
                current_stmts.append(expr_to_str(stmt))

            # ── FUNCCALL ─────────────────────────────────────
            elif isinstance(stmt, c_ast.FuncCall):
                current_stmts.append(expr_to_str(stmt))

            # ── UNARY (i++, i--) ─────────────────────────────
            elif isinstance(stmt, c_ast.UnaryOp):
                current_stmts.append(expr_to_str(stmt))

            # ── EVERYTHING ELSE ──────────────────────────────
            else:
                current_stmts.append(type(stmt).__name__)

        if current_stmts:
            node = self.new_block(current_stmts)
            self.G.add_edge(prev, node)
            prev = node

        return prev