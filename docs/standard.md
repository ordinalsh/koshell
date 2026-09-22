# La stdlib

La biblioteca estándar de Koshell vive en el paquete `standard/` y se registra
en el runtime con una sola llamada:

```python
from koskript import KoskriptRuntime
from standard import register_standard

runtime = KoskriptRuntime()
register_standard(runtime)
```

`register_standard` registra los trece módulos y crea el objeto `koshell`.

## Convenciones

Todas las funciones siguen las mismas reglas que la stdlib de Koskript:

- **Aridad validada**: pasar más o menos argumentos de los permitidos lanza
  `MismatchType` con el número esperado.
- **Tipos validados**: argumentos del tipo equivocado lanzan `MismatchType`.
- **Errores de dominio**: archivos inexistentes, JSON inválido, algoritmos
  desconocidos, etc. lanzan `RuntimeError`.
- **Errores del sistema operativo**: se envuelven como `RuntimeError` con el
  mensaje del sistema, sin cerrar la shell.
- **Mutación in-place**: las funciones que modifican un archivo, una colección
  o el entorno lo hacen en el sitio y devuelven algo útil (la ruta, el valor o
  la propia colección).
- **Valores nativos**: los `array` y `map` que devuelven las funciones son
  listas y diccionarios de Python, así que funcionan con toda la stdlib de
  Koskript (`array.push`, `map.keys`, `len`, ...).

## Firma y documentación en vivo

Cada módulo es una clase con funciones; en Koshell se accede como
`modulo.funcion(...)`. La propia shell puede generar la referencia:

```koskript
koshell.modules()          // ["archive", "clock", "codec", ...]
koshell.help()             // resumen de módulos
koshell.help("network")    // firmas de todas las funciones de network
koshell.about()            // nombre, versión, módulos, versión de Python
```

## Estructura

| Módulo | Clase Python | Archivo |
| --- | --- | --- |
| `filesystem` | `Filesystem` | `standard/filesystem.py` |
| `process` | `Process` | `standard/processes.py` |
| `tasks` | `Tasks` | `standard/tasks.py` |
| `env` | `Environment` | `standard/environment.py` |
| `system` | `System` | `standard/system.py` |
| `clock` | `Clock` | `standard/clock.py` |
| `network` | `Network` | `standard/network.py` |
| `archive` | `Archive` | `standard/archive.py` |
| `codec` | `Codec` | `standard/codec.py` |
| `data` | `Data` | `standard/data.py` |
| `output` | `Output` | `standard/output.py` |
| `input` | `Input` | `standard/input.py` |
| `logger` | `Logger` | `standard/logger.py` |
| `koshell` | `Koshell` | `standard/koshell.py` |

## Añadir tus propios módulos

`register_standard` acepta un mapa extra de módulos. Cada valor puede ser una
clase (sus métodos públicos se exponen como funciones del módulo) o una función
suelta:

```python
from standard import register_standard


class Git:
    def status(path="."):
        return process.run(f"git -C {path} status --short")

    def log(path=".", count=10):
        return process.run(f"git -C {path} log --oneline -n {count}")


register_standard(runtime, extra={"git": Git})
```

Desde Koshell:

```koskript
git.status(".")
output.table(git.log(".", 5))
```

## El puente de callbacks

`standard/bridge.py` conecta las funciones Python con las lambdas y funciones
de Koskript. Hoy lo usa `filesystem.walk` para invocar su callback:

```koskript
filesystem.walk(".", (entry) {
    if (entry.file and filesystem.extension(entry.name) == "md") {
        print(entry.path)
    }
})
```

## Ejecución segura desde hilos

`tasks` ejecuta callbacks en un hilo de fondo. Como el runtime de Koskript no es
thread-safe, `standard/bridge.py` mantiene un candado reentrante compartido:

```python
from standard import execution_lock

with execution_lock():
    runtime.execute(comando)
```

`main.py` ya envuelve cada comando con ese candado, y `bridge.call` /
`bridge.execute` lo adquieren antes de tocar el runtime, así que una tarea
nunca se ejecuta a la vez que un comando tuyo.

## print

En Koshell el nombre global `print` está sobreescrito con `rich` para que la
salida se formatee (markup, colores, tablas). Puedes seguir usando
`output.info`, `output.warn`, etc. para salidas etiquetadas.
