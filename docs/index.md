# Koshell

Koshell es una shell interactiva escrita en Python cuyo lenguaje de comandos es
[Koskript](https://koskript.alesis.buzz/), un lenguaje de scripting embebible,
dinámico y con interop nativo con Python.

Cada línea que escribes en el prompt se parsea y se ejecuta en un
`KoskriptRuntime` que tiene registrada la biblioteca estándar de Koshell: trece
módulos con más de 180 funciones para manejar archivos, procesos, red,
compresión, datos, entorno, tareas programadas y más.

```
Aleix@DESKTOP D:\Python\Koshell $ print("hola " + system.user())
hola Aleix
Aleix@DESKTOP D:\Python\Koshell $ local r = process.run("git status")
Aleix@DESKTOP D:\Python\Koshell $ output.table([{ "code": r.code, "ok": r.ok }])
```

## Qué incluye

- **REPL con prompt en vivo**: usuario, host y directorio actual, con `rich`.
- **Lenguaje completo**: variables, funciones, closures, clases, herencia y
  control de flujo (ver [Koskript en Koshell](koskript.md)).
- **Stdlib amplia**: `filesystem`, `process`, `tasks`, `env`, `system`,
  `clock`, `network`, `archive`, `codec`, `data`, `output`, `input`, `logger`.
- **Tareas en segundo plano**: `tasks.every(5, ...)` ejecuta código cada
  segundos, minutos u horas sin bloquear el prompt.
- **Control de la shell**: `koshell.execute`, `koshell.source`,
  `koshell.loadfrom`, `koshell.help`, `koshell.exit`.
- **Errores controlados**: un script que falla imprime el error y la shell
  sigue funcionando.
- **Autodocumentación**: `koshell.help()` lista los módulos y
  `koshell.help("network")` las firmas de un módulo.

## Arquitectura

```
main.py                 bucle REPL: lee, ejecuta, imprime
standard/
  __init__.py           register_standard(runtime): registra los 12 módulos
  arity.py              valida la aridad y lanza Errors.MismatchType
  bridge.py             puente para invocar callbacks escritos en Koskript
  helpers.py            validación de tipos, errores y utilidades internas
  filesystem.py         módulo filesystem
  processes.py          módulo process
  tasks.py              módulo tasks (planificador en segundo plano)
  environment.py        módulo env
  system.py             módulo system
  clock.py              módulo clock
  network.py            módulo network
  archive.py            módulo archive
  codec.py              módulo codec
  data.py               módulo data
  output.py             módulo output
  input.py              módulo input
  logger.py             módulo logger
  koshell.py            módulo koshell
docs/                   este sitio DocMD
```

El flujo de una línea es:

1. `console.input` muestra el prompt y lee el comando.
2. `runtime.execute(comando)` lo parsea y ejecuta.
3. Si el resultado no es `null`, se imprime con `rich`.
4. Si algo falla, se imprime el tipo de error y el mensaje, y se vuelve al
   prompt.

## Módulos

| Módulo | Qué cubre | Funciones |
| --- | --- | --- |
| [`filesystem`](filesystem.md) | Archivos, directorios, rutas, disco | 45 |
| [`process`](process.md) | Procesos, subprocess, CPU/memoria | 18 |
| [`tasks`](tasks.md) | Tareas programadas en segundo plano | 10 |
| [`env`](env.md) | Variables de entorno y `PATH` | 9 |
| [`system`](system.md) | Plataforma, hardware, usuario | 19 |
| [`clock`](clock.md) | Fechas, horas, timestamps, `sleep` | 12 |
| [`network`](network.md) | HTTP, DNS, puertos | 15 |
| [`archive`](archive.md) | ZIP y TAR | 11 |
| [`codec`](codec.md) | Hashing, Base64, Hex, UUID, tokens | 16 |
| [`data`](data.md) | JSON, CSV y líneas | 6 |
| [`output`](output.md) | Salida formateada con `rich` | 12 |
| [`input`](input.md) | Entrada interactiva | 5 |
| [`logger`](logger.md) | Logs con marca de tiempo | 7 |
| [`koshell`](koshell.md) | Control de la propia shell | 9 |

## Empezar

Sigue [Primeros pasos](getting-started.md) para instalar y ejecutar Koshell, y
[La stdlib](standard.md) para conocer las convenciones comunes a todos los
módulos.
