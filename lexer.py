"""
MÓDULO: lexer.py
PROYECTO FINAL: COMPILADORES - FASE 1
Analizador Léxico (Scanner) implementado con expresiones regulares (módulo 're').
"""

import re
from typing import List, Tuple, NamedTuple

# ==============================================================================
# 1. ESTRUCTURAS DE DATOS
# ==============================================================================

class Token(NamedTuple):
    """Estructura para representar un Token detectado."""
    type: str
    value: str
    line: int
    column: int

class LexicalError(NamedTuple):
    """Estructura para representar un error léxico detectado."""
    message: str
    char: str
    line: int
    column: int

# ==============================================================================
# 2. CLASE PRINCIPAL DEL ANALIZADOR LÉXICO
# ==============================================================================

class Lexer:
    """
    Analizador Léxico (Scanner).
    Transforma una cadena de código fuente en una lista de Tokens y Errores Léxicos.
    """

    # Mapeo de palabras reservadas a su tipo de Token exacto
    KEYWORD_MAP = {
        'int': 'PR_INT',
        'float': 'PR_FLOAT',
        'char': 'PR_CHAR',
        'string': 'PR_STRING',
        'bool': 'PR_BOOL',
        'void': 'PR_VOID',
        'if': 'PR_IF',
        'else': 'PR_ELSE',
        'while': 'PR_WHILE',
        'for': 'PR_FOR',
        'return': 'PR_RETURN',
        'break': 'PR_BREAK',
        'continue': 'PR_CONTINUE',
        'true': 'PR_TRUE',
        'false': 'PR_FALSE',
    }

    # Patrones en orden de prioridad (el primero que coincide gana).
    # IMPORTANTE: usar solo grupos NO capturantes (?:...) dentro de los patrones.
    TOKEN_SPECIFICATION = [
        # --- ELEMENTOS A IGNORAR / ESPACIOS ---
        ('NEWLINE',        r'\n'),
        ('SKIP',           r'[ \t\r]+'),

        # --- COMENTARIOS ---
        ('COMMENT_SINGLE', r'//[^\n]*'),
        ('COMMENT_MULTI',  r'/\*[\s\S]*?\*/'),
        ('UNTERMINATED_COMMENT', r'/\*[\s\S]*'),   # /* sin su */

        # --- LITERALES ---
        ('STRING_LITERAL', r'"(?:[^"\\\n]|\\.)*"'),
        ('UNTERMINATED_STRING', r'"(?:[^"\\\n]|\\.)*\\?'),  # " sin cerrar en la línea
        ('MALFORMED_NUMBER', r'[0-9]+(?:\.[0-9]+)?[A-Za-z_][A-Za-z0-9_]*'),  # ej: 123abc
        ('FLOAT_LITERAL',  r'[0-9]+\.[0-9]+'),
        ('INT_LITERAL',    r'[0-9]+'),

        # --- PALABRAS RESERVADAS E IDENTIFICADORES ---
        ('KEYWORD',        r'\b(?:' + '|'.join(KEYWORD_MAP) + r')\b'),
        ('ID',             r'[A-Za-z_][A-Za-z0-9_]*'),

        # --- OPERADORES ---
        ('OP_REL',         r'==|!=|<=|>=|<|>'),   # antes que '=' para que '==' no se parta
        ('OP_ASSIGN',      r'='),
        ('OP_ARIT',        r'[+\-*/]'),

        # --- DELIMITADORES ---
        ('DELIM_LPAREN',   r'\('),
        ('DELIM_RPAREN',   r'\)'),
        ('DELIM_LBRACE',   r'\{'),
        ('DELIM_RBRACE',   r'\}'),
        ('DELIM_COMMA',    r','),
        ('DELIM_SEMICOLON', r';'),

        # Comodín para cualquier otro carácter no reconocido (Error Léxico)
        ('MISMATCH',       r'.'),
    ]

    def __init__(self, code: str):
        self.code = code
        # Compila la expresión regular combinando todos los grupos etiquetados
        tok_regex = '|'.join(f'(?P<{pair[0]}>{pair[1]})' for pair in self.TOKEN_SPECIFICATION)
        self.regex = re.compile(tok_regex)

    def tokenize(self) -> Tuple[List[Token], List[LexicalError]]:
        """
        Procesa el código fuente completo y retorna una tupla con:
        - Lista de Tokens válidos
        - Lista de Errores Léxicos encontrados
        """
        tokens: List[Token] = []
        errors: List[LexicalError] = []

        line_num = 1
        line_start = 0

        for mo in self.regex.finditer(self.code):
            kind = mo.lastgroup
            value = mo.group()
            position = mo.start()
            col_num = position - line_start + 1

            if kind == 'NEWLINE':
                line_start = mo.end()
                line_num += 1

            elif kind == 'SKIP' or kind == 'COMMENT_SINGLE':
                continue

            elif kind in ('COMMENT_MULTI', 'UNTERMINATED_COMMENT'):
                if kind == 'UNTERMINATED_COMMENT':
                    errors.append(LexicalError(
                        "Comentario multilínea sin cerrar", value[:2] + '...', line_num, col_num))
                # Actualizar conteo de líneas con los saltos de línea del comentario
                newlines = value.count('\n')
                if newlines:
                    line_num += newlines
                    line_start = position + value.rfind('\n') + 1

            elif kind == 'KEYWORD':
                tokens.append(Token(self.KEYWORD_MAP[value], value, line_num, col_num))

            elif kind == 'UNTERMINATED_STRING':
                errors.append(LexicalError("Cadena sin cerrar", value, line_num, col_num))

            elif kind == 'MALFORMED_NUMBER':
                errors.append(LexicalError("Número mal formado", value, line_num, col_num))

            elif kind == 'MISMATCH':
                errors.append(LexicalError("Carácter no reconocido", value, line_num, col_num))

            else:
                tokens.append(Token(kind, value, line_num, col_num))

        return tokens, errors
