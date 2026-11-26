"""
MÓDULO: semantico.py
PROYECTO FINAL: COMPILADORES - FASE 3
Analizador semántico: recorre el AST de la Fase 2, construye la Tabla de Símbolos con
ámbitos anidados, verifica tipos y el uso correcto de variables y funciones, y reporta
los errores semánticos con su línea y columna.

El recorrido usa un método por cada tipo de nodo (visit_If, visit_Asignacion, ...).
Los métodos de expresiones devuelven el tipo calculado ('int', 'float', 'string' o
'error') y lo guardan en el nodo (atributo `tipo_calculado`) para la opción --ast.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from sintactico import ASTNode

# ==============================================================================
# 1. CONSTANTES DEL SISTEMA DE TIPOS
# ==============================================================================

T_INT, T_FLOAT, T_STRING, T_VOID = "int", "float", "string", "void"
T_ERROR = "error"                       # tipo de una expresión que ya produjo un error
NUMERICOS = (T_INT, T_FLOAT)
TIPOS_VALIDOS = (T_INT, T_FLOAT, T_STRING, T_VOID)
OPERADORES_ARIT = ("+", "-", "*", "/")


# ==============================================================================
# 2. ESTRUCTURAS DE DATOS
# ==============================================================================

@dataclass
class Symbol:
    """Entrada de la tabla de símbolos."""
    nombre: str
    categoria: str                      # 'variable' | 'parametro' | 'funcion'
    tipo: str                           # tipo de la variable/parámetro; tipo de retorno si es función
    ambito: str
    linea: int                          # línea de declaración
    columna: int = 0
    tipos_parametros: Optional[List[str]] = None   # solo funciones
    predefinida: bool = False
    usado: bool = False                 # ¿se leyó alguna vez? (advertencias)
    asignado: bool = True               # ¿ya recibió un valor? (advertencias)
    advertido: bool = False

    @property
    def tipo_retorno(self) -> Optional[str]:
        return self.tipo if self.categoria == "funcion" else None

    def tipo_texto(self) -> str:
        """Variables: 'float'. Funciones: 'retorno(tipos de parámetros)'."""
        if self.categoria == "funcion":
            return f"{self.tipo}({', '.join(self.tipos_parametros or [])})"
        return self.tipo


@dataclass
class SemanticError:
    mensaje: str
    linea: int
    columna: int

    def __str__(self) -> str:
        return (f"[ERROR SEMÁNTICO] {self.mensaje} en "
                f"Posición: [Línea {self.linea}, Col {self.columna}]")


@dataclass
class SemanticWarning:
    mensaje: str
    linea: int
    columna: int

    def __str__(self) -> str:
        return (f"[ADVERTENCIA] {self.mensaje} en "
                f"Posición: [Línea {self.linea}, Col {self.columna}]")


class Scope:
    """Un ámbito: sus símbolos y una referencia al ámbito que lo contiene."""

    def __init__(self, nombre: str, padre: Optional["Scope"] = None):
        self.nombre = nombre
        self.padre = padre
        self.simbolos: Dict[str, Symbol] = {}


class SymbolTable:
    """Pila de ámbitos. Además guarda TODOS los símbolos declarados (incluso los de
    ámbitos ya cerrados) en orden de declaración, para imprimir la tabla al final."""

    def __init__(self):
        self.global_scope = Scope("global")
        self.actual = self.global_scope
        self.todos: List[Symbol] = []
        # imprimir(...) existe sin declararse: acepta cualquier cantidad y tipo de argumentos
        self.predefinidas: Dict[str, Symbol] = {
            "imprimir": Symbol("imprimir", "funcion", T_VOID, "global", 0,
                               tipos_parametros=None, predefinida=True),
        }

    # --- ámbitos ---
    def abrir_ambito(self, etiqueta: str) -> Scope:
        """El ámbito de una función se llama como ella; los internos: 'main > bloque L12'."""
        if self.actual is self.global_scope:
            nombre = etiqueta
        else:
            nombre = f"{self.actual.nombre} > {etiqueta}"
        self.actual = Scope(nombre, self.actual)
        return self.actual

    def cerrar_ambito(self) -> Scope:
        cerrado = self.actual
        self.actual = cerrado.padre
        return cerrado

    # --- símbolos ---
    def declarar(self, simbolo: Symbol) -> None:
        self.actual.simbolos[simbolo.nombre] = simbolo
        self.todos.append(simbolo)

    def buscar_local(self, nombre: str) -> Optional[Symbol]:
        return self.actual.simbolos.get(nombre)

    def buscar(self, nombre: str) -> Optional[Symbol]:
        """Busca desde el ámbito actual hacia afuera, hasta el global."""
        ambito = self.actual
        while ambito is not None:
            if nombre in ambito.simbolos:
                return ambito.simbolos[nombre]
            ambito = ambito.padre
        return self.predefinidas.get(nombre)


# ==============================================================================
# 3. REGLAS DE TIPOS
# ==============================================================================

def tipo_binario(op: str, a: str, b: str) -> Optional[str]:
    """Tipo resultante de `a op b`, o None si la combinación no es válida."""
    if a in NUMERICOS and b in NUMERICOS:
        if op in OPERADORES_ARIT:
            return T_FLOAT if T_FLOAT in (a, b) else T_INT    # promoción int -> float
        return T_INT                                          # relacionales e igualdad: 1 / 0
    if a == T_STRING and b == T_STRING:
        if op == "+":
            return T_STRING                                   # concatenación
        if op in ("==", "!="):
            return T_INT
    return None


def es_compatible(destino: str, origen: str) -> bool:
    """¿Se puede asignar un valor de tipo `origen` a algo de tipo `destino`?"""
    if T_ERROR in (destino, origen):
        return True                                           # no generar errores en cascada
    if destino == origen and destino in (T_INT, T_FLOAT, T_STRING):
        return True
    return destino == T_FLOAT and origen == T_INT             # promoción implícita


# ==============================================================================
# 4. ANALIZADOR SEMÁNTICO
# ==============================================================================

class AnalizadorSemantico:
    def __init__(self, advertencias: bool = False):
        self.tabla = SymbolTable()
        self.errores: List[SemanticError] = []
        self.advertencias: List[SemanticWarning] = []
        self.con_advertencias = advertencias
        self.funcion_actual: Optional[Tuple[str, str]] = None   # (nombre, tipo de retorno)

    # ---------------- utilidades ----------------

    def analizar(self, ast: ASTNode) -> List[SemanticError]:
        self.visit(ast)
        return self.errores

    def error(self, mensaje: str, linea: int, columna: int) -> None:
        self.errores.append(SemanticError(mensaje, linea, columna))

    def advertir(self, mensaje: str, linea: int, columna: int) -> None:
        if self.con_advertencias:
            self.advertencias.append(SemanticWarning(mensaje, linea, columna))

    def visit(self, nodo: ASTNode):
        """Despacha al método visit_<TipoDeNodo>; si no existe, recorre los hijos."""
        metodo = getattr(self, f"visit_{nodo.tipo}", self.visit_generico)
        return metodo(nodo)

    def visit_generico(self, nodo: ASTNode):
        for hijo in nodo.hijos:
            self.visit(hijo)

    def tipo_de(self, nodo: ASTNode, tipo: str) -> str:
        """Guarda el tipo calculado en el nodo (para --ast) y lo devuelve."""
        nodo.tipo_calculado = tipo
        return tipo

    def ya_declarado(self, categoria: str, nombre: str, previo: Symbol,
                     linea: int, columna: int) -> None:
        etiqueta = {"variable": "Variable", "parametro": "Parámetro", "funcion": "Función"}[categoria]
        sufijo = "o" if categoria == "parametro" else "a"
        self.error(f"{etiqueta} '{nombre}' ya declarad{sufijo} en este ámbito "
                   f"(Línea {previo.linea})", linea, columna)

    def tipo_efectivo(self, tipo: str) -> str:
        """Los tipos del lenguaje son int, float, string y void; char/bool se tratan como error."""
        return tipo if tipo in TIPOS_VALIDOS else T_ERROR

    def verificar_asignacion(self, destino: str, origen: str, nombre: str,
                             linea: int, columna: int) -> bool:
        if es_compatible(destino, origen):
            return True
        self.error(f"Tipos incompatibles: no se puede asignar '{origen}' a "
                   f"'{nombre}' de tipo '{destino}'", linea, columna)
        return False

    def verificar_condicion(self, palabra: str, tipo: str, expr: ASTNode) -> None:
        if tipo not in NUMERICOS and tipo != T_ERROR:
            self.error(f"La condición del '{palabra}' debe ser numérica, se encontró '{tipo}'",
                       expr.linea, expr.columna)

    # ---------------- programa y declaraciones ----------------

    def visit_Programa(self, nodo: ASTNode):
        for hijo in nodo.hijos:
            self.visit(hijo)

    def visit_Funcion(self, nodo: ASTNode):
        parametros, cuerpo = nodo.hijos
        nombre = nodo.valor
        retorno = (nodo.detalle or "").replace("retorna ", "")
        linea_n, col_n = parametros.linea, parametros.columna      # posición del nombre
        if retorno in ("char", "bool"):
            self.error(f"El tipo '{retorno}' no está soportado "
                       f"(tipos válidos: int, float, string, void)", nodo.linea, nodo.columna)
        retorno = self.tipo_efectivo(retorno)

        previo = self.tabla.buscar_local(nombre)
        if previo is not None:
            self.ya_declarado("funcion", nombre, previo, linea_n, col_n)
        else:
            # Se registra ANTES de analizar el cuerpo: permite la recursión
            self.tabla.declarar(Symbol(
                nombre, "funcion", retorno, self.tabla.actual.nombre, nodo.linea, col_n,
                tipos_parametros=[p.detalle for p in parametros.hijos]))

        self.tabla.abrir_ambito(nombre)
        anterior = self.funcion_actual
        self.funcion_actual = (nombre, retorno)
        for p in parametros.hijos:
            self.visit(p)
        for sentencia in cuerpo.hijos:       # el cuerpo comparte el ámbito de los parámetros
            self.visit(sentencia)
        self.funcion_actual = anterior
        self.revisar_no_usados(self.tabla.cerrar_ambito())

    def visit_Parametro(self, nodo: ASTNode):
        nombre, tipo = nodo.valor, nodo.detalle
        if tipo in ("char", "bool"):
            self.error(f"El tipo '{tipo}' no está soportado "
                       f"(tipos válidos: int, float, string)", nodo.linea, nodo.columna)
            tipo = T_ERROR
        elif tipo == T_VOID:
            self.error(f"El parámetro '{nombre}' no puede ser de tipo 'void'",
                       nodo.linea, nodo.columna)
            tipo = T_ERROR
        previo = self.tabla.buscar_local(nombre)
        if previo is not None:
            self.ya_declarado("parametro", nombre, previo, nodo.linea, nodo.columna)
            return
        self.tabla.declarar(Symbol(nombre, "parametro", tipo, self.tabla.actual.nombre,
                                   nodo.linea, nodo.columna))

    def visit_Declaracion(self, nodo: ASTNode):
        tipo = nodo.valor
        if tipo in ("char", "bool"):
            self.error(f"El tipo '{tipo}' no está soportado "
                       f"(tipos válidos: int, float, string)", nodo.linea, nodo.columna)
            tipo = T_ERROR
        for variable in nodo.hijos:
            self.declarar_variable(tipo, variable)

    def declarar_variable(self, tipo: str, variable: ASTNode):
        nombre = variable.valor
        if tipo == T_VOID:
            self.error(f"La variable '{nombre}' no puede ser de tipo 'void'",
                       variable.linea, variable.columna)
            tipo = T_ERROR
        previo = self.tabla.buscar_local(nombre)
        if previo is not None:
            self.ya_declarado("variable", nombre, previo, variable.linea, variable.columna)
        if variable.hijos:
            # La inicialización se evalúa antes de registrar la variable: `int x = x;`
            # no puede usar la variable que se está declarando.
            tipo_expr = self.visit(variable.hijos[0])
            self.verificar_asignacion(tipo, tipo_expr, nombre, variable.linea, variable.columna)
        if previo is None:
            es_global = self.tabla.actual is self.tabla.global_scope
            self.tabla.declarar(Symbol(
                nombre, "variable", tipo, self.tabla.actual.nombre, variable.linea,
                variable.columna, asignado=bool(variable.hijos) or es_global))
        variable.tipo_calculado = tipo

    # ---------------- sentencias ----------------

    def visit_Bloque(self, nodo: ASTNode):
        self.tabla.abrir_ambito(f"bloque L{nodo.linea}")
        for sentencia in nodo.hijos:
            self.visit(sentencia)
        self.revisar_no_usados(self.tabla.cerrar_ambito())

    def visit_SentenciaVacia(self, nodo: ASTNode):
        pass

    def visit_SentenciaExpresion(self, nodo: ASTNode):
        expr = nodo.hijos[0]
        if expr.tipo == "Llamada":
            self.evaluar_llamada(expr, permitir_void=True)   # `saludar();` sí es válido
        else:
            self.visit(expr)

    def visit_If(self, nodo: ASTNode):
        condicion = nodo.hijos[0].hijos[0]
        self.verificar_condicion("if", self.visit(condicion), condicion)
        self.visit(nodo.hijos[1].hijos[0])                   # rama 'entonces'
        if len(nodo.hijos) > 2:
            self.visit(nodo.hijos[2].hijos[0])               # rama 'sino'

    def visit_While(self, nodo: ASTNode):
        condicion = nodo.hijos[0].hijos[0]
        self.verificar_condicion("while", self.visit(condicion), condicion)
        self.visit(nodo.hijos[1].hijos[0])

    def visit_For(self, nodo: ASTNode):
        self.tabla.abrir_ambito(f"for L{nodo.linea}")        # el 'for' abre su propio ámbito
        for parte in nodo.hijos:
            if parte.tipo == "Condicion":
                expr = parte.hijos[0]
                self.verificar_condicion("for", self.visit(expr), expr)
            elif parte.tipo == "Cuerpo":
                self.visit(parte.hijos[0])
            else:                                            # Inicio | Actualizacion
                for hijo in parte.hijos:
                    self.visit(hijo)
        self.revisar_no_usados(self.tabla.cerrar_ambito())

    def visit_Return(self, nodo: ASTNode):
        tipo_valor = self.visit(nodo.hijos[0]) if nodo.hijos else None
        if self.funcion_actual is None:
            self.error("'return' fuera de una función", nodo.linea, nodo.columna)
            return
        nombre, retorno = self.funcion_actual
        if retorno == T_VOID:
            if tipo_valor is not None:
                self.error(f"La función '{nombre}' es de tipo 'void' y no puede retornar un valor",
                           nodo.linea, nodo.columna)
        elif tipo_valor is None:
            if retorno != T_ERROR:
                self.error(f"La función '{nombre}' debe retornar un valor de tipo '{retorno}'",
                           nodo.linea, nodo.columna)
        elif not es_compatible(retorno, tipo_valor):
            self.error(f"La función '{nombre}' retorna '{retorno}' pero el valor retornado "
                       f"es de tipo '{tipo_valor}'", nodo.linea, nodo.columna)

    # ---------------- expresiones (devuelven el tipo calculado) ----------------

    def visit_Entero(self, nodo: ASTNode):
        return self.tipo_de(nodo, T_INT)

    def visit_Flotante(self, nodo: ASTNode):
        return self.tipo_de(nodo, T_FLOAT)

    def visit_Cadena(self, nodo: ASTNode):
        return self.tipo_de(nodo, T_STRING)

    def visit_Booleano(self, nodo: ASTNode):
        self.error(f"El valor '{nodo.valor}' no está soportado "
                   f"(tipos válidos: int, float, string)", nodo.linea, nodo.columna)
        return self.tipo_de(nodo, T_ERROR)

    def visit_Identificador(self, nodo: ASTNode):
        simbolo = self.tabla.buscar(nodo.valor)
        if simbolo is None:
            self.error(f"Variable '{nodo.valor}' no declarada", nodo.linea, nodo.columna)
            return self.tipo_de(nodo, T_ERROR)
        if simbolo.categoria == "funcion":
            self.error(f"'{nodo.valor}' es una función y no puede usarse como variable",
                       nodo.linea, nodo.columna)
            return self.tipo_de(nodo, T_ERROR)
        simbolo.usado = True
        if not simbolo.asignado and not simbolo.advertido:
            simbolo.advertido = True
            self.advertir(f"La variable '{nodo.valor}' se usa antes de recibir un valor",
                          nodo.linea, nodo.columna)
        return self.tipo_de(nodo, simbolo.tipo)

    def visit_Asignacion(self, nodo: ASTNode):
        nombre = nodo.valor
        simbolo = self.tabla.buscar(nombre)
        destino: str
        if simbolo is None:
            self.error(f"Variable '{nombre}' no declarada", nodo.linea, nodo.columna)
            destino = T_ERROR
        elif simbolo.categoria == "funcion":
            self.error(f"'{nombre}' es una función y no puede usarse como variable",
                       nodo.linea, nodo.columna)
            destino = T_ERROR
        else:
            destino = simbolo.tipo
        tipo_valor = self.visit(nodo.hijos[0])               # se analiza siempre, para ver sus errores
        if simbolo is not None and simbolo.categoria != "funcion":
            simbolo.asignado = True
        if destino == T_ERROR:
            return self.tipo_de(nodo, T_ERROR)
        if not self.verificar_asignacion(destino, tipo_valor, nombre, nodo.linea, nodo.columna):
            return self.tipo_de(nodo, T_ERROR)
        return self.tipo_de(nodo, destino)

    def visit_OpBinaria(self, nodo: ASTNode):
        izq, der = nodo.hijos
        t_izq, t_der = self.visit(izq), self.visit(der)
        if nodo.valor == "/" and der.tipo in ("Entero", "Flotante") and float(der.valor) == 0:
            self.advertir("División entre la constante 0", nodo.linea, nodo.columna)
        if T_ERROR in (t_izq, t_der):
            return self.tipo_de(nodo, T_ERROR)               # sin errores en cascada
        resultado = tipo_binario(nodo.valor, t_izq, t_der)
        if resultado is None:
            self.error(f"Operador '{nodo.valor}' no aplicable entre '{t_izq}' y '{t_der}'",
                       nodo.linea, nodo.columna)
            return self.tipo_de(nodo, T_ERROR)
        return self.tipo_de(nodo, resultado)

    def visit_OpUnaria(self, nodo: ASTNode):
        tipo = self.visit(nodo.hijos[0])
        if tipo == T_ERROR:
            return self.tipo_de(nodo, T_ERROR)
        if tipo not in NUMERICOS:
            self.error(f"Operador '{nodo.valor}' no aplicable a '{tipo}'", nodo.linea, nodo.columna)
            return self.tipo_de(nodo, T_ERROR)
        return self.tipo_de(nodo, tipo)

    def visit_Llamada(self, nodo: ASTNode):
        return self.evaluar_llamada(nodo, permitir_void=False)

    def evaluar_llamada(self, nodo: ASTNode, permitir_void: bool) -> str:
        nombre = nodo.valor
        tipos_args = [self.visit(arg) for arg in nodo.hijos]  # los argumentos se analizan siempre
        simbolo = self.tabla.buscar(nombre)
        if simbolo is None:
            self.error(f"Función '{nombre}' no declarada", nodo.linea, nodo.columna)
            return self.tipo_de(nodo, T_ERROR)
        if simbolo.categoria != "funcion":
            que = "una variable" if simbolo.categoria == "variable" else "un parámetro"
            self.error(f"'{nombre}' es {que} y no puede llamarse como función",
                       nodo.linea, nodo.columna)
            return self.tipo_de(nodo, T_ERROR)
        simbolo.usado = True
        if not simbolo.predefinida:                          # imprimir(...) acepta cualquier cosa
            esperados = simbolo.tipos_parametros or []
            if len(esperados) != len(tipos_args):
                self.error(f"La función '{nombre}' espera {len(esperados)} argumento(s) "
                           f"pero recibió {len(tipos_args)}", nodo.linea, nodo.columna)
            else:
                for i, (esperado, recibido) in enumerate(zip(esperados, tipos_args), start=1):
                    if not es_compatible(esperado, recibido):
                        arg = nodo.hijos[i - 1]
                        self.error(f"Argumento {i} de la función '{nombre}': no se puede pasar "
                                   f"'{recibido}' a un parámetro de tipo '{esperado}'",
                                   arg.linea, arg.columna)
        if simbolo.tipo == T_VOID and not permitir_void:
            self.error(f"La función '{nombre}' es de tipo 'void' y no puede usarse en una expresión",
                       nodo.linea, nodo.columna)
            return self.tipo_de(nodo, T_ERROR)
        return self.tipo_de(nodo, simbolo.tipo)

    # ---------------- advertencias ----------------

    def revisar_no_usados(self, ambito: Scope) -> None:
        """Advertencia: variables locales declaradas que nunca se leen."""
        if not self.con_advertencias:
            return
        for s in ambito.simbolos.values():
            if s.categoria == "variable" and not s.usado:
                self.advertir(f"La variable '{s.nombre}' fue declarada pero nunca se usa",
                              s.linea, s.columna)

    # ---------------- reporte ----------------

    def imprimir_reporte(self) -> None:
        print("=== ANÁLISIS SEMÁNTICO ===")
        for e in self.errores:
            print(e)
        if not self.errores:
            print("Análisis semántico completado sin errores.")
        for w in self.advertencias:
            print(w)
        print()
        self.imprimir_tabla()
        print()
        print(f"Errores semánticos: {len(self.errores)}")
        if self.con_advertencias:
            print(f"Advertencias: {len(self.advertencias)}")
        if self.errores:
            print(f"Resultado: {len(self.errores)} error(es) encontrados")
        else:
            print("Resultado: COMPILACIÓN EXITOSA")

    def imprimir_tabla(self) -> None:
        print("=== TABLA DE SÍMBOLOS ===")
        filas = [(s.nombre, s.categoria, s.tipo_texto(), s.ambito, str(s.linea))
                 for s in self.tabla.todos]
        encabezado = ("Nombre", "Categoría", "Tipo", "Ámbito", "Línea")
        minimos = (18, 10, 15, 20, 5)
        anchos = [max(m, len(h), *(len(f[i]) for f in filas)) if filas else max(m, len(h))
                  for i, (h, m) in enumerate(zip(encabezado, minimos))]
        def linea(c):
            return (f"{c[0]:<{anchos[0]}} | {c[1]:<{anchos[1]}} | {c[2]:<{anchos[2]}} | "
                    f"{c[3]:<{anchos[3]}} | {c[4]}")
        print(linea(encabezado))
        print("+".join(["-" * (anchos[0] + 1)] + ["-" * (a + 2) for a in anchos[1:-1]]
                       + ["-" * (anchos[-1] + 1)]))
        for f in filas:
            print(linea(f))


# ==============================================================================
# 5. AST DECORADO (opción --ast)
# ==============================================================================

def imprimir_ast_decorado(nodo: ASTNode, prefijo: str = "", ultimo: bool = True,
                          raiz: bool = True) -> None:
    """Igual que ASTNode.imprimir, pero agrega el tipo calculado: 'OpBinaria: * [float]'."""
    etiqueta = nodo.etiqueta()
    tipo = getattr(nodo, "tipo_calculado", None)
    if tipo is not None:
        etiqueta += f" [{tipo}]"
    if raiz:
        print(etiqueta)
        nuevo = ""
    else:
        print(prefijo + ("└── " if ultimo else "├── ") + etiqueta)
        nuevo = prefijo + ("    " if ultimo else "│   ")
    for i, hijo in enumerate(nodo.hijos):
        imprimir_ast_decorado(hijo, nuevo, i == len(nodo.hijos) - 1, False)
