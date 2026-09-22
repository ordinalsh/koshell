# input

Entrada interactiva con los prompts de `rich`. Pensado para scripts que se
ejecutan en la terminal de Koshell.

```koskript
local nombre = input.ask("¿Cómo te llamas?")
output.success("Hola " + nombre)
```

## Funciones

| Función | Descripción | Devuelve |
| --- | --- | --- |
| `input.ask(prompt, default=null)` | Pregunta y devuelve texto. | `string` |
| `input.confirm(prompt, default=false)` | Pregunta sí/no. | `bool` |
| `input.password(prompt)` | Pregunta sin mostrar lo tecleado. | `string` |
| `input.number(prompt, default=null)` | Pregunta y devuelve un entero. | `int` |
| `input.choose(prompt, options)` | Muestra opciones y devuelve la elegida. | valor |

## Ejemplos

```koskript
local nombre = input.ask("Nombre del proyecto", "demo")
local version = input.ask("Versión", "0.1.0")

local carpetas = input.confirm("¿Crear la estructura de carpetas?", true)
if (carpetas) {
    filesystem.makedirs(filesystem.pathjoin(nombre, "src"))
    filesystem.makedirs(filesystem.pathjoin(nombre, "tests"))
    output.success("Proyecto " + nombre + " " + version + " creado")
}

local entorno = input.choose("Entorno de despliegue", ["dev", "staging", "prod"])
local puerto = input.number("Puerto", 8080)
print(entorno, puerto)

local clave = input.password("Token de API")
```

## Notas

- Si el usuario cancela con `Ctrl+C` o `Ctrl+D`, la función lanza
  `RuntimeError` con el mensaje `input.*() was cancelled`; la shell sigue
  funcionando.
- `input.ask` con `default` acepta `Enter` para usar ese valor.
- `input.number` solo acepta enteros; `rich` vuelve a preguntar si el valor no
  es válido.
- `input.choose` resalta las opciones y devuelve el valor original del array
  (no el índice).
