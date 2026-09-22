# Primeros pasos

## Requisitos

- Python 3.10 o superior (probado con 3.14).
- Las dependencias de `requirements.txt`: `koskript`, `rich`, `psutil` y
  `requests`.

## Instalación

```bash
pip install -r requirements.txt
```

## Ejecutar la shell

```bash
python main.py
```

Verás el prompt con tu usuario, el host y el directorio actual:

```
Aleix@DESKTOP-AEO3Q06 D:\Python\Koshell $
```

## Tus primeros comandos

Koshell no usa comandos al estilo POSIX: cada línea es código Koskript.

```koskript
print("hola mundo")
local x = 10
print(x * 2)
```

Las funciones de la stdlib se llaman con la misma sintaxis:

```koskript
filesystem.listdir(".")
filesystem.read("requirements.txt")
system.memory().used_human
process.which("python")
```

Cuando el resultado de una línea no es `null`, la shell lo imprime:

```koskript
1 + 2                 // imprime 3
len(filesystem.drives())
```

## Variables y funciones

```koskript
local root = filesystem.current_dir()
const LIMITE = 3

fn grandes(dir) {
    local result = []
    for (entry in filesystem.entries(dir)) {
        if (entry.size > LIMITE) {
            array.push(result, entry.name)
        }
    }
    return result
}

print(grandes(root))
```

## Guardar y cargar scripts

Guarda un archivo `saludo.kos` y ejecútalo con `koshell.source`:

```koskript
// saludo.kos
print("hola " + env.get("USERNAME", "invitado"))
```

```koskript
koshell.source("saludo.kos")
```

También puedes ejecutar código en línea o desde una URL:

```koskript
koshell.eval("1 + 1")
koshell.loadfrom("https://ejemplo.com/script.kos")
```

## Descubrir la stdlib

```koskript
koshell.modules()
koshell.help()
koshell.help("filesystem")
koshell.about()
```

`koshell.help` genera la lista de funciones con sus firmas reales.

## Tareas en segundo plano

El módulo [`tasks`](tasks.md) ejecuta código cada cierto tiempo sin bloquear el
prompt:

```koskript
local reloj = tasks.every(5, () { print(clock.time()) }, "reloj")
local backup = tasks.every_hours(2, "archive.zip_create('backup.zip', 'standard')")

tasks.list()
tasks.trigger(reloj)     // ejecutar ahora
tasks.pause(reloj)       // pausar
tasks.cancel(backup)     // cancelar
tasks.clear()            // cancelar todas
```

## Errores

Los errores no cierran la shell: se imprimen y vuelves al prompt.

```koskript
codec.hash("x", "nope")
// RuntimeError: codec() unknown hash algorithm 'nope'

filesystem.read("no-existe.txt")
// RuntimeError: filesystem.read() failed: No such file or directory: no-existe.txt

len()
// MismatchType: len() expected 1 argument(s), got 0
```

## Salir

```koskript
koshell.exit()
```

`Ctrl+C` o `Ctrl+D` en el prompt también cierran la shell.
