# env

Variables de entorno del proceso de Koshell. Los cambios afectan también a los
subprocesos que lances con [`process.run`](process.md) y
[`process.spawn`](process.md).

```koskript
print(env.get("USERNAME", env.get("USER", "invitado")))
env.set("KOSHELL_MODE", "dev")
```

## Funciones

| Función | Descripción | Devuelve |
| --- | --- | --- |
| `env.get(name, default=null)` | Valor de la variable, o `default` si no existe. | `string` |
| `env.set(name, value)` | Crea o actualiza la variable. | `string` |
| `env.unset(name)` | Elimina la variable. | `bool` |
| `env.has(name)` | ¿Existe la variable? | `bool` |
| `env.all()` | Copia de todas las variables. | `map` |
| `env.expand(text)` | Expande `$VAR` y `%VAR%` dentro de un texto. | `string` |
| `env.path()` | Entradas del `PATH` como array. | `array` |
| `env.add_path(directory)` | Añade un directorio al final del `PATH` si no está. | `string` |
| `env.remove_path(directory)` | Quita un directorio del `PATH`. | `string` |

`unset` devuelve `true` si la variable existía; `add_path` y `remove_path`
devuelven el directorio para poder encadenar.

## Ejemplos

```koskript
// Leer con valor por defecto
local editor = env.get("EDITOR", "notepad")

// Leer y escribir variables
env.set("KOSHELL_PROJECT", filesystem.current_dir())
print(env.expand("Proyecto: $KOSHELL_PROJECT"))

// Recorrer el entorno
foreach (name, value in env.all()) {
    if (string.starts_with(name, "KOSHELL_")) {
        print(name, "=", value)
    }
}

// Manipular el PATH
local herramientas = filesystem.pathjoin(filesystem.current_dir(), "tools")
env.add_path(herramientas)
print(process.which("mytool"))
```

## Notas

- En Windows los nombres de variables no distinguen mayúsculas.
- `env.set` solo acepta strings; convierte números con `str(value)` si hace
  falta.
- `env.expand` usa las reglas del sistema: en Windows `%VAR%`, en el resto
  `$VAR` (y `${VAR}`).
