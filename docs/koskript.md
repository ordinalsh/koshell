# Koskript en Koshell

Todo lo que escribes en Koshell es [Koskript](https://koskript.alesis.buzz/).
Esta página resume el lenguaje; la referencia completa está en la
[documentación de Koskript](https://koskript.alesis.buzz/).

## Tipos

| Tipo | Ejemplo |
| --- | --- |
| `int` | `42` |
| `float` | `3.14` |
| `string` | `"hola"` o `'hola'` |
| `bool` | `true`, `false` |
| `null` | `null` |
| `array` | `[1, 2, 3]` |
| `map` | `{ "clave": "valor" }` |
| `function` | `fn f() { }`, `(x) { return x }` |
| `class` / `instance` | `class A { }`, `new A()` |

`type(valor)` devuelve el nombre del tipo.

## Variables

```koskript
local x = 10
const PI = 3.14
local config = { "debug": true }
local items = [1, 2, 3]
```

- `local` declara en el bloque actual (incluidos `if`, `while`, `for`,
  `foreach`).
- `const` es una ligadura de solo lectura; el contenido de arrays y maps sí se
  puede modificar.
- Asignar a un nombre (`x = 1`) actualiza la declaración más cercana; si no
  existe, es un `NameError`.
- Las funciones y lambdas capturan el ámbito donde se **definen**.

## Funciones y lambdas

```koskript
fn add(a, b) {
    return a + b
}

local doble = (x) { return x * 2 }
print(add(1, 2), doble(4))
```

Los argumentos de más se ignoran y los que faltan valen `null`. `return` sin
valor devuelve `null`.

## Operadores

`+` `-` `*` `/` `%`, menos unario `-x`, comparaciones `==` `!=` `>` `<` `>=`
`<=`, lógicos `and` `or` `not` (con cortocircuito) y agrupación con `( )`.
`+` también concatena strings.

## Control de flujo

```koskript
if (x > 10) {
    print("grande")
} elseif (x == 10) {
    print("exacto")
} else {
    print("pequeño")
}

while (x > 0) {
    x = x - 1
}

for (item in items) {
    print(item)
}

foreach (clave, valor in config) {
    print(clave, valor)
}

for (n in range(1, 10)) {
    if (n == 3) { continue }
    if (n == 8) { break }
}
```

`for` acepta arrays y cualquier iterable de Python (por ejemplo `range`).
`foreach` acepta maps y objetos con `items()`.

## Acceso a miembros e índices

```koskript
local user = { "name": "Aleix", "age": 17 }
print(user.name)          // Aleix
user.age = 18             // asignación de miembro
print(user["age"])        // 18

local items = [10, 20, 30]
print(items[0], items[-1])
```

La lectura por índice funciona en arrays, maps, strings y objetos Python con
`__getitem__`. La **escritura** por índice (`items[0] = 9`) todavía no está
soportada; usa las funciones de `array` de la stdlib de Koskript
(`array.push`, `array.insert`, `array.remove_at`, ...).

## Strings

Comillas simples o dobles y escapes `\n`, `\t`, `\r`, `\0`, `\\`, `\"`, `\'`.
No hay interpolación: concatena con `+` o usa `array.join` / `json.encode`.

## Verdad (truthiness)

Son falsos: `false`, `null`, `0`, `0.0`, `""`, `[]` y `{}`. Todo lo demás es
verdadero. `bool(valor)` aplica las mismas reglas.

## Comentarios

```koskript
// comentario de línea
```

No hay comentarios de bloque.

## Clases

```koskript
class Animal {
    public name = "genérico"
    private energy = 100

    constructor(name) {
        this.name = name
    }

    public fn speak() {
        return "..."
    }

    static fn kingdom() {
        return "animalia"
    }
}

class Dog extends Animal {
    constructor(name) {
        super::constructor(name)
    }

    public fn speak() {
        return "woof"
    }
}

const rex = new Dog("Rex")
print(rex.speak(), Dog.kingdom())
```

Las lambdas definidas dentro de un método capturan `this`.

## Palabras reservadas

No se pueden usar como identificadores:

`if` `elseif` `else` `while` `for` `foreach` `fn` `return` `local` `const`
`true` `false` `null` `and` `or` `not` `in` `break` `continue` `class`
`extends` `new` `static` `public` `private` `this` `super` `constructor`

## Interop con Python (y callbacks)

La stdlib de Koshell es Python, así que puedes pasarle lambdas o funciones como
callbacks:

```koskript
filesystem.walk(".", (entry) {
    if (entry.file) {
        print(entry.path)
    }
})
```

También puedes llamar métodos de objetos Python y usar sus atributos; los
atributos dunder (`__x__`) están bloqueados.

## Gotchas

Los saltos de línea son espacios en blanco, así que una línea que empieza por
`(` después de otra que termina en `)` se interpreta como una llamada
encadenada:

```koskript
local r = math.random()
local ok = (r >= 0) and (r < 1)   // bien

// Evita:
// local r = math.random()
// (r >= 0) and (r < 1)           // se parsea como math.random()(r >= 0)
```

## Errores

Koskript lanza errores bajo `koskript.Errors`:

| Error | Cuándo |
| --- | --- |
| `SyntaxError` | El script no se puede parsear (incluye línea y columna). |
| `NameError` | Un nombre no está definido. |
| `MismatchType` | Tipo incorrecto o aridad incorrecta. |
| `ProtectedObject` | Se intenta reasignar un `const`. |
| `RuntimeError` | Cualquier otro fallo de ejecución. |

En Koshell se imprimen y la shell continúa. Todavía no existe `try` / `catch`
en el lenguaje.
