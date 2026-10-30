"""
Command-line interface for the Mini Compiler. Useful for showing the output
of each phase (the web page only shows the program output and tokens).

Usage:
    python cli.py program.txt            # program output, errors and warnings
    python cli.py program.txt --all      # every phase
    python cli.py program.txt --tokens --tac
"""

import argparse
import sys

from compiler import compile_source


def heading(title):
    print(f"\n=== {title} " + "=" * max(0, 60 - len(title)))


def print_tree(node, indent=0):
    role = f"{node['role']}: " if node.get("role") else ""
    detail = f" {node['detail']}" if node["detail"] else ""
    dtype = f" : {node['dtype']}" if node["dtype"] else ""
    print("  " * indent + f"{role}{node['label']}{detail}{dtype}")
    for child in node["children"]:
        print_tree(child, indent + 1)


def print_code(lines):
    for number, line in enumerate(lines, 1):
        indent = "" if line.endswith(":") else "    "  # labels start at the margin
        print(f"{number:3}  {indent}{line}")


def main():
    parser = argparse.ArgumentParser(description="Mini Compiler for If-Else statements")
    parser.add_argument("file", help="source file to compile")
    parser.add_argument("--tokens", action="store_true", help="show the token list (lexer)")
    parser.add_argument("--ast", action="store_true", help="show the syntax tree (parser)")
    parser.add_argument("--symbols", action="store_true", help="show the symbol table (semantic analyzer)")
    parser.add_argument("--tac", action="store_true", help="show the three-address code (ICG)")
    parser.add_argument("--opt", action="store_true", help="show the optimized three-address code")
    parser.add_argument("--all", action="store_true", help="show every phase")
    args = parser.parse_args()

    try:
        with open(args.file, encoding="utf-8") as handle:
            source = handle.read()
    except OSError as error:
        print(f"error: cannot read {args.file}: {error.strerror}")
        return 2

    result = compile_source(source)

    if (args.tokens or args.all) and result["tokens"]:
        heading("Tokens")
        for token in result["tokens"]:
            print(f"  {token['line']:>3}:{token['column']:<3} {token['type']:<15} {token['value']}")

    if (args.ast or args.all) and result["ast"]:
        heading("Syntax Tree")
        print_tree(result["ast"])

    if (args.symbols or args.all) and result["symbol_table"]:
        heading("Symbol Table")
        print(f"  {'Name':<12} {'Type':<6} {'Scope':<10} {'Line':<5} Uses")
        for symbol in result["symbol_table"]:
            print(f"  {symbol['name']:<12} {symbol['type']:<6} {symbol['scope']:<10} "
                  f"{symbol['line']:<5} {symbol['used']}")

    if (args.tac or args.all) and result["tac"]:
        heading("Three-Address Code")
        print_code(result["tac"])

    if (args.opt or args.all) and result["tac"] and result["failed_phase"] != "ICG":
        heading("Optimized Three-Address Code")
        print_code(result["optimized_tac"])

    heading("Phases")
    print("  " + "  ->  ".join(f"{p['name']} [{p['status']}]" for p in result["phases"]))

    if result["success"] or result["output"]:
        heading("Program Output")
        print("\n".join(result["output"]) if result["output"] else "(no output)")

    for warning in result["warnings"]:
        print(f"warning [{warning['phase']}] {warning['text']}")
    for error in result["errors"]:
        print(f"error   [{error['phase']}] {error['text']}")

    return 0 if result["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
