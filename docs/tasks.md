# tasks

Planificador de tareas en segundo plano. Permite ejecutar código cada ciertos
segundos, minutos u horas, o una sola vez tras un retardo, sin bloquear el
prompt.

```koskript
tasks.every(5, () { print("latido", clock.time()) })
tasks.every_hours(2, "backup()", "backup")
```

## Programar

| Función | Descripción | Devuelve |
| --- | --- | --- |
| `tasks.every(seconds, callback, name=null)` | Ejecuta el callback cada `seconds` segundos. | `int` |
| `tasks.every_minutes(minutes, callback, name=null)` | Igual, en minutos. | `int` |
| `tasks.every_hours(hours, callback, name=null)` | Igual, en horas. | `int` |
| `tasks.after(seconds, callback, name=null)` | Ejecuta una sola vez tras `seconds` segundos. | `int` |

Todas devuelven el **id** de la tarea, que usarás para pausarla, dispararla o
cancelarla. `name` es opcional; por defecto es `"task-<id>"`.

El `callback` puede ser:

- una lambda o función de Koskript: `() { print("hola") }`
- el nombre de una función declarada: `mi_funcion`
- un método de un objeto Python: `session::ping()`
- código Koskript como string: `"print(clock.iso())"`

Los callbacks **no reciben argumentos**.

## Gestionar

| Función | Descripción | Devuelve |
| --- | --- | --- |
| `tasks.list()` | Tareas activas, ordenadas por id. | `array` |
| `tasks.cancel(id)` | Elimina la tarea. | `bool` |
| `tasks.pause(id)` | Deja de ejecutarla hasta `resume`. | `bool` |
| `tasks.resume(id)` | La reactiva y reinicia su contador. | `bool` |
| `tasks.trigger(id)` | Ejecuta el callback ahora mismo. | `bool` |
| `tasks.clear()` | Elimina todas las tareas. | `int` |

Las funciones de gestión devuelven `false` si el id no existe (no lanzan
error). `clear` devuelve cuántas tareas se eliminaron.

Cada elemento de `tasks.list()` es un map:

| Campo | Tipo | Descripción |
| --- | --- | --- |
| `id` | `int` | Identificador de la tarea. |
| `name` | `string` | Nombre (`"task-3"` si no pasaste uno). |
| `kind` | `string` | `"every"` (periódica) o `"once"` (una vez). |
| `interval` | `float` | Intervalo en segundos. |
| `remaining` | `float` | Segundos que faltan para la próxima ejecución. |
| `last` | `float` | Timestamp de la última ejecución, o `null`. |
| `runs` | `int` | Veces que se ha ejecutado. |
| `enabled` | `bool` | `false` si está en pausa. |

## Ejemplos

```koskript
// Reloj cada 5 segundos
tasks.every(5, () { print(clock.time()) }, "reloj")

// Guardar la memoria del sistema cada minuto en un log
tasks.every_minutes(1, () {
    logger.write("memoria.log", system.memory().used_human)
}, "memoria")

// Copia de seguridad cada 2 horas
tasks.every_hours(2, () {
    archive.zip_create("backup.zip", "standard")
    output.success("backup hecho a las " + clock.time())
}, "backup")

// Recordatorio único dentro de 30 segundos
tasks.after(30, () { output.warn("¡Se acabó el tiempo!") }, "recordatorio")
```

Gestionar las tareas desde el prompt:

```koskript
output.table(tasks.list(), ["id", "name", "kind", "remaining", "runs"])

tasks.pause(1)       // congelar el reloj
tasks.resume(1)      // reactivarlo, contando de nuevo
tasks.trigger(1)     // forzar una ejecución inmediata
tasks.cancel(1)      // borrarlo
tasks.clear()        // borrar todas
```

Un monitor de CPU que se pausa cuando no lo necesitas:

```koskript
local monitor = tasks.every(2, () {
    local uso = system.cpu_percent()
    if (uso > 80) {
        output.warn("CPU alta: " + str(uso) + "%")
    }
}, "cpu")

// más tarde...
tasks.pause(monitor)
```

## Notas

- La **primera ejecución ocurre tras el intervalo**, no al programarla; usa
  `tasks.trigger(id)` si quieres ejecutarla ya.
- El planificador vive en un hilo daemon llamado `koshell-tasks`. La shell y el
  hilo comparten un candado, así que una tarea nunca se ejecuta a la vez que un
  comando tuyo: si una tarea tarda, el prompt espera a que termine.
- La salida de las tareas puede aparecer mientras estás escribiendo.
- Si una tarea lanza un error, se imprime con `output.error` y la tarea
  continúa programada; el planificador no se detiene.
- `pause` congela `remaining`; `resume` reinicia el contador con el intervalo
  completo.
- `tasks` es global al proceso: si registras la stdlib en varios runtimes,
  comparten el mismo planificador.
- Los intervalos aceptan decimales (`0.5` = medio segundo).
