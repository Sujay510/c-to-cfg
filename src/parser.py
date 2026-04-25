from pycparser import c_parser, c_ast
import re


def parse_c_file(filepath: str) -> c_ast.FileAST:
    """Parse a C file and return its AST."""
    with open(filepath, 'r') as f:
        code = f.read()
    return parse_c_code(code, filepath)


def parse_c_code(code: str,
                 filepath: str = "<string>") -> c_ast.FileAST:
    """Clean and parse C code string, return AST."""

    # ── Step 1: Remove block comments /* ... */ ───────────────
    code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)

    # ── Step 2: Remove line comments // ... ───────────────────
    code = re.sub(r'//[^\n]*', '', code)

    # ── Step 3: Remove #include lines ────────────────────────
    code = re.sub(r'#include\s*[<"][^>"]*[>"]', '', code)

    # ── Step 4: Remove #define lines ─────────────────────────
    code = re.sub(r'#define[^\n]*', '', code)

    # ── Step 5: Remove #pragma lines ─────────────────────────
    code = re.sub(r'#pragma[^\n]*', '', code)

    # ── Step 6: Remove #ifndef / #ifdef / #endif lines ───────
    code = re.sub(r'#(ifndef|ifdef|endif|else|elif)[^\n]*',
                  '', code)

    # ── Step 7: Remove blank lines (cleanup) ─────────────────
    code = re.sub(r'\n\s*\n', '\n\n', code)

    # ── Parse ─────────────────────────────────────────────────
    parser = c_parser.CParser()
    try:
        ast = parser.parse(code, filename=filepath)
        return ast
    except Exception as e:
        print(f"\n❌ Parse Error in {filepath}:")
        print(f"   {e}")
        print("\n── Cleaned Code ──")
        for i, line in enumerate(code.splitlines(), 1):
            print(f"  {i:3}: {line}")
        raise