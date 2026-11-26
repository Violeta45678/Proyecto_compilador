# Proyecto Final: Compiladores

Analizador léxico (Fase 1), sintáctico (Fase 2) y semántico (Fase 3) en Python, implementados a mano, sin generadores automáticos ni librerías de terceros.

**Integrantes:**
- Violeta Sofia Martinez Puente
- Dalila Astrid Murcia Medina
- Marelin Valeriana Romualdo Leonor

Universidad de Sonsonate, Ingeniería en Sistemas Computacionales. Curso: Compiladores.

## Estructura del repositorio

```
.
├── main.py          # Punto de entrada (Fases 1, 2 y 3)
├── lexer.py         # Analizador léxico (Fase 1)
├── sintactico.py    # Analizador sintáctico y AST (Fase 2)
├── semantico.py     # Tabla de símbolos y análisis semántico (Fase 3)
├── GRAMATICA.md     # Gramática EBNF, precedencia y recuperación de errores
├── tests/
│   ├── caso_valido.txt              # válido para la Fase 3
│   ├── caso_error.txt               # un error de cada chequeo obligatorio (Fase 3)
│   ├── ejemplo_enunciado_1.txt      # ejemplo 1 del enunciado de la Fase 3
│   ├── ejemplo_enunciado_2.txt      # ejemplo 2 del enunciado de la Fase 3
│   ├── caso_valido_fase2.txt        # casos válidos de la Fase 2
│   ├── caso_valido_expresiones.txt
│   ├── caso_valido_control.txt
│   ├── caso_valido_funciones.txt
│   ├── caso_error_sintactico.txt    # errores sintácticos (Fase 2)
│   └── caso_error_lexico.txt        # errores léxicos (Fase 1)
├── .gitignore
└── README.md
```

## Requisitos

- Python 3.8 o superior
- Sin dependencias externas

---

# Fase 1: Análisis Léxico

Lee un archivo de texto con código fuente, reconoce los tokens del lenguaje y reporta los errores léxicos con su línea y columna. Usa una expresión regular del módulo nativo `re`.

## Ejecución

```bash
python main.py <ruta_del_archivo> --tokens
```

Con `--tokens` se imprime cada token y cada error léxico en el orden en que aparecen en el archivo. Sin esa opción solo se imprimen los errores léxicos y se continúa con la Fase 2.

```bash
python main.py tests/caso_valido_fase2.txt --tokens
python main.py tests/caso_error_lexico.txt --tokens
```

## Componentes reconocidos

| Categoría | Tipo de token | Elementos |
|---|---|---|
| Palabras reservadas | `PR_INT`, `PR_FLOAT`, `PR_CHAR`, `PR_STRING`, `PR_BOOL`, `PR_VOID`, `PR_IF`, `PR_ELSE`, `PR_WHILE`, `PR_FOR`, `PR_RETURN`, `PR_BREAK`, `PR_CONTINUE`, `PR_TRUE`, `PR_FALSE` | `int`, `float`, `char`, `string`, `bool`, `void`, `if`, `else`, `while`, `for`, `return`, `break`, `continue`, `true`, `false` |
| Identificadores | `ID` | Letra o `_` seguida de letras, dígitos o `_` |
| Enteros | `INT_LITERAL` | `[0-9]+` |
| Flotantes | `FLOAT_LITERAL` | `[0-9]+.[0-9]+` |
| Cadenas | `STRING_LITERAL` | Texto entre comillas dobles, con secuencias de escape (`\"`, `\\`) |
| Operadores aritméticos | `OP_ARIT` | `+` `-` `*` `/` |
| Operadores relacionales | `OP_REL` | `==` `!=` `<` `>` `<=` `>=` |
| Asignación | `OP_ASSIGN` | `=` |
| Delimitadores | `DELIM_LPAREN`, `DELIM_RPAREN`, `DELIM_LBRACE`, `DELIM_RBRACE`, `DELIM_COMMA`, `DELIM_SEMICOLON` | `(` `)` `{` `}` `,` `;` |

