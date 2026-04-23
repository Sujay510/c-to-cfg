from pycparser import c_ast
from .basic_blocks import BasicBlock, BasicBlockBuilder


class CFGBuilder(c_ast.NodeVisitor):
    def __init__(self):
        self.builder = BasicBlockBuilder()
        self.current_block = self.builder.new_block(label="Entry")

    def build(self, ast):
        self.visit(ast)
        exit_block = self.builder.new_block(label="Exit")
        self.builder.add_edge(self.current_block.id, exit_block.id)
        return self.builder.blocks

    # ─── FUNCTION DEFINITION ─────────────────────────────────
    def visit_FuncDef(self, node):
        # Each function gets its OWN entry block
        # connected from the global START (block 0)
        func_entry = self.builder.new_block(
            label=f"Func:{node.decl.name}"
        )
        # Connect START → this function
        self.builder.add_edge(0, func_entry.id)
        func_entry.instructions.append(
            f"FUNCTION {node.decl.name}()"
        )
        self.current_block = func_entry
        # Visit function body
        self.visit(node.body)
        # Add function exit
        func_exit = self.builder.new_block(
            label=f"FuncExit:{node.decl.name}"
        )
        self.builder.add_edge(self.current_block.id, func_exit.id)
        func_exit.instructions.append(
            f"END {node.decl.name}"
        )
        self.current_block = func_exit

    # ─── IF / ELSE ───────────────────────────────────────────
    def visit_If(self, node):
        cond_block = self.current_block
        cond_block.instructions.append(
            f"IF {self._node_to_str(node.cond)}"
        )

        # True branch
        true_block = self.builder.new_block(label="If_True")
        self.builder.add_edge(cond_block.id, true_block.id)
        self.current_block = true_block
        self.visit(node.iftrue)
        true_end = self.current_block

        # False branch
        false_block = self.builder.new_block(label="If_False")
        self.builder.add_edge(cond_block.id, false_block.id)
        self.current_block = false_block
        if node.iffalse:
            self.visit(node.iffalse)
        false_end = self.current_block

        # Merge block
        merge_block = self.builder.new_block(label="Merge")
        self.builder.add_edge(true_end.id, merge_block.id)
        self.builder.add_edge(false_end.id, merge_block.id)
        self.current_block = merge_block

    # ─── FOR LOOP ────────────────────────────────────────────
    def visit_For(self, node):
        if node.init:
            self.current_block.instructions.append(
                f"FOR_INIT {self._node_to_str(node.init)}"
            )

        cond_block = self.builder.new_block(label="For_Cond")
        self.builder.add_edge(self.current_block.id, cond_block.id)
        if node.cond:
            cond_block.instructions.append(
                f"FOR_COND {self._node_to_str(node.cond)}"
            )

        body_block = self.builder.new_block(label="For_Body")
        self.builder.add_edge(cond_block.id, body_block.id)
        self.current_block = body_block
        if node.stmt:
            self.visit(node.stmt)

        if node.next:
            self.current_block.instructions.append(
                f"FOR_INC {self._node_to_str(node.next)}"
            )

        self.builder.add_edge(self.current_block.id, cond_block.id)

        after_block = self.builder.new_block(label="For_Exit")
        self.builder.add_edge(cond_block.id, after_block.id)
        self.current_block = after_block

    # ─── WHILE LOOP ──────────────────────────────────────────
    def visit_While(self, node):
        cond_block = self.builder.new_block(label="While_Cond")
        self.builder.add_edge(self.current_block.id, cond_block.id)
        cond_block.instructions.append(
            f"WHILE {self._node_to_str(node.cond)}"
        )

        body_block = self.builder.new_block(label="While_Body")
        self.builder.add_edge(cond_block.id, body_block.id)
        self.current_block = body_block
        self.visit(node.stmt)

        self.builder.add_edge(self.current_block.id, cond_block.id)

        after_block = self.builder.new_block(label="While_Exit")
        self.builder.add_edge(cond_block.id, after_block.id)
        self.current_block = after_block

    # ─── DO WHILE LOOP ───────────────────────────────────────
    def visit_DoWhile(self, node):
        body_block = self.builder.new_block(label="DoWhile_Body")
        self.builder.add_edge(self.current_block.id, body_block.id)
        self.current_block = body_block
        self.visit(node.stmt)

        cond_block = self.builder.new_block(label="DoWhile_Cond")
        self.builder.add_edge(self.current_block.id, cond_block.id)
        cond_block.instructions.append(
            f"DO_WHILE {self._node_to_str(node.cond)}"
        )

        self.builder.add_edge(cond_block.id, body_block.id)
        after_block = self.builder.new_block(label="DoWhile_Exit")
        self.builder.add_edge(cond_block.id, after_block.id)
        self.current_block = after_block

    # ─── SWITCH ──────────────────────────────────────────────
    def visit_Switch(self, node):
        self.current_block.instructions.append(
            f"SWITCH {self._node_to_str(node.cond)}"
        )
        switch_block = self.current_block
        after_block = self.builder.new_block(label="Switch_Exit")

        if node.stmt:
            for case in node.stmt.block_items or []:
                case_block = self.builder.new_block(label="Case")
                self.builder.add_edge(switch_block.id, case_block.id)
                self.current_block = case_block
                if isinstance(case, c_ast.Case):
                    case_block.instructions.append(
                        f"CASE {self._node_to_str(case.expr)}"
                    )
                    for stmt in case.stmts or []:
                        self.visit(stmt)
                elif isinstance(case, c_ast.Default):
                    case_block.instructions.append("DEFAULT")
                    for stmt in case.stmts or []:
                        self.visit(stmt)
                self.builder.add_edge(
                    self.current_block.id, after_block.id
                )

        self.current_block = after_block

    # ─── FUNCTION CALL ───────────────────────────────────────
    def visit_FuncCall(self, node):
        name = self._node_to_str(node.name)
        args = ""
        if node.args:
            args = ", ".join(
                self._node_to_str(a) for a in node.args.exprs
            )
        self.current_block.instructions.append(
            f"CALL {name}({args})"
        )

    # ─── DECLARATIONS ────────────────────────────────────────
    def visit_Decl(self, node):
        if node.init:
            self.current_block.instructions.append(
                f"DECL {node.name} = {self._node_to_str(node.init)}"
            )
        else:
            self.current_block.instructions.append(
                f"DECL {node.name}"
            )

    # ─── ASSIGNMENTS ─────────────────────────────────────────
    def visit_Assignment(self, node):
        self.current_block.instructions.append(
            f"{self._node_to_str(node.lvalue)} "
            f"{node.op} "
            f"{self._node_to_str(node.rvalue)}"
        )

    # ─── RETURN ──────────────────────────────────────────────
    def visit_Return(self, node):
        self.current_block.instructions.append(
            f"RETURN {self._node_to_str(node.expr)}"
        )

    # ─── UNARY (i++, i--) ────────────────────────────────────
    def visit_UnaryOp(self, node):
        self.current_block.instructions.append(
            f"UNARY {node.op}{self._node_to_str(node.expr)}"
        )

    # ─── BREAK / CONTINUE ────────────────────────────────────
    def visit_Break(self, node):
        self.current_block.instructions.append("BREAK")

    def visit_Continue(self, node):
        self.current_block.instructions.append("CONTINUE")

    # ─── HELPER ──────────────────────────────────────────────
    def _node_to_str(self, node) -> str:
        if node is None:
            return ""
        if isinstance(node, c_ast.ID):
            return node.name
        if isinstance(node, c_ast.Constant):
            return node.value
        if isinstance(node, c_ast.BinaryOp):
            return (
                f"{self._node_to_str(node.left)} "
                f"{node.op} "
                f"{self._node_to_str(node.right)}"
            )
        if isinstance(node, c_ast.UnaryOp):
            return f"{node.op}{self._node_to_str(node.expr)}"
        if isinstance(node, c_ast.ArrayRef):
            return (
                f"{self._node_to_str(node.name)}"
                f"[{self._node_to_str(node.subscript)}]"
            )
        if isinstance(node, c_ast.StructRef):
            return (
                f"{self._node_to_str(node.name)}"
                f"{node.type}"
                f"{self._node_to_str(node.field)}"
            )
        if isinstance(node, c_ast.Cast):
            return f"({self._node_to_str(node.expr)})"
        if isinstance(node, c_ast.ExprList):
            return ", ".join(
                self._node_to_str(e) for e in node.exprs
            )
        if isinstance(node, c_ast.Assignment):
            return (
                f"{self._node_to_str(node.lvalue)} "
                f"{node.op} "
                f"{self._node_to_str(node.rvalue)}"
            )
        if isinstance(node, c_ast.FuncCall):
            name = self._node_to_str(node.name)
            args = ""
            if node.args:
                args = ", ".join(
                    self._node_to_str(a)
                    for a in node.args.exprs
                )
            return f"{name}({args})"
        if isinstance(node, c_ast.DeclList):
            return ", ".join(
                self._node_to_str(d) for d in node.decls
            )
        return type(node).__name__