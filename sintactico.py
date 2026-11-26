"""
MÓDULO: sintactico.py
PROYECTO FINAL: COMPILADORES - FASE 2
Analizador sintáctico descendente recursivo (una función por regla de la gramática).
Consume la lista de Token(type, value, line, column) que produce Lexer(code).tokenize().
Construye un AST y recupera errores en modo pánico.
"""

from typing import List, Optional, Tuple
from lexer import Token

TIPOS = {"PR_INT", "PR_FLOAT", "PR_CHAR", "PR_STRING", "PR_BOOL", "PR_VOID"}

# Tokens en los que la recuperación en modo pánico se detiene sin consumirlos.
INICIO_SENTENCIA = TIPOS | {"PR_IF", "PR_ELSE", "PR_WHILE", "PR_FOR",
                            "PR_RETURN", "DELIM_LBRACE"}


# ==============================================================================
# 1. ESTRUCTURAS DE DATOS
# ==============================================================================

class ASTNode:
    """Nodo del árbol. Conserva la línea y la columna de su token de origen."""

    def __init__(self, tipo: str, valor: Optional[str] = None,
                 hijos: Optional[list] = None, linea: int = 0, columna: int = 0,
                 detalle: Optional[str] = None):
        self.tipo = tipo
        self.valor = valor
        self.hijos = hijos if hijos is not None else []
        self.linea = linea
        self.columna = columna
        self.detalle = detalle      # dato extra (p. ej. el tipo de un parámetro)

    def etiqueta(self) -> str:
        texto = self.tipo if self.valor is None else f"{self.tipo}: {self.valor}"
        return texto if self.detalle is None else f"{texto} ({self.detalle})"

    def imprimir(self, prefijo: str = "", ultimo: bool = True, raiz: bool = True):
        if raiz:
            print(self.etiqueta())
            nuevo = ""
        else:
            print(prefijo + ("└── " if ultimo else "├── ") + self.etiqueta())
            nuevo = prefijo + ("    " if ultimo else "│   ")
        for i, hijo in enumerate(self.hijos):
            hijo.imprimir(nuevo, i == len(self.hijos) - 1, False)


class ParseError(Exception):
    def __init__(self, mensaje: str, linea: int, columna: int):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.linea = linea
        self.columna = columna


