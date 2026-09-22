# output

Salida formateada con `rich`: etiquetas de color, paneles, tablas, Markdown y
volcados de datos.

```koskript
output.info("arrancando")
output.success("todo listo")
output.warn("quedan 3 tareas")
output.error("algo falló")
```

## Mensajes

| Función | Descripción | Devuelve |
| --- | --- | --- |
| `output.info(message)` | Línea azul con la etiqueta `info`. | `null` |
| `output.success(message)` | Línea verde con la etiqueta `ok`. | `null` |
| `output.warn(message)` | Línea amarilla con la etiqueta `warn`. | `null` |
| `output.error(message)` | Línea roja con la etiqueta `error`. | `null` |
| `output.debug(message)` | Línea atenuada con la etiqueta `debug`. | `null` |
| `output.title(message)` | Texto en negrita. | `null` |
| `output.rule(label="")` | Línea separadora con un rótulo opcional. | `null` |
| `output.panel(message, title=null)` | Panel enmarcado. | `null` |
| `output.markdown(text)` | Renderiza Markdown en la terminal. | `null` |
| `output.pretty(value)` | Volcado legible de arrays, maps y objetos. | `null` |
| `output.clear()` | Limpia la pantalla. | `null` |

## Tablas

| Función | Descripción | Devuelve |
| --- | --- | --- |
| `output.table(rows, columns=null)` | Imprime una tabla. | `null` |

- `rows` puede ser un array de maps (las claves de la primera fila son las
  columnas) o un array de arrays.
- `columns` es un array opcional con las claves o títulos a mostrar, en orden.

```koskript
output.table([
    { "servicio": "api", "puerto": 8080, "activo": true },
    { "servicio": "db", "puerto": 5432, "activo": false }
], ["servicio", "puerto", "activo"])
```

## Ejemplos

```koskript
output.rule("Resumen del sistema")
output.panel(system.user() + "@" + system.hostname(), "Koshell")

output.title("Procesos con más memoria")
output.table(process.top(5), ["pid", "name", "memory_human"])

output.title("Documentación")
output.markdown("**Koshell** usa *Koskript*; mira `koshell.help()`.")

output.pretty({ "modulos": koshell.modules() })
```

## Notas

- `output` usa su propia consola de `rich`; es independiente de `print`.
- Los mensajes se escapan: puedes pasar corchetes o etiquetas sin que se
  interpreten como markup.
- `output.table` con un array vacío no imprime nada.
