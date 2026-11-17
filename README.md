# Proyecto Final: Compiladores

## Fase 1: Análisis Léxico

Analizador léxico (scanner) en Python que lee un archivo de texto con código fuente, reconoce los tokens del lenguaje asignado y reporta los errores léxicos con su línea y columna. Es una implementación propia basada en expresiones regulares del módulo nativo `re`, sin generadores automáticos ni librerías de terceros.

**Integrantes:**
- Violeta Sofia Martinez Puente
- Dalila Astrid Murcia Medina
- Marelin Valeriana Romualdo Leonor

Universidad de Sonsonate, Ingeniería en Sistemas Computacionales. Curso: Compiladores.

---

## Estructura del repositorio

```
.
├── main.py          # Punto de entrada
├── lexer.py         # Lógica del analizador léxico
├── tests/
│   ├── caso_valido.txt
│   └── caso_error.txt
├── .gitignore
└── README.md
```

## Requisitos

- Python 3.8 o superior
- Sin dependencias externas

## Ejecución

```bash
python main.py <ruta_del_archivo>
```

```bash
python main.py tests/caso_valido.txt
python main.py tests/caso_error.txt
```

El programa termina con código 0 si no hay errores léxicos y con código 1 si hay alguno o si el archivo no se puede leer.

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

## Elementos ignorados

- Espacios, tabulaciones y saltos de línea.
- Comentarios de una línea (`// ...`) y multilínea (`/* ... */`).

Se consumen sin generar token, pero se cuentan sus saltos de línea para que la posición de los tokens siguientes sea correcta.

## Manejo de errores léxicos

El analizador no se detiene ante un error: lo registra y sigue con el resto del archivo. Detecta cuatro tipos:

| Error | Ejemplo | Qué consume |
|---|---|---|
| Carácter no reconocido | `$`, `@`, `#` | El carácter |
| Cadena sin cerrar | `"hola` | Hasta el final de la línea |
| Número mal formado | `123abc` | El número junto con las letras que lo siguen |
| Comentario multilínea sin cerrar | `/* ...` | Hasta el final del archivo |

## Formato de salida

Token:

```
[TOKEN] Tipo: <TIPO> | Lexema: '<lexema>' | Posición: [Línea L, Col C]
```

Error:

```
[ERROR LÉXICO] <descripción> '<texto>' en Posición: [Línea L, Col C]
```

Al final se imprime un resumen con la cantidad de tokens válidos y de errores.

Ejemplo (`tests/caso_error.txt`):

```
[TOKEN] Tipo: PR_INT          | Lexema: 'int'         | Posición: [Línea 1, Col 1]
[TOKEN] Tipo: ID              | Lexema: 'limite'      | Posición: [Línea 1, Col 5]
[TOKEN] Tipo: OP_ASSIGN       | Lexema: '='           | Posición: [Línea 1, Col 12]
[ERROR LÉXICO] Carácter no reconocido '$' en Posición: [Línea 1, Col 14]
[TOKEN] Tipo: INT_LITERAL     | Lexema: '100'         | Posición: [Línea 1, Col 16]
[TOKEN] Tipo: DELIM_SEMICOLON | Lexema: ';'           | Posición: [Línea 1, Col 19]
```

## Casos de prueba

| Archivo | Descripción |
|---|---|
| `tests/caso_valido.txt` | Programa con declaraciones, funciones, `if`/`else`, `for`, `while`, comentarios de ambos tipos y los tres literales. No produce errores léxicos. |
| `tests/caso_error.txt` | Seis errores léxicos intencionales: `$` (línea 1), cadena sin cerrar (línea 3), `123abc` (línea 4), `@` (línea 7), `#` (línea 8) y comentario multilínea sin cerrar (línea 10). Se reportan todos en una sola ejecución. |

## Decisiones de diseño

- **Técnica:** una sola expresión regular compilada, formada por grupos con nombre (`(?P<TIPO>...)`) unidos con `|`. Se recorre el código con `finditer` y el primer patrón que coincide gana, por lo que el orden de `TOKEN_SPECIFICATION` importa: los operadores de dos caracteres (`==`, `<=`) van antes que `=` y `<`, y los patrones de error van junto a los literales que podrían confundirse.
- **Palabras reservadas:** se reconocen con `\b` y luego se mapean a su tipo mediante el diccionario `KEYWORD_MAP`. Así `int` es `PR_INT`, pero `integer` es `ID`.
- **Posición:** la línea y la columna empiezan en 1. La columna se calcula como la posición del lexema menos el inicio de la línea actual. Al encontrar un salto de línea, o un comentario multilínea que contenga alguno, se actualizan ambos valores.
- **Estructuras de datos:** `Token(type, value, line, column)` y `LexicalError(message, char, line, column)`, ambas `NamedTuple`. `tokenize()` devuelve las dos listas por separado.
- **Errores:** los casos mal formados (cadena sin cerrar, número pegado a letras, comentario sin cerrar) tienen su propio patrón, lo que permite dar un mensaje específico en lugar de uno genérico. Cualquier otro carácter cae en el comodín `MISMATCH`.
- **Salida:** `main.py` junta tokens y errores y los ordena por línea y columna, para que el error aparezca en el lugar del código donde ocurrió.
