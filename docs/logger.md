# logger

Logs de texto con marca de tiempo y nivel. Cada línea tiene el formato:

```
[2026-09-21T18:04:11] INFO mensaje
```

```koskript
logger.write("app.log", "servidor arrancado")
logger.write("app.log", "puerto ocupado", "error")
print(logger.read("app.log"))
```

## Funciones

| Función | Descripción | Devuelve |
| --- | --- | --- |
| `logger.write(path, message, level="info")` | Añade una línea al log (lo crea si no existe). | `string` |
| `logger.read(path, lines=20)` | Últimas `lines` líneas; con `lines <= 0`, todas. | `array` |
| `logger.tail(path, lines=20)` | Alias de `read`. | `array` |
| `logger.clear(path)` | Vacía el archivo. | `string` |
| `logger.size(path)` | Tamaño en bytes. | `int` |
| `logger.exists(path)` | ¿Existe el archivo? | `bool` |
| `logger.levels()` | Niveles admitidos. | `array` |

Niveles: `"debug"`, `"info"`, `"warn"`, `"error"`. Un nivel desconocido lanza
`RuntimeError`.

## Ejemplos

```koskript
local log = filesystem.pathjoin(filesystem.current_dir(), "koshell.log")

logger.write(log, "inicio de sesión")
logger.write(log, "quedan pocos recursos", "warn")
logger.write(log, "no se pudo conectar", "error")

// Ver las últimas 2 líneas
for (linea in logger.tail(log, 2)) {
    print(linea)
}

// Rotar manualmente
if (logger.size(log) > 100000) {
    filesystem.copy(log, log + ".1")
    logger.clear(log)
}

print(logger.levels())
```

## Notas

- `logger.write` añade siempre; nunca sobrescribe.
- `logger.read` devuelve `[]` si el archivo no existe (no lanza error).
- El nivel se guarda en mayúsculas aunque lo pases en minúsculas.