Se ignoran espacios, tabulaciones, saltos de línea y comentarios (`// ...` y `/* ... */`). Sus saltos de línea se cuentan para que la posición de los tokens siguientes sea correcta.

## Errores léxicos

El analizador no se detiene ante un error: lo registra y sigue con el resto del archivo.

| Error | Ejemplo | Qué consume |
|---|---|---|
| Carácter no reconocido | `$`, `@`, `#` | El carácter |
| Cadena sin cerrar | `"hola` | Hasta el final de la línea |
| Número mal formado | `123abc` | El número junto con las letras que lo siguen |
| Comentario multilínea sin cerrar | `/* ...` | Hasta el final del archivo |

## Formato de salida

```
[TOKEN] Tipo: PR_INT          | Lexema: 'int'         | Posición: [Línea 1, Col 1]
[TOKEN] Tipo: ID              | Lexema: 'limite'      | Posición: [Línea 1, Col 5]
[TOKEN] Tipo: OP_ASSIGN       | Lexema: '='           | Posición: [Línea 1, Col 12]
[ERROR LÉXICO] Carácter no reconocido '$' en Posición: [Línea 1, Col 14]
[TOKEN] Tipo: INT_LITERAL     | Lexema: '100'         | Posición: [Línea 1, Col 16]
```

## Decisiones de diseño (Fase 1)

- **Técnica:** una sola expresión regular compilada con grupos con nombre unidos con `|`. Se recorre con `finditer` y el primer patrón que coincide gana, por lo que el orden de `TOKEN_SPECIFICATION` importa (por ejemplo, `==` y `<=` van antes que `=` y `<`).
- **Palabras reservadas:** se reconocen con `\b` y se mapean con `KEYWORD_MAP`. `int` es `PR_INT`, pero `integer` es `ID`.
- **Posición:** línea y columna empiezan en 1; la columna es la posición del lexema menos el inicio de la línea actual.
- **Estructuras:** `Token(type, value, line, column)` y `LexicalError(message, char, line, column)`, ambas `NamedTuple`.
- **Errores:** los casos mal formados tienen su propio patrón para dar un mensaje específico; el resto cae en el comodín `MISMATCH`.

---

# Fase 2: Análisis Sintáctico

Parser descendente recursivo (una función por regla de la gramática) que consume la lista de tokens de la Fase 1, verifica la gramática, construye un AST y reporta errores sintácticos con línea y columna.

## Ejecución

```bash
python main.py <ruta_del_archivo>
```

```bash
python main.py tests/caso_valido_fase2.txt --ast
python main.py tests/caso_error_sintactico.txt
```

Primero se ejecuta el análisis léxico y se imprimen sus errores, y luego el sintáctico. Con `--ast` se imprime el AST con sangría (en la Fase 3 el árbol ya incluye el tipo calculado de cada expresión). El programa devuelve código 0 si la compilación es exitosa y 1 en caso contrario.

## Construcciones soportadas

- Declaración de variables, con o sin inicialización y varias por línea: `int a = 1, b;`
- Asignaciones: `x = y + 2;` y encadenadas `a = b = c = 0;`
- Expresiones aritméticas y relacionales con paréntesis y menos unario
- Estructuras de control: `if`, `if-else` (incluido `else if`), `while` y `for` (con sus tres partes opcionales)
- Bloques con llaves y sentencia vacía `;`
- Declaración de funciones con parámetros y tipo de retorno
- Llamadas a funciones con argumentos, anidadas y recursivas
- `return` con o sin valor

La gramática completa en EBNF, la tabla de precedencia y los puntos de sincronización están en [`GRAMATICA.md`](GRAMATICA.md).

## Precedencia y asociatividad

| Nivel | Operadores | Asociatividad |
|---|---|---|
| 1 (menor) | `=` | derecha |
| 2 | `==` `!=` | izquierda |
| 3 | `<` `>` `<=` `>=` | izquierda |
| 4 | `+` `-` | izquierda |
| 5 | `*` `/` | izquierda |
| 6 (mayor) | `-` unario, paréntesis | derecha |

