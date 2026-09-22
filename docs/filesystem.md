# filesystem

Archivos, directorios, rutas y espacio en disco. Es el módulo más grande de la
stdlib: 45 funciones.

```koskript
local raiz = filesystem.current_dir()
for (entry in filesystem.entries(raiz)) {
    print(entry.name, entry.size)
}
```

## Rutas

| Función | Descripción | Devuelve |
| --- | --- | --- |
| `filesystem.pathjoin(path, *paths)` | Une segmentos de ruta con el separador del sistema. | `string` |
| `filesystem.abspath(path)` | Convierte a ruta absoluta. | `string` |
| `filesystem.realpath(path)` | Resuelve enlaces simbólicos y `..`. | `string` |
| `filesystem.normpath(path)` | Normaliza la ruta sin tocar el disco. | `string` |
| `filesystem.expanduser(path)` | Expande `~` al directorio del usuario. | `string` |
| `filesystem.basename(path)` | Último componente de la ruta. | `string` |
| `filesystem.dirname(path)` | Ruta sin el último componente. | `string` |
| `filesystem.extension(path)` | Extensión sin el punto (`"gz"`). | `string` |
| `filesystem.stem(path)` | Nombre del archivo sin extensión. | `string` |
| `filesystem.current_dir()` | Directorio de trabajo actual. | `string` |
| `filesystem.home()` | Directorio personal del usuario. | `string` |
| `filesystem.temp()` | Directorio temporal del sistema. | `string` |
| `filesystem.drives()` | Raíces disponibles (`["C:\\", "D:\\"]`). | `array` |

## Consultas

| Función | Descripción | Devuelve |
| --- | --- | --- |
| `filesystem.exists(path)` | ¿Existe la ruta? | `bool` |
| `filesystem.isfile(path)` | ¿Es un archivo? | `bool` |
| `filesystem.isdir(path)` | ¿Es un directorio? | `bool` |
| `filesystem.islink(path)` | ¿Es un enlace simbólico? | `bool` |
| `filesystem.size(path)` | Tamaño en bytes. | `int` |
| `filesystem.modified(path)` | Última modificación (timestamp). | `float` |
| `filesystem.created(path)` | Creación (timestamp). | `float` |
| `filesystem.accessed(path)` | Último acceso (timestamp). | `float` |
| `filesystem.disk(path=".")` | Uso de disco de la unidad. | `map` |

`filesystem.disk` devuelve `{ "path", "total", "used", "free", "percent" }` en
bytes y porcentaje.

## Directorios

| Función | Descripción | Devuelve |
| --- | --- | --- |
| `filesystem.navigate(path)` | Cambia el directorio de trabajo. `false` si no existe; error si es un archivo. | `bool` |
| `filesystem.chdir(path)` | Alias de `navigate`. | `bool` |
| `filesystem.makedir(path)` | Crea un directorio. Falla si ya existe. | `string` |
| `filesystem.makedirs(path)` | Crea la ruta completa; no falla si existe. | `string` |
| `filesystem.rmdir(path, verification=false)` | Borra un directorio recursivamente. | `bool` |
| `filesystem.listdir(path)` | Nombres del directorio, ordenados. `false` si no existe. | `array` |
| `filesystem.entries(path)` | Detalle de cada entrada. | `array` |
| `filesystem.walk(path, callback=null)` | Recorre recursivamente todo el árbol. Error si la ruta no existe. | `array` |

`entries` y `walk` devuelven maps con:

| Campo | Tipo | Descripción |
| --- | --- | --- |
| `name` | `string` | Nombre del archivo o carpeta. |
| `path` | `string` | Ruta tal como se construyó. |
| `file` | `bool` | ¿Es archivo? |
| `dir` | `bool` | ¿Es directorio? |
| `link` | `bool` | ¿Es enlace? |
| `size` | `int` | Tamaño en bytes. |
| `modified` / `created` / `accessed` | `float` | Timestamps. |

`rmdir` borra también directorios con contenido, pero exige
`verification=true` para hacerlo:

```koskript
filesystem.rmdir("build", true)
```

`listdir`, `remfile`, `rmdir` y `navigate` devuelven `false` cuando la ruta no
existe; `entries`, `walk` y `read` lanzan `RuntimeError`. `glob` y `find`
devuelven un array vacío si no hay coincidencias.

Si el callback de `walk` es una lambda o función de Koskript, se invoca por
cada entrada:

```koskript
filesystem.walk("standard", (entry) {
    if (entry.file) {
        print(entry.name)
    }
})
```

## Archivos

| Función | Descripción | Devuelve |
| --- | --- | --- |
| `filesystem.read(path, encoding="utf-8")` | Lee el archivo como texto. | `string` |
| `filesystem.write(path, text, append=false, encoding="utf-8")` | Escribe (o añade) texto. | `string` |
| `filesystem.readlines(path, encoding="utf-8")` | Lee y separa en líneas (sin `\n`). | `array` |
| `filesystem.writelines(path, lines, append=false, encoding="utf-8")` | Escribe un array de líneas. | `string` |
| `filesystem.touch(path)` | Crea un archivo vacío. | `bool` |
| `filesystem.copy(source, destination)` | Copia un archivo conservando metadatos. | `string` |
| `filesystem.copytree(source, destination)` | Copia un árbol de directorios. | `string` |
| `filesystem.move(source, destination)` | Mueve archivo o directorio. | `string` |
| `filesystem.rename(source, destination)` | Renombra (reemplaza el destino). | `string` |
| `filesystem.remfile(path)` | Borra un archivo. `false` si no existe. | `bool` |
| `filesystem.remove(path)` | Alias de `remfile`. | `bool` |
| `filesystem.mktemp(prefix="koshell-", suffix=".tmp")` | Crea un archivo temporal vacío. | `string` |
| `filesystem.open(path)` | Abre la ruta con la aplicación por defecto. | `bool` |

Las funciones que devuelven `string` devuelven la ruta resultante, para poder
encadenar:

```koskript
local destino = filesystem.pathjoin(filesystem.temp(), "koshell-demo.txt")
filesystem.write(destino, "hola\n", false)
filesystem.write(destino, "mundo\n", true)
print(filesystem.readlines(destino))
filesystem.copy(destino, destino + ".bak")
filesystem.remfile(destino + ".bak")
```

## Búsqueda

| Función | Descripción | Devuelve |
| --- | --- | --- |
| `filesystem.glob(path, pattern)` | Busca con patrón glob, recursivo (`**`). | `array` |
| `filesystem.find(path, pattern)` | Alias de `glob`. | `array` |

```koskript
filesystem.glob(".", "**/*.md")
filesystem.glob("standard", "*.py")
```

## Ejemplo completo

```koskript
local dir = filesystem.pathjoin(filesystem.current_dir(), "docs")

local md = filesystem.glob(dir, "*.md")
print("Páginas:", len(md))

local total = 0
for (page in md) {
    total = total + filesystem.size(page)
}
print("Bytes:", total)

output.table(filesystem.entries(dir), ["name", "size"])
```
