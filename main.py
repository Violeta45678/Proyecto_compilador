"""
MÓDULO: main.py
PROYECTO FINAL: COMPILADORES - FASE 1
Punto de entrada. Uso: python main.py <ruta_del_archivo>
"""

import sys
from lexer import Lexer


def main() -> int:
    if len(sys.argv) != 2:
        print("Uso: python main.py <ruta_del_archivo>")
        return 1

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    ruta = sys.argv[1]
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            codigo = f.read()
    except FileNotFoundError:
        print(f"Error: no se encontró el archivo '{ruta}'.")
        return 1
    except (OSError, UnicodeDecodeError) as e:
        print(f"Error al leer el archivo '{ruta}': {e}")
        return 1

    tokens, errores = Lexer(codigo).tokenize()

    # Tokens y errores en el orden en que aparecen en el archivo
    eventos = [("T", t.line, t.column, t) for t in tokens] + \
              [("E", e.line, e.column, e) for e in errores]
    eventos.sort(key=lambda x: (x[1], x[2]))

    for tipo, _, _, obj in eventos:
        if tipo == "T":
            lexema = f"'{obj.value}'"
            print(f"[TOKEN] Tipo: {obj.type:<16}| Lexema: {lexema:<14}| "
                  f"Posición: [Línea {obj.line}, Col {obj.column}]")
        else:
            print(f"[ERROR LÉXICO] {obj.message} '{obj.char}' en "
                  f"Posición: [Línea {obj.line}, Col {obj.column}]")

    print(f"\nResumen: {len(tokens)} token(s) válido(s), {len(errores)} error(es) léxico(s).")
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