## Ejemplo de salida

Entrada `int x = factorial(5);`:

```
Análisis sintáctico completado sin errores.
Programa
└── Declaracion: int
    └── Variable: x
        └── Llamada: factorial
            └── Entero: 5

Errores léxicos: 0
Errores sintácticos: 0
Resultado: COMPILACIÓN EXITOSA
```

Salida de `tests/caso_error_sintactico.txt`:

```
[ERROR SINTÁCTICO] Se esperaba ';' pero se encontró 'int' en Posición: [Línea 2, Col 1]
[ERROR SINTÁCTICO] Se esperaba ')' pero se encontró ';' en Posición: [Línea 3, Col 15]
[ERROR SINTÁCTICO] Se esperaba una expresión pero se encontró '*' en Posición: [Línea 4, Col 5]
[ERROR SINTÁCTICO] 'else' sin 'if' correspondiente en Posición: [Línea 5, Col 1]
[ERROR SINTÁCTICO] Se esperaba ')' pero se encontró '{' en Posición: [Línea 6, Col 11]
[ERROR SINTÁCTICO] Se esperaba un tipo de dato pero se encontró ')' en Posición: [Línea 9, Col 14]
[ERROR SINTÁCTICO] El lado izquierdo de la asignación debe ser una variable en Posición: [Línea 12, Col 7]
[ERROR SINTÁCTICO] Se esperaba '}' pero se encontró fin de archivo en Posición: [Línea 14, Col 15]
Errores sintácticos: 8
```

## Casos de prueba

| Archivo | Descripción |
|---|---|
| `tests/caso_valido_fase2.txt` | Programa completo con todas las construcciones: declaraciones, funciones, `if-else`, `for`, `while`, llamadas y `return`. |
| `tests/caso_valido_expresiones.txt` | Precedencia, asociatividad y paréntesis. |
| `tests/caso_valido_control.txt` | Estructuras de control anidadas, `for(;;)`, bloques y sentencia vacía. |
| `tests/caso_valido_funciones.txt` | Funciones, parámetros, llamadas anidadas y recursión. |
| `tests/caso_error_sintactico.txt` | Ocho errores sintácticos de seis tipos distintos (`;` faltante, `)` faltante, expresión incompleta, `else` sin `if`, parámetro sin tipo, asignación a algo que no es variable, `}` sin cerrar), todos reportados en una sola ejecución. |
| `tests/caso_error_lexico.txt` | Seis errores léxicos (Fase 1). |

## Decisiones de diseño (Fase 2)

- **Una función por regla:** cada regla de la gramática es un método de `Parser` (`sentencia_if`, `aditivo`, `primario`, etc.), con la regla escrita como comentario encima.
- **Precedencia en la gramática:** una regla por nivel, de menor a mayor precedencia. La asociatividad por la izquierda se resuelve con un ciclo y la de `=` con recursión sobre `asignacion`.
- **Lookahead:** función y declaración empiezan igual (`tipo ID`), así que `elemento` mira dos tokens más adelante: si el tercero es `(`, es una función. Llamada e identificador se distinguen con un token (`ID` seguido de `(`).
- **`else` ambiguo:** se une al `if` más cercano porque el parser consume el `else` en cuanto aparece tras la sentencia del `if`. Un `else` suelto se reporta como error y se descarta solo ese token.
- **Asignación válida:** `asignacion` parsea el lado izquierdo como expresión y después verifica que sea un identificador; si no, reporta error. Así `a + 1 = 5;` se detecta sin complicar la gramática.
- **Recuperación en modo pánico:** al fallar una regla se lanza `ParseError`, que se captura en el ciclo del programa o del bloque. `sincronizar()` descarta tokens hasta un `;` (se consume), un `}` o el inicio de una sentencia (no se consumen). Si el error ocurre sin avanzar ningún token, se descarta uno para evitar un ciclo infinito.
- **AST para la Fase 3:** cada `ASTNode` guarda tipo, valor, hijos, línea y columna de su token de origen. Solo se imprime si no hubo errores sintácticos.


