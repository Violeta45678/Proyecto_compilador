# Gramática del lenguaje (Fase 2)

## 1. Gramática en EBNF
Las palabras en `MAYÚSCULAS` son tokens del lexer; los terminales entre comillas se comparan por su lexema.
`{ x }` = cero o más veces, `[ x ]` = opcional.

```
programa        = { elemento } EOF ;
elemento        = funcion | sentencia ;

funcion         = tipo ID "(" [ parametros ] ")" bloque ;
parametros      = tipo ID { "," tipo ID } ;
tipo            = "int" | "float" | "char" | "string" | "bool" | "void" ;

sentencia       = declaracion | sentencia_if | sentencia_while | sentencia_for
                | sentencia_return | bloque | ";" | expresion ";" ;
bloque          = "{" { sentencia } "}" ;
declaracion     = tipo declarador { "," declarador } ";" ;
declarador      = ID [ "=" expresion ] ;
sentencia_if    = "if" "(" expresion ")" sentencia [ "else" sentencia ] ;
sentencia_while = "while" "(" expresion ")" sentencia ;
sentencia_for   = "for" "(" [ declaracion_sin_pc | expresion ] ";" [ expresion ] ";"
                  [ expresion ] ")" sentencia ;
sentencia_return= "return" [ expresion ] ";" ;

expresion       = asignacion ;
asignacion      = igualdad [ "=" asignacion ] ;
igualdad        = relacional { ( "==" | "!=" ) relacional } ;
relacional      = aditivo { ( "<" | ">" | "<=" | ">=" ) aditivo } ;
aditivo         = multiplicativo { ( "+" | "-" ) multiplicativo } ;
multiplicativo  = unario { ( "*" | "/" ) unario } ;
unario          = "-" unario | primario ;
primario        = INT_LITERAL | FLOAT_LITERAL | STRING_LITERAL | "true" | "false"
                | ID [ "(" [ argumentos ] ")" ] | "(" expresion ")" ;
argumentos      = expresion { "," expresion } ;
```

`declaracion_sin_pc` es `declaracion` sin el `;` final, que en el `for` consume la propia regla.

## 2. Precedencia y asociatividad

| Nivel | Operadores | Asociatividad | Regla |
|---|---|---|---|
| 1 (menor) | `=` | derecha | `asignacion` |
| 2 | `==` `!=` | izquierda | `igualdad` |
| 3 | `<` `>` `<=` `>=` | izquierda | `relacional` |
| 4 | `+` `-` | izquierda | `aditivo` |
| 5 | `*` `/` | izquierda | `multiplicativo` |
| 6 (mayor) | `-` unario, paréntesis | derecha (`- -x`) | `unario`, `primario` |

La asociatividad por la izquierda se implementa con un ciclo `{ ... }`; la de `=` con recursión sobre la propia regla.

## 3. Ausencia de recursión por la izquierda y de ambigüedad
- Ninguna regla comienza llamándose a sí misma: las repeticiones usan `{ }`.
- Función o declaración: ambas empiezan con `tipo ID`. Se distinguen con 2 tokens de anticipación: si el tercero es `(` es una función.
- Llamada o identificador: se distingue con 1 token de anticipación (`ID` seguido de `(`).
- `else` ambiguo (dangling else): el `else` se une al `if` más cercano, porque el parser lo consume en cuanto aparece tras la sentencia del `if`.

## 4. Recuperación de errores (modo pánico)
Cuando una regla no encuentra el token esperado, lanza `ParseError`. La excepción se captura en el ciclo del `programa` o del `bloque`, que registra el error y llama a `sincronizar()`, la cual descarta tokens hasta uno de estos puntos:

| Punto de sincronización | Acción |
|---|---|
| `;` | Se consume y el análisis sigue con la sentencia siguiente |
| `}` | No se consume: lo usa el bloque que lo contiene |
| Inicio de sentencia (`int`, `float`, `char`, `string`, `bool`, `void`, `if`, `else`, `while`, `for`, `return`, `{`) | No se consume: empieza una sentencia nueva |

- Si el error ocurre sin avanzar ningún token, se descarta uno antes de sincronizar, para no repetir el mismo error indefinidamente.
- Un `else` sin `if` se reporta como error y se descarta solo ese token; el análisis continúa.
- El AST solo se imprime si no hubo errores sintácticos.
