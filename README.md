# Proyecto Final: Compiladores

Analizador léxico (Fase 1) y sintáctico (Fase 2) en Python, implementados a mano, sin generadores automáticos ni librerías de terceros.

**Integrantes:**
- <Nombre 1>
- <Nombre 2>
- <Nombre 3>

Universidad de Sonsonate, Ingeniería en Sistemas Computacionales. Curso: Compiladores.

## Estructura del repositorio

```
.
├── main.py          # Punto de entrada (Fase 1 + Fase 2)
├── lexer.py         # Analizador léxico (Fase 1)
├── sintactico.py    # Analizador sintáctico y AST (Fase 2)
├── GRAMATICA.md     # Gramática EBNF, precedencia y recuperación de errores
├── tests/
│   ├── caso_valido.txt
│   ├── caso_valido_expresiones.txt
│   ├── caso_valido_control.txt
│   ├── caso_valido_funciones.txt
│   ├── caso_error.txt           # errores sintácticos (Fase 2)
│   └── caso_error_lexico.txt    # errores léxicos (Fase 1)
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
python main.py tests/caso_valido.txt --tokens
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
python main.py tests/caso_valido.txt
python main.py tests/caso_error.txt
```

Primero se ejecuta el análisis léxico y se imprimen sus errores, y luego el sintáctico. Si no hay errores sintácticos se imprime el AST con sangría. El programa devuelve código 0 si la compilación es exitosa y 1 en caso contrario.

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

Salida de `tests/caso_error.txt`:

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
| `tests/caso_valido.txt` | Programa completo con todas las construcciones: declaraciones, funciones, `if-else`, `for`, `while`, llamadas y `return`. |
| `tests/caso_valido_expresiones.txt` | Precedencia, asociatividad y paréntesis. |
| `tests/caso_valido_control.txt` | Estructuras de control anidadas, `for(;;)`, bloques y sentencia vacía. |
| `tests/caso_valido_funciones.txt` | Funciones, parámetros, llamadas anidadas y recursión. |
| `tests/caso_error.txt` | Ocho errores sintácticos de seis tipos distintos (`;` faltante, `)` faltante, expresión incompleta, `else` sin `if`, parámetro sin tipo, asignación a algo que no es variable, `}` sin cerrar), todos reportados en una sola ejecución. |
| `tests/caso_error_lexico.txt` | Seis errores léxicos (Fase 1). |

## Decisiones de diseño (Fase 2)

- **Una función por regla:** cada regla de la gramática es un método de `Parser` (`sentencia_if`, `aditivo`, `primario`, etc.), con la regla escrita como comentario encima.
- **Precedencia en la gramática:** una regla por nivel, de menor a mayor precedencia. La asociatividad por la izquierda se resuelve con un ciclo y la de `=` con recursión sobre `asignacion`.
- **Lookahead:** función y declaración empiezan igual (`tipo ID`), así que `elemento` mira dos tokens más adelante: si el tercero es `(`, es una función. Llamada e identificador se distinguen con un token (`ID` seguido de `(`).
- **`else` ambiguo:** se une al `if` más cercano porque el parser consume el `else` en cuanto aparece tras la sentencia del `if`. Un `else` suelto se reporta como error y se descarta solo ese token.
- **Asignación válida:** `asignacion` parsea el lado izquierdo como expresión y después verifica que sea un identificador; si no, reporta error. Así `a + 1 = 5;` se detecta sin complicar la gramática.
- **Recuperación en modo pánico:** al fallar una regla se lanza `ParseError`, que se captura en el ciclo del programa o del bloque. `sincronizar()` descarta tokens hasta un `;` (se consume), un `}` o el inicio de una sentencia (no se consumen). Si el error ocurre sin avanzar ningún token, se descarta uno para evitar un ciclo infinito.
- **AST para la Fase 3:** cada `ASTNode` guarda tipo, valor, hijos, línea y columna de su token de origen. Solo se imprime si no hubo errores sintácticos.
