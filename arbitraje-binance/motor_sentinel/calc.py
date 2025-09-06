#!/usr/bin/env python3
"""
Calculadora CLI simple (sin dependencias externas).

Soporta: suma (+), resta (-), multiplicación (*), división (/),
división entera (//), módulo (%), potencia (**), y paréntesis.

Uso rápido:
  python calc.py "2+3*4"        -> 14
  python calc.py "(10-3)/2"     -> 3.5
  python calc.py                 # modo interactivo (REPL)
"""

from __future__ import annotations

import argparse
import ast
import operator as op
import sys
from typing import Union


# Operadores permitidos
BIN_OPS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.FloorDiv: op.floordiv,
    ast.Mod: op.mod,
    ast.Pow: op.pow,
}

UNARY_OPS = {
    ast.UAdd: op.pos,
    ast.USub: op.neg,
}


Number = Union[int, float]


def _eval(node: ast.AST) -> Number:
    if isinstance(node, ast.Expression):
        return _eval(node.body)

    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Sólo se permiten números (int/float)")

    if isinstance(node, ast.Num):  # compatibilidad con versiones antiguas
        return node.n  # type: ignore[attr-defined]

    if isinstance(node, ast.BinOp):
        if type(node.op) not in BIN_OPS:
            raise ValueError("Operador binario no permitido")
        left = _eval(node.left)
        right = _eval(node.right)
        try:
            return BIN_OPS[type(node.op)](left, right)  # type: ignore[index]
        except ZeroDivisionError:
            raise ValueError("División por cero")

    if isinstance(node, ast.UnaryOp):
        if type(node.op) not in UNARY_OPS:
            raise ValueError("Operador unario no permitido")
        operand = _eval(node.operand)
        return UNARY_OPS[type(node.op)](operand)  # type: ignore[index]

    if isinstance(node, ast.Paren):  # no existe como nodo; paréntesis se reflejan en el árbol
        return _eval(node.value)  # pragma: no cover

    raise ValueError("Expresión no soportada")


def safe_eval(expr: str) -> Number:
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as e:
        raise ValueError(f"Sintaxis inválida: {e.msg}")

    # Validar que el árbol contenga sólo nodos esperados
    for node in ast.walk(tree):
        if isinstance(node, (ast.Load, ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant, ast.Num, *BIN_OPS.keys(), *UNARY_OPS.keys())):
            continue
        # Prohibir nombres, llamadas, atributos, etc.
        if isinstance(node, (ast.Name, ast.Call, ast.Attribute, ast.Subscript, ast.Dict, ast.List, ast.Tuple)):
            raise ValueError("Sólo se permiten operaciones aritméticas básicas")
    return _eval(tree)


def repl() -> int:
    print("Calculadora simple. Escribe una expresión o 'exit'/'quit'.")
    while True:
        try:
            line = input("calc> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not line:
            continue
        if line.lower() in {"exit", "quit"}:
            return 0
        try:
            result = safe_eval(line)
            # Imprimir como int si corresponde
            if isinstance(result, float) and result.is_integer():
                print(int(result))
            else:
                print(result)
        except ValueError as e:
            print(f"error: {e}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Calculadora aritmética simple")
    parser.add_argument("expr", nargs="?", help="Expresión a evaluar, p.ej. '2+2*3'")
    args = parser.parse_args(argv)
    if not args.expr:
        return repl()
    try:
        result = safe_eval(args.expr)
    except ValueError as e:
        parser.exit(2, f"error: {e}\n")
    if isinstance(result, float) and result.is_integer():
        print(int(result))
    else:
        print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

