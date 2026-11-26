"""
MÓDULO: main.py
PROYECTO FINAL: COMPILADORES - FASES 1, 2 Y 3
Punto de entrada. Ejecuta en orden: análisis léxico, sintáctico y semántico.

Uso:
    python main.py <ruta_del_archivo> [--tokens] [--ast] [--advertencias]

    --tokens        muestra todos los tokens (Fase 1 completa)
    --ast           imprime el AST decorado con el tipo calculado de cada expresión
    --advertencias  activa las advertencias [ADVERTENCIA] (variables sin usar, usadas
                    antes de recibir un valor y división entre la constante 0)
"""

import sys
from lexer import Lexer
from sintactico import Parser
from semantico import AnalizadorSemantico, imprimir_ast_decorado


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
    opciones = {"--tokens", "--ast", "--advertencias"}
    args = [a for a in sys.argv[1:] if a not in opciones]
    con_tokens = "--tokens" in sys.argv[1:]
    con_ast = "--ast" in sys.argv[1:]
    con_advertencias = "--advertencias" in sys.argv[1:]
    if len(args) != 1:
        print("Uso: python main.py <ruta_del_archivo> [--tokens] [--ast] [--advertencias]")
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
    ast, errores_sint = Parser(tokens).analizar()
    for e in errores_sint:
        print(f"[ERROR SINTÁCTICO] {e.mensaje} en "
              f"Posición: [Línea {e.linea}, Col {e.columna}]")

    # Fase 3: solo si el AST está completo (sin errores léxicos ni sintácticos)
    if errores_lex or errores_sint:
        print("Análisis semántico omitido: corrija primero los errores anteriores.")
        return 1

    analizador = AnalizadorSemantico(advertencias=con_advertencias)
    analizador.analizar(ast)
    analizador.imprimir_reporte()
    if con_ast:
        print("\n=== AST DECORADO ===")
        imprimir_ast_decorado(ast)
    return 1 if analizador.errores else 0


if __name__ == "__main__":
    sys.exit(main())
