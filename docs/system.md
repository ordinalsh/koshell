# system

Información del sistema: plataforma, hardware, usuario y rutas base.

```koskript
print(system.platform(), system.release(), system.machine())
print(system.memory().used_human, "/", system.memory().total_human)
```

## Identidad y plataforma

| Función | Descripción | Devuelve |
| --- | --- | --- |
| `system.platform()` | Sistema operativo (`"Windows"`, `"Linux"`, `"Darwin"`). | `string` |
| `system.release()` | Versión del kernel / SO. | `string` |
| `system.version()` | Descripción completa del SO. | `string` |
| `system.machine()` | Arquitectura (`"AMD64"`, `"arm64"`). | `string` |
| `system.hostname()` | Nombre del equipo. | `string` |
| `system.user()` | Usuario actual. | `string` |
| `system.home()` | Directorio personal. | `string` |
| `system.python()` | Versión de Python (`"3.14.6"`). | `string` |
| `system.locale()` | Configuración regional, o `"unknown"`. | `string` |
| `system.timezone()` | Zona horaria local. | `string` |

## Hardware y recursos

| Función | Descripción | Devuelve |
| --- | --- | --- |
| `system.cpu_count(logical=true)` | Núcleos lógicos o físicos. | `int` |
| `system.cpu_percent(interval=0.0)` | Uso de CPU; con `interval > 0` mide ese periodo. | `float` |
| `system.memory()` | Memoria RAM. | `map` |
| `system.swap()` | Memoria de intercambio. | `map` |
| `system.disk(path=".")` | Uso de disco de la unidad que contiene `path`. | `map` |
| `system.boot_time()` | Momento de arranque (timestamp). | `float` |
| `system.uptime()` | Segundos desde el arranque. | `float` |

`memory` devuelve `{ "total", "available", "used", "percent", "total_human",
"used_human", "available_human" }`; `swap` y `disk` siguen el mismo patrón con
campos en bytes y en formato legible.

## Acciones

| Función | Descripción | Devuelve |
| --- | --- | --- |
| `system.open(path)` | Abre archivo o carpeta con la aplicación por defecto. | `bool` |
| `system.info()` | Resumen agregado del sistema. | `map` |

`system.info()` combina plataforma, host, usuario, CPU, memoria, disco, uptime
y zona horaria en un solo map.

## Ejemplos

```koskript
// Resumen rápido
local s = system.info()
output.panel(s.hostname + " · " + s.platform + " " + s.release, "Sistema")
output.table([
    { "clave": "CPU", "valor": str(s.cpu_count) + " núcleos" },
    { "clave": "RAM", "valor": s.memory.used_human + " / " + s.memory.total_human },
    { "clave": "Disco", "valor": str(s.disk.percent) + "%" },
    { "clave": "Python", "valor": s.python }
])

// Medir CPU en una ventana de un segundo
print("CPU:", system.cpu_percent(1), "%")
```

## Notas

- Los porcentajes son floats redondeados a dos decimales cuando aplica.
- `system.open` es no bloqueante: lanza la aplicación y devuelve `true`.
- En plataformas sin `os.startfile`, se usa `open` (macOS) o `xdg-open`
  (Linux).
