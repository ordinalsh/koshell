# koshell

Control de la propia shell: ejecutar código, cargar scripts, descubrir la
stdlib y salir.

```koskript
koshell.help("filesystem")
print(koshell.about().version)
```

## Funciones

| Función | Descripción | Devuelve |
| --- | --- | --- |
| `koshell.execute(code)` | Ejecuta código Koskript en el runtime actual. | valor |
| `koshell.eval(code)` | Alias de `execute`. | valor |
| `koshell.source(path)` | Ejecuta un archivo `.kos` local. | valor |
| `koshell.loadfrom(url, timeout=10)` | Descarga y ejecuta un script remoto. | valor |
| `koshell.modules()` | Nombres de los módulos registrados, ordenados. | `array` |
| `koshell.help(name=null)` | Ayuda generada por introspección. | `string` |
| `koshell.about()` | Nombre, versión, módulos y versión de Python. | `map` |
| `koshell.clear()` | Limpia la pantalla. | `null` |
| `koshell.exit(code=0)` | Cierra Koshell con un código de salida. | — |

## Ejecutar código y scripts

```koskript
// Código en línea
print(koshell.eval("1 + 2"))            // 3

// Archivo local
koshell.source("scripts/setup.kos")

// Script remoto
koshell.loadfrom("https://ejemplo.com/utilidades.kos")
```

Las declaraciones de nivel superior de un `execute`/`source`/`loadfrom`
persisten en el runtime: si un script define una función, estará disponible
después en el prompt.

`loadfrom` devuelve `false` si no se pudo descargar el script (sin lanzar
error); los errores de sintaxis o de ejecución del script sí se propagan.

## Descubrir la stdlib

```koskript
koshell.modules()
// ["archive", "clock", "codec", "data", "env", "filesystem",
//  "input", "logger", "network", "output", "process", "system", "tasks"]

print(koshell.help())
print(koshell.help("codec"))
```

`koshell.help` usa las firmas reales de cada función, así que siempre está
sincronizada con el código.

`koshell.about()` devuelve:

| Campo | Tipo | Descripción |
| --- | --- | --- |
| `name` | `string` | `"Koshell"`. |
| `version` | `string` | Versión de la stdlib. |
| `python` | `string` | Versión de Python. |
| `modules` | `array` | Módulos registrados. |
| `module_count` | `int` | Número de módulos. |

## Salir y limpiar

```koskript
koshell.clear()
koshell.exit()        // o koshell.exit(1)
```

`koshell.exit` termina el proceso con el código indicado (0 por defecto).

## Notas

- `koshell` es un objeto con estado: guarda el runtime y la lista de módulos
  registrados.
- También existe el atributo `koshell.version`, con la versión de la stdlib.
- `koshell.loadfrom` acepta `timeout` en segundos como segundo argumento.