# ==============================================================================
# 2. PARSER
# ==============================================================================

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = list(tokens)
        if self.tokens:
            u = self.tokens[-1]
            linea, col = u.line, u.column + len(u.value)
        else:
            linea, col = 1, 1
        self.tokens.append(Token("EOF", "", linea, col))     # centinela
        self.pos = 0
        self.errores: List[ParseError] = []

    # ---------------- funciones auxiliares ----------------

    def current(self) -> Token:
        return self.tokens[self.pos]

    def peek(self, n: int = 1) -> Token:
        return self.tokens[min(self.pos + n, len(self.tokens) - 1)]

    def check(self, tipo: str, valor: Optional[str] = None) -> bool:
        t = self.current()
        return t.type == tipo and (valor is None or t.value == valor)

    def advance(self) -> Token:
        t = self.current()
        if t.type != "EOF":
            self.pos += 1
        return t

    def error_esperado(self, descripcion: str) -> ParseError:
        t = self.current()
        encontrado = "fin de archivo" if t.type == "EOF" else f"'{t.value}'"
        return ParseError(f"Se esperaba {descripcion} pero se encontró {encontrado}",
                          t.line, t.column)

    def expect(self, tipo: str, descripcion: str) -> Token:
        if self.check(tipo):
            return self.advance()
        raise self.error_esperado(descripcion)

    def _registrar(self, error: ParseError, inicio: int):
        """Modo pánico: anota el error y descarta tokens hasta un punto de sincronización."""
        self.errores.append(error)
        if self.pos == inicio:          # garantiza avance para no entrar en un ciclo
            self.advance()
        self.sincronizar()

    def sincronizar(self):
        while not self.check("EOF"):
            if self.check("DELIM_SEMICOLON"):
                self.advance()          # ';' cierra la sentencia fallida
                return
            if self.check("DELIM_RBRACE") or self.current().type in INICIO_SENTENCIA:
                return                  # '}' o inicio de sentencia: no se consumen
            self.advance()

    # ---------------- programa ----------------
    # programa -> { elemento } EOF

    def analizar(self) -> Tuple[ASTNode, List[ParseError]]:
        hijos = []
        while not self.check("EOF"):
            inicio = self.pos
            try:
                hijos.append(self.elemento())
            except ParseError as e:
                self._registrar(e, inicio)
        return ASTNode("Programa", None, hijos, 1, 1), self.errores

    # elemento -> funcion | sentencia   (2 tokens de anticipación: tipo ID '(')
    def elemento(self) -> ASTNode:
        if (self.current().type in TIPOS and self.peek(1).type == "ID"
                and self.peek(2).type == "DELIM_LPAREN"):
            return self.funcion()
        return self.sentencia()

    # funcion -> tipo ID '(' [ parametros ] ')' bloque
    def funcion(self) -> ASTNode:
        tipo = self.advance()
        nombre = self.expect("ID", "un identificador")
        self.expect("DELIM_LPAREN", "'('")
        parametros = self.parametros()
        self.expect("DELIM_RPAREN", "')'")
        cuerpo = self.bloque()
        return ASTNode("Funcion", nombre.value,
                       [ASTNode("Parametros", None, parametros, nombre.line, nombre.column), cuerpo],
                       tipo.line, tipo.column, detalle=f"retorna {tipo.value}")

    # parametros -> tipo ID { ',' tipo ID }
    def parametros(self) -> list:
        lista = []
        if self.check("DELIM_RPAREN"):
            return lista
        while True:
            if self.current().type not in TIPOS:
                raise self.error_esperado("un tipo de dato")
            tipo = self.advance()
            nombre = self.expect("ID", "un identificador")
            # La posición es la del nombre (no la del tipo) para que el analizador
            # semántico pueda señalar el parámetro exacto (p. ej. un parámetro repetido).
            lista.append(ASTNode("Parametro", nombre.value, [], nombre.line, nombre.column,
                                 detalle=tipo.value))
            if self.check("DELIM_COMMA"):
                self.advance()
                continue
            return lista

    # ---------------- sentencias ----------------
    # sentencia -> declaracion | if | while | for | return | bloque | ';' | expresion ';'

    def sentencia(self) -> ASTNode:
        t = self.current()
        if t.type in TIPOS:
            return self.declaracion()
        if t.type == "PR_IF":
            return self.sentencia_if()
        if t.type == "PR_WHILE":
            return self.sentencia_while()
        if t.type == "PR_FOR":
            return self.sentencia_for()
        if t.type == "PR_RETURN":
            return self.sentencia_return()
        if t.type == "DELIM_LBRACE":
            return self.bloque()
        if t.type == "DELIM_SEMICOLON":
            self.advance()
            return ASTNode("SentenciaVacia", None, [], t.line, t.column)
        if t.type == "PR_ELSE":
            self.advance()
            self.errores.append(ParseError("'else' sin 'if' correspondiente", t.line, t.column))
            return ASTNode("SentenciaVacia", None, [], t.line, t.column)
        expr = self.expresion()
        self.expect("DELIM_SEMICOLON", "';'")
        return ASTNode("SentenciaExpresion", None, [expr], t.line, t.column)

    # bloque -> '{' { sentencia } '}'
    def bloque(self) -> ASTNode:
        llave = self.expect("DELIM_LBRACE", "'{'")
        hijos = []
        while not self.check("DELIM_RBRACE") and not self.check("EOF"):
            inicio = self.pos
            try:
                hijos.append(self.sentencia())
            except ParseError as e:
                self._registrar(e, inicio)
        self.expect("DELIM_RBRACE", "'}'")
        return ASTNode("Bloque", None, hijos, llave.line, llave.column)

    # declaracion -> tipo declarador { ',' declarador } ';'
    # declarador  -> ID [ '=' expresion ]
    def declaracion(self, consumir_pc: bool = True) -> ASTNode:
        tipo = self.advance()
        nodo = ASTNode("Declaracion", tipo.value, [], tipo.line, tipo.column)
        while True:
            nombre = self.expect("ID", "un identificador")
            var = ASTNode("Variable", nombre.value, [], nombre.line, nombre.column)
            if self.check("OP_ASSIGN"):
                self.advance()
                var.hijos.append(self.expresion())
            nodo.hijos.append(var)
            if self.check("DELIM_COMMA"):
                self.advance()
                continue
            break
        if consumir_pc:
            self.expect("DELIM_SEMICOLON", "';'")
        return nodo

    # if -> 'if' '(' expresion ')' sentencia [ 'else' sentencia ]
    # El 'else' se une al 'if' más cercano (se consume apenas aparece).
    def sentencia_if(self) -> ASTNode:
        kw = self.advance()
        self.expect("DELIM_LPAREN", "'('")
        cond = self.expresion()
        self.expect("DELIM_RPAREN", "')'")
        entonces = self.sentencia()
        hijos = [ASTNode("Condicion", None, [cond], kw.line, kw.column),
                 ASTNode("Entonces", None, [entonces], kw.line, kw.column)]
        if self.check("PR_ELSE"):
            e = self.advance()
            hijos.append(ASTNode("Sino", None, [self.sentencia()], e.line, e.column))
        return ASTNode("If", None, hijos, kw.line, kw.column)

    # while -> 'while' '(' expresion ')' sentencia
    def sentencia_while(self) -> ASTNode:
        kw = self.advance()
        self.expect("DELIM_LPAREN", "'('")
        cond = self.expresion()
        self.expect("DELIM_RPAREN", "')'")
        cuerpo = self.sentencia()
        return ASTNode("While", None,
                       [ASTNode("Condicion", None, [cond], kw.line, kw.column),
                        ASTNode("Cuerpo", None, [cuerpo], kw.line, kw.column)],
                       kw.line, kw.column)

    # for -> 'for' '(' [ declaracion | expresion ] ';' [ expresion ] ';' [ expresion ] ')' sentencia
    def sentencia_for(self) -> ASTNode:
        kw = self.advance()
        self.expect("DELIM_LPAREN", "'('")
        hijos = []
        if self.current().type in TIPOS:
            hijos.append(ASTNode("Inicio", None, [self.declaracion(consumir_pc=False)], kw.line, kw.column))
        elif not self.check("DELIM_SEMICOLON"):
            hijos.append(ASTNode("Inicio", None, [self.expresion()], kw.line, kw.column))
        self.expect("DELIM_SEMICOLON", "';'")
        if not self.check("DELIM_SEMICOLON"):
            hijos.append(ASTNode("Condicion", None, [self.expresion()], kw.line, kw.column))
        self.expect("DELIM_SEMICOLON", "';'")
        if not self.check("DELIM_RPAREN"):
            hijos.append(ASTNode("Actualizacion", None, [self.expresion()], kw.line, kw.column))
        self.expect("DELIM_RPAREN", "')'")
        hijos.append(ASTNode("Cuerpo", None, [self.sentencia()], kw.line, kw.column))
        return ASTNode("For", None, hijos, kw.line, kw.column)

    # return -> 'return' [ expresion ] ';'
    def sentencia_return(self) -> ASTNode:
        kw = self.advance()
        hijos = []
        if not self.check("DELIM_SEMICOLON"):
            hijos.append(self.expresion())
        self.expect("DELIM_SEMICOLON", "';'")
        return ASTNode("Return", None, hijos, kw.line, kw.column)

    # ---------------- expresiones (de menor a mayor precedencia) ----------------
    # expresion      -> asignacion
    # asignacion     -> igualdad [ '=' asignacion ]          (asociativa a la derecha)
    # igualdad       -> relacional { ('==' | '!=') relacional }
    # relacional     -> aditivo { ('<' | '>' | '<=' | '>=') aditivo }
    # aditivo        -> multiplicativo { ('+' | '-') multiplicativo }
    # multiplicativo -> unario { ('*' | '/') unario }
    # unario         -> '-' unario | primario
    # primario       -> ENTERO | FLOTANTE | CADENA | 'true' | 'false'
    #                 | ID [ '(' [ argumentos ] ')' ] | '(' expresion ')'
    # argumentos     -> expresion { ',' expresion }

    def expresion(self) -> ASTNode:
        return self.asignacion()

    def asignacion(self) -> ASTNode:
        izq = self.igualdad()
        if self.check("OP_ASSIGN"):
            op = self.advance()
            valor = self.asignacion()
            if izq.tipo != "Identificador":
                raise ParseError("El lado izquierdo de la asignación debe ser una variable",
                                 op.line, op.column)
            return ASTNode("Asignacion", izq.valor, [valor], izq.linea, izq.columna)
        return izq

    def _binaria(self, siguiente, tipo_op: str, valores: set) -> ASTNode:
        izq = siguiente()
        while self.check(tipo_op) and self.current().value in valores:
            op = self.advance()
            der = siguiente()
            izq = ASTNode("OpBinaria", op.value, [izq, der], op.line, op.column)
        return izq

    def igualdad(self) -> ASTNode:
        return self._binaria(self.relacional, "OP_REL", {"==", "!="})

    def relacional(self) -> ASTNode:
        return self._binaria(self.aditivo, "OP_REL", {"<", ">", "<=", ">="})

    def aditivo(self) -> ASTNode:
        return self._binaria(self.multiplicativo, "OP_ARIT", {"+", "-"})

    def multiplicativo(self) -> ASTNode:
        return self._binaria(self.unario, "OP_ARIT", {"*", "/"})

    def unario(self) -> ASTNode:
        if self.check("OP_ARIT", "-"):
            op = self.advance()
            return ASTNode("OpUnaria", "-", [self.unario()], op.line, op.column)
        return self.primario()

    def primario(self) -> ASTNode:
        t = self.current()
        if t.type == "INT_LITERAL":
            self.advance()
            return ASTNode("Entero", t.value, [], t.line, t.column)
        if t.type == "FLOAT_LITERAL":
            self.advance()
            return ASTNode("Flotante", t.value, [], t.line, t.column)
        if t.type == "STRING_LITERAL":
            self.advance()
            return ASTNode("Cadena", t.value[1:-1], [], t.line, t.column)
        if t.type in ("PR_TRUE", "PR_FALSE"):
            self.advance()
            return ASTNode("Booleano", t.value, [], t.line, t.column)
        if t.type == "ID":
            if self.peek(1).type == "DELIM_LPAREN":
                self.advance()
                self.advance()
                args = []
                if not self.check("DELIM_RPAREN"):
                    args.append(self.expresion())
                    while self.check("DELIM_COMMA"):
                        self.advance()
                        args.append(self.expresion())
                self.expect("DELIM_RPAREN", "')'")
                return ASTNode("Llamada", t.value, args, t.line, t.column)
            self.advance()
            return ASTNode("Identificador", t.value, [], t.line, t.column)
        if t.type == "DELIM_LPAREN":
            self.advance()
            expr = self.expresion()
            self.expect("DELIM_RPAREN", "')'")
            return expr
        raise self.error_esperado("una expresión")
