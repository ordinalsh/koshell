# process

Procesos del sistema y ejecución de comandos. Usa `psutil` para la
introspección y `subprocess` para lanzar programas.

```koskript
output.table(process.top(5), ["pid", "name", "memory_human"])
```

## Listado y consultas

| Función | Descripción | Devuelve |
| --- | --- | --- |
| `process.get_tasks()` | Todos los procesos en ejecución. | `array` |
| `process.find(name)` | Procesos cuyo nombre contiene `name` (sin distinguir mayúsculas). | `array` |
| `process.info(pid)` | Detalle de un proceso. `null` si no existe. | `map` |
| `process.exists(pid)` | ¿Existe ese PID? | `bool` |
| `process.pid()` | PID del propio Koshell. | `int` |
| `process.parent(pid)` | Proceso padre. `null` si no tiene. | `map` |
| `process.children(pid)` | Procesos hijos. | `array` |
| `process.cmdline(pid)` | Línea de comandos. | `array` |
| `process.cwd(pid)` | Directorio de trabajo. `null` si no se puede leer. | `string` |
| `process.top(limit=10, by="memory")` | Procesos ordenados por consumo. | `array` |

Cada tarea es un map con:

| Campo | Tipo | Descripción |
| --- | --- | --- |
| `pid` | `int` | Identificador del proceso. |
| `name` | `string` | Nombre del ejecutable. |
| `status` | `string` | `running`, `sleeping`, `zombie`, ... |
| `memory` | `int` | Memoria residente en bytes. |
| `memory_human` | `string` | Memoria legible (`"120.50 MB"`). |
| `threads` | `int` | Número de hilos. |
| `created` | `float` | Timestamp de creación. |
| `user` | `string` | Usuario propietario, o `null`. |

`process.top` acepta `"memory"` o `"cpu"`; con `"cpu"` añade el campo `cpu` a
cada tarea (porcentaje desde la llamada anterior).

## Control

| Función | Descripción | Devuelve |
| --- | --- | --- |
| `process.terminate_task(pid)` | Pide al proceso que termine (SIGTERM). | `bool` |
| `process.kill_task(pid)` | Fuerza la terminación (SIGKILL). | `bool` |
| `process.suspend(pid)` | Pausa el proceso. | `bool` |
| `process.resume(pid)` | Reanuda el proceso. | `bool` |
| `process.wait(pid, timeout=null)` | Espera a que termine. | `bool` |

Devuelven `false` si el proceso no existe o si se agotó el `timeout`; lanzan
`RuntimeError` si el sistema niega el acceso.

```koskript
local pid = process.spawn("notepad")
clock.sleep(1)
process.suspend(pid)
clock.sleep(0.5)
process.resume(pid)
process.kill_task(pid)
```

## Ejecución

| Función | Descripción | Devuelve |
| --- | --- | --- |
| `process.run(command, cwd=null, timeout=null, shell=true)` | Ejecuta y espera, capturando la salida. | `map` |
| `process.spawn(command, cwd=null)` | Lanza un proceso en segundo plano. | `int` |
| `process.which(command)` | Ruta del ejecutable en el `PATH`. `null` si no está. | `string` |

`process.run` devuelve:

| Campo | Tipo | Descripción |
| --- | --- | --- |
| `code` | `int` | Código de salida. |
| `ok` | `bool` | `true` si `code == 0`. |
| `stdout` | `string` | Salida estándar. |
| `stderr` | `string` | Salida de error. |
| `duration` | `float` | Segundos que tardó. |

- Si `command` es un `string`, se ejecuta a través del shell del sistema.
- Si `command` es un `array`, se ejecuta directamente sin shell (más seguro).

```koskript
local r = process.run("git status --short")
if (r.ok) {
    print(r.stdout)
} else {
    output.error(r.stderr)
}

local listado = process.run(["python", "--version"])
print(listado.stdout)

// con timeout: lanza RuntimeError si se pasa
process.run("ping -n 5 127.0.0.1", null, 2)
```

`process.spawn` lanza el proceso desacoplado (en Windows con
`DETACHED_PROCESS`) y devuelve su PID.

## Notas

- Los nombres de proceso en `find` no distinguen mayúsculas.
- `get_tasks` omite procesos a los que el sistema no permite acceder.
- `terminate_task` y `kill_task` devuelven `false` si el PID ya no existe; solo
  lanzan error si el sistema deniega el permiso.