---

# Fase 3: Análisis Semántico

Recorre el AST de la Fase 2 con un visitante (`visit_<TipoDeNodo>`), construye la tabla de símbolos con ámbitos anidados, calcula el tipo de cada expresión y reporta los errores semánticos con línea y columna. Solo se ejecuta si el programa no tiene errores léxicos ni sintácticos; en ese caso se imprime `Análisis semántico omitido: corrija primero los errores anteriores.`

## Ejecución

```bash
python main.py <ruta_del_archivo> [--tokens] [--ast] [--advertencias]
```

```bash
python main.py tests/caso_valido.txt
python main.py tests/caso_error.txt
python main.py tests/caso_valido.txt --ast --advertencias
```

| Opción | Efecto |
|---|---|
| `--tokens` | Imprime los tokens de la Fase 1. |
| `--ast` | Imprime el AST decorado con el tipo de cada expresión (extra). |
| `--advertencias` | Activa las `[ADVERTENCIA]` por variables declaradas y no usadas (extra). No cuentan como errores. |

El programa devuelve 0 si la compilación es exitosa y 1 si hay errores de cualquier fase.

## Reglas de tipos

Tipos: `int`, `float`, `string`, `void` y un tipo interno `error` que se usa para no encadenar mensajes.

| Operación | Operandos | Resultado |
|---|---|---|
| `+` `-` `*` `/` | `int`, `int` | `int` |
| `+` `-` `*` `/` | `int`/`float` con al menos un `float` | `float` (el `int` se promueve) |
| `+` | `string`, `string` | `string` (concatenación) |
| `-` `*` `/` | con `string` | error |
| `<` `>` `<=` `>=` | numéricos | `int` (0 o 1) |
| `==` `!=` | numéricos entre sí, o `string` con `string` | `int` (0 o 1) |
| `-` unario | `int` / `float` | mismo tipo |
| `=` y declaración con valor | `int ← int`, `float ← float`, `float ← int`, `string ← string` | tipo del destino |
| `int ← float`, `string ← número`, `número ← string` | | error de asignación |
| Condición de `if`, `while`, `for` | `int` o `float` | cualquier otro tipo es error |
| Expresión con `void` | llamada a función `void` dentro de una expresión | error |

## Manejo de ámbitos

- La tabla de símbolos es una pila de ámbitos. Se abre uno al entrar a una función (que incluye sus parámetros), a un bloque `{ }` y a un `for` (para su variable de control), y se cierra al salir.
- La búsqueda empieza en el ámbito actual y sube hacia el global, por lo que una variable interna **oculta** (shadowing) a una externa con el mismo nombre sin error.
- Solo se reporta duplicado cuando el nombre ya existe **en el mismo ámbito**.
- Cada función se registra en el ámbito global **antes** de analizar su cuerpo, así que puede llamarse a sí misma (recursión). Una función debe declararse antes de usarse.
- `imprimir(...)` viene predefinida: acepta cualquier cantidad y tipo de argumentos y es `void`.
- Para la tabla final se guarda una lista plana de todos los símbolos en orden de declaración. El ámbito se muestra con su ruta (`main > bloque L33`).

## Verificaciones implementadas

| # | Verificación | Mensaje |
|---|---|---|
| 1 | Identificador no declarado (variable o función) | `Variable 'x' no declarada` / `Función 'f' no declarada` |
| 2 | Declaración duplicada en el mismo ámbito (variable, parámetro, función) | `Variable 'x' ya declarada en este ámbito (Línea N)` |
| 3 | Asignación o inicialización con tipos incompatibles | `Tipos incompatibles: no se puede asignar 'string' a 'x' de tipo 'int'` |
| 4 | Operación con operandos incompatibles | `Operador '-' no aplicable entre 'string' y 'string'` |
| 5 | Cantidad incorrecta de argumentos | `La función 'f' espera 1 argumento(s) pero recibió 2` |
| 6 | `return` con valor en función `void`, o sin valor en función que no es `void` | `La función 'f' debe retornar un valor de tipo 'int'` |

