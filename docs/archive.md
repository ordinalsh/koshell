# archive

Creación, inspección y extracción de archivos ZIP y TAR (con o sin compresión).

```koskript
archive.zip_create("proyecto.zip", ["standard", "main.py"])
output.table(archive.zip_list("proyecto.zip"), ["name", "size"])
```

## ZIP

| Función | Descripción | Devuelve |
| --- | --- | --- |
| `archive.zip_create(path, source, compression="deflated")` | Crea un ZIP nuevo. | `map` |
| `archive.zip_add(path, source)` | Añade entradas a un ZIP (lo crea si no existe). | `map` |
| `archive.zip_extract(path, destination=".")` | Extrae todo. | `array` |
| `archive.zip_list(path)` | Lista el contenido. | `array` |

`source` puede ser un `string` o un `array` de rutas. Los directorios se añaden
recursivamente conservando su nombre como prefijo.

Compresiones válidas: `"stored"`, `"deflated"`, `"bzip2"` y `"lzma"`.

## TAR

| Función | Descripción | Devuelve |
| --- | --- | --- |
| `archive.tar_create(path, source, compression=null)` | Crea un TAR. | `map` |
| `archive.tar_extract(path, destination=".")` | Extrae todo. | `array` |
| `archive.tar_list(path)` | Lista el contenido. | `array` |

Si `compression` es `null` se deduce por la extensión: `.tar` → sin compresión,
`.tar.gz`/`.tgz` → gzip (por defecto), `.tar.bz2`/`.tbz2` → bzip2,
`.tar.xz`/`.txz` → xz. Valores explícitos: `"none"`, `"gz"`, `"bz2"`, `"xz"`.

## Genéricas

| Función | Descripción | Devuelve |
| --- | --- | --- |
| `archive.pack(path, source)` | Crea el archivo según la extensión (`.zip` o `.tar*`). | `map` |
| `archive.unpack(path, destination=".")` | Extrae un ZIP o TAR detectando el formato. | `array` |
| `archive.contains(path, member)` | ¿Existe esa entrada? | `bool` |
| `archive.read(path, member)` | Lee una entrada como texto UTF-8. | `string` |

`zip_create`, `zip_add` y `tar_create` devuelven
`{ "path": ..., "entries": n }` con el número de archivos añadidos.

`zip_list` y `tar_list` devuelven maps con `name`, `size`, `compressed`
(`null` en TAR), `modified` y `dir`.

## Ejemplos

```koskript
// Empaquetar un directorio y verificar el contenido
archive.zip_create("stdlib.zip", "standard")
print("Entradas:", len(archive.zip_list("stdlib.zip")))
print(archive.contains("stdlib.zip", "standard/network.py"))
print(archive.read("stdlib.zip", "standard/__init__.py"))

// Extraer en una carpeta nueva
archive.zip_extract("stdlib.zip", "copia")
print(filesystem.exists("copia/standard/network.py"))

// TAR con compresión deducida por la extensión
archive.tar_create("backup.tar.gz", ["docs", "main.py"])
archive.unpack("backup.tar.gz", "restaurado")

// Detección automática
archive.pack("todo.zip", ["standard", "docs"])
archive.unpack("todo.zip", "todo")
```

## Notas

- La extracción de TAR usa `filter="data"` cuando el intérprete lo soporta,
  evitando rutas maliciosas.
- `zip_add` conserva el contenido previo del archivo.
- `archive.read` decodifica en UTF-8 y sustituye los bytes inválidos, así que
  también funciona con archivos de texto no estrictos.
