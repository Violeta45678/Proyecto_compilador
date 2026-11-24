"""
MÓDULO: main.py
PROYECTO FINAL: COMPILADORES - FASES 1 Y 2
Punto de entrada. Uso:
    python main.py <ruta_del_archivo>            # Fase 1 (errores léxicos) + Fase 2
    python main.py <ruta_del_archivo> --tokens   # además muestra todos los tokens (Fase 1 completa)
"""

import sys
from lexer import Lexer
from sintactico import Parser


def mostrar_fase1(tokens, errores_lex, con_tokens: bool):
    """Salida de la Fase 1: tokens y errores léxicos en el orden en que aparecen."""
    if con_tokens:
        print("===== FASE 1: ANÁLISIS LÉXICO =====")
        eventos = [("T", t.line, t.column, t) for t in tokens] + \
                  [("E", e.line, e.column, e) for e in errores_lex]
        eventos.sort(key=lambda x: (x[1], x[2]))
        for tipo, _, _, obj in eventos:
            if tipo == "T":
                lexema = f"'{obj.value}'"
                print(f"[TOKEN] Tipo: {obj.type:<16}| Lexema: {lexema:<14}| "
                      f"Posición: [Línea {obj.line}, Col {obj.column}]")
            else:
                print(f"[ERROR LÉXICO] {obj.message} '{obj.char}' en "
                      f"Posición: [Línea {obj.line}, Col {obj.column}]")
        print(f"\nResumen: {len(tokens)} token(s) válido(s), {len(errores_lex)} error(es) léxico(s).")
        print("\n===== FASE 2: ANÁLISIS SINTÁCTICO =====")
    else:
        for e in errores_lex:
            print(f"[ERROR LÉXICO] {e.message} '{e.char}' en "
                  f"Posición: [Línea {e.line}, Col {e.column}]")


def main() -> int:
    args = [a for a in sys.argv[1:] if a != "--tokens"]
    con_tokens = "--tokens" in sys.argv[1:]
    if len(args) != 1:
        print("Uso: python main.py <ruta_del_archivo> [--tokens]")
        return 1

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    ruta = args[0]
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            codigo = f.read()
    except FileNotFoundError:
        print(f"Error: no se encontró el archivo '{ruta}'.")
        return 1
    except (OSError, UnicodeDecodeError) as e:
        print(f"Error al leer el archivo '{ruta}': {e}")
        return 1

    # Fase 1: análisis léxico
    tokens, errores_lex = Lexer(codigo).tokenize()
    mostrar_fase1(tokens, errores_lex, con_tokens)

    # Fase 2: análisis sintáctico
    ast, errores = Parser(tokens).analizar()
    for e in errores:
        print(f"[ERROR SINTÁCTICO] {e.mensaje} en "
              f"Posición: [Línea {e.linea}, Col {e.columna}]")

    if errores:
        print(f"Errores sintácticos: {len(errores)}")
        return 1

    print("Análisis sintáctico completado sin errores.")
    ast.imprimir()
    print(f"\nErrores léxicos: {len(errores_lex)}")
    print("Errores sintácticos: 0")
    if errores_lex:
        print("Resultado: COMPILACIÓN CON ERRORES LÉXICOS")
        return 1
    print("Resultado: COMPILACIÓN EXITOSA")
    return 0


if __name__ == "__main__":
    sys.exit(main())
