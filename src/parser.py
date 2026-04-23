from pycparser import c_parser, c_ast
import re

def parse_c_file(filepath: str) -> c_ast.FileAST:
    parser = c_parser.CParser()

    with open(filepath, 'r') as f:
        code = f.read()

    # Remove /* block comments */
    code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)

    # Remove // line comments
    code = re.sub(r'//.*?\n', '\n', code)

    # Remove #include lines
    code = re.sub(r'#include\s*[<"][^>"]*[>"]', '', code)

    # Remove #define lines
    code = re.sub(r'#define\s+.*?\n', '\n', code)

    ast = parser.parse(code, filename=filepath)
    return ast