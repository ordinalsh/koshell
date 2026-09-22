# data

Lectura y escritura de datos estructurados: JSON, CSV y archivos de líneas.
Para texto plano usa [`filesystem.read`](filesystem.md) y
[`filesystem.write`](filesystem.md).

```koskript
local config = data.read_json("config.json")
print(config.version)
config.debug = true
data.write_json("config.json", config)
```

## Funciones

| Función | Descripción | Devuelve |
| --- | --- | --- |
| `data.read_json(path)` | Lee y decodifica un JSON. | valor |
| `data.write_json(path, value, indent=2)` | Escribe un valor como JSON (UTF-8, sin escapar acentos). | `string` |
| `data.read_lines(path)` | Lee el archivo y devuelve sus líneas sin `\n`. | `array` |
| `data.write_lines(path, lines, append=false)` | Escribe un array de líneas. | `string` |
| `data.read_csv(path, headers=true, types=false)` | Lee un CSV. | `array` |
| `data.write_csv(path, rows, append=false)` | Escribe un CSV. | `string` |

Las funciones de escritura devuelven la ruta del archivo.

## JSON

`read_json` devuelve arrays, maps y primitivas de Koskript. Un JSON inválido o
un archivo inexistente lanza `RuntimeError`.

```koskript
data.write_json("package.json", {
    "name": "koshell",
    "version": "2.0.0",
    "modules": ["filesystem", "network", "codec"]
})

local pkg = data.read_json("package.json")
print(pkg.name, len(pkg.modules))
```

## CSV

- Con `headers=true` (por defecto) cada fila es un map usando la primera línea
  como cabeceras.
- Con `headers=false` cada fila es un array de celdas.
- Con `types=true` se convierten a `int` o `float` las celdas que parezcan
  números.

Al escribir, `rows` puede ser un array de maps (se usa el orden de claves de la
primera fila) o un array de arrays.

```koskript
data.write_csv("ventas.csv", [
    { "mes": "enero", "total": 1200 },
    { "mes": "febrero", "total": 1450 }
])

local ventas = data.read_csv("ventas.csv", true, true)
for (fila in ventas) {
    print(fila.mes, fila.total * 2)
}

// Añadir filas sin repetir cabecera
data.write_csv("ventas.csv", [{ "mes": "marzo", "total": 980 }], true)
```

## Líneas

```koskript
data.write_lines("tareas.txt", ["comprar", "estudiar", "programar"])
array.push(data.read_lines("tareas.txt"), "descansar")
```

## Notas

- `write_json` usa `ensure_ascii=false`: los caracteres no ASCII se guardan tal
  cual.
- `read_csv` y `write_csv` abren los archivos en modo compatible con CSV
  (`newline=""`), por lo que funcionan con finales de línea de cualquier
  sistema.
- `read_lines` acepta también archivos con `\r\n`; las líneas no incluyen el
  salto.
