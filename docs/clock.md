# clock

Fechas, horas y temporización. Todos los timestamps son segundos desde el epoch
(`1970-01-01`), como los que devuelve `clock.now()`.

```koskript
local inicio = clock.now()
// ... trabajo ...
print("Tardó", clock.elapsed(inicio), "segundos")
```

## Funciones

| Función | Descripción | Devuelve |
| --- | --- | --- |
| `clock.now()` | Timestamp local actual. | `float` |
| `clock.utc_now()` | Timestamp UTC actual. | `float` |
| `clock.iso(timestamp=null)` | Fecha y hora local en ISO 8601. | `string` |
| `clock.utc_iso(timestamp=null)` | Fecha y hora UTC en ISO 8601. | `string` |
| `clock.date(timestamp=null)` | Fecha `YYYY-MM-DD`. | `string` |
| `clock.time(timestamp=null)` | Hora `HH:MM:SS`. | `string` |
| `clock.weekday(timestamp=null)` | Nombre del día de la semana. | `string` |
| `clock.format(timestamp, pattern)` | Formatea con un patrón `strftime`. | `string` |
| `clock.parse(text, pattern)` | Convierte texto a timestamp. `null` si no encaja. | `float` |
| `clock.parts(timestamp=null)` | Componentes de la fecha. | `map` |
| `clock.sleep(seconds)` | Pausa la shell. | `float` |
| `clock.elapsed(start)` | Segundos transcurridos desde `start`. | `float` |

Todas las funciones con `timestamp=null` usan el momento actual.

`clock.parts` devuelve `{ "year", "month", "day", "hour", "minute", "second",
"weekday", "weekday_index", "yearday", "timestamp" }`, donde `weekday_index` va
de 0 (lunes) a 6 (domingo).

## Ejemplos

```koskript
// Fecha legible
print(clock.iso())                    // 2026-09-21T18:04:11
print(clock.date(), clock.time())
print(clock.weekday())                // Monday

// Patrones personalizados
print(clock.format(clock.now(), "%d/%m/%Y %H:%M"))
print(clock.format(clock.now(), "%A, %d de %B"))

// Convertir texto a timestamp
local fin_de_ano = clock.parse("2026-12-31", "%Y-%m-%d")
print("Días restantes:", math.floor((fin_de_ano - clock.now()) / 86400))

// Medir una operación
local t0 = clock.now()
clock.sleep(0.25)
print(clock.elapsed(t0))              // ~0.25
```

## Notas

- `clock.sleep` bloquea la shell; úsalo en scripts, no en el prompt si quieres
  seguir escribiendo.
- `clock.parse` devuelve `null` cuando el texto no coincide con el patrón, en
  lugar de lanzar error.
- `clock.weekday` usa el idioma del sistema.