Verificaciones adicionales:

- Tipo de cada argumento contra el parámetro correspondiente.
- Tipo del valor retornado contra el tipo de la función.
- Condiciones de `if`, `while` y `for` que no son numéricas.
- Uso de una función `void` dentro de una expresión.
- `[ADVERTENCIA]` por variables no usadas (con `--advertencias`).

Los errores no detienen el análisis. Una expresión con error toma el tipo `error`, que es compatible con todo, para que un solo fallo no genere una cascada de mensajes.

## Formato de salida

Salida de `tests/ejemplo_enunciado_1.txt`:

```
=== ANÁLISIS SEMÁNTICO ===
[ERROR SEMÁNTICO] La función 'saludar' es de tipo 'void' y no puede retornar un valor en Posición: [Línea 10, Col 5]
[ERROR SEMÁNTICO] Variable 'contador' ya declarada en este ámbito (Línea 14) en Posición: [Línea 16, Col 9]
[ERROR SEMÁNTICO] Variable 'cantidad' no declarada en Posición: [Línea 17, Col 22]
[ERROR SEMÁNTICO] Tipos incompatibles: no se puede asignar 'string' a 'contador' de tipo 'int' en Posición: [Línea 18, Col 5]
...
Errores semánticos: 10
Resultado: 10 error(es) encontrados
```

Salida de `tests/caso_valido.txt` (fragmento):

```
=== ANÁLISIS SEMÁNTICO ===
Análisis semántico completado sin errores.

=== TABLA DE SÍMBOLOS ===
Nombre             | Categoría  | Tipo                   | Ámbito                | Línea
-------------------+------------+------------------------+-----------------------+------
limite             | variable   | int                    | global                | 5
factorial          | funcion    | int(int)               | global                | 9
n                  | parametro  | int                    | factorial             | 9
aplicarTasa        | funcion    | float(float, int)      | global                | 16
i                  | variable   | int                    | aplicarTasa > for L18 | 18
limite             | variable   | int                    | main                  | 29
limite             | variable   | int                    | main > bloque L33     | 34

Errores semánticos: 0
Advertencias: 0
Resultado: COMPILACIÓN EXITOSA
```

## Casos de prueba (Fase 3)

| Archivo | Descripción |
|---|---|
| `tests/caso_valido.txt` | Globales y locales, ocultamiento en dos niveles, funciones con parámetros, recursión, promoción `int → float`, concatenación de `string` e `imprimir`. Compila sin errores. |
| `tests/caso_error.txt` | Sintácticamente correcto, con 11 errores que cubren las 6 verificaciones obligatorias en una sola ejecución. |
| `tests/ejemplo_enunciado_1.txt` / `_2.txt` | Los dos ejemplos del enunciado; la salida coincide con la esperada. |

Los casos válidos de la Fase 2 siguen compilando sin errores semánticos, y los de error léxico y sintáctico omiten el análisis semántico.

## Decisiones de diseño (Fase 3)

- **Visitante sobre el AST de la Fase 2:** `AnalizadorSemantico.visit` despacha por `visit_<nodo.tipo>`, sin modificar la forma del árbol.
- **Posición de los errores:** el nodo `Parametro` guarda la línea y columna del **nombre** del parámetro (no del tipo), para que un duplicado apunte donde corresponde. Es el único cambio en `sintactico.py`.
- **Tipo `error`:** evita errores en cascada y permite seguir analizando el resto del programa.
- **Relacionales como `int`:** el lenguaje no tiene `bool` en operaciones, así que `<`, `==`, etc. producen `int` y las condiciones aceptan `int` o `float`.
- **AST decorado:** cada nodo de expresión recibe el atributo `tipo_calculado`, que `--ast` muestra entre corchetes.
