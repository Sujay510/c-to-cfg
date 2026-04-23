from src.parser import parse_c_file
from src.cfg_builder import CFGBuilder
from src.visualizer import visualize_cfg


def main():
    print("Parsing sample.c ...")
    ast = parse_c_file("samples/sample.c")

    print("Building CFG ...")
    builder = CFGBuilder()
    blocks = builder.build(ast)

    print("\n=== CFG Basic Blocks ===")
    for block in blocks:
        print(f"\n{block}")
        for instr in block.instructions:
            print(f"   {instr}")
        print(f"   → successors: {block.successors}")

    print("\nGenerating CFG image ...")
    visualize_cfg(blocks, output_path="cfg_output.png")


if __name__ == "__main__":
    main()