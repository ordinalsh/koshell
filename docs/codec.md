# codec

Hashing, HMAC, codificaciones (Base64, Hex, URL), UUIDs y generación de
secretos. Todo lo que devuelve es `string`, listo para guardar o comparar.

```koskript
print(codec.hash("hola"))                     // sha256 por defecto
print(codec.base64_encode("hola"))            // aG9sYQ==
print(codec.uuid())                           // 4f0b...-...
```

## Codificaciones

| Función | Descripción | Devuelve |
| --- | --- | --- |
| `codec.base64_encode(text)` | Codifica en Base64. | `string` |
| `codec.base64_decode(text)` | Decodifica Base64 (estricto). | `string` |
| `codec.base64_url_encode(text)` | Base64 URL-safe. | `string` |
| `codec.base64_url_decode(text)` | Decodifica Base64 URL-safe. | `string` |
| `codec.hex_encode(text)` | Codifica en hexadecimal. | `string` |
| `codec.hex_decode(text)` | Decodifica hexadecimal. | `string` |
| `codec.url_encode(text)` | Codifica para URL (`%20`, ...). | `string` |
| `codec.url_decode(text)` | Decodifica una URL. | `string` |

## Hashing y firmas

| Función | Descripción | Devuelve |
| --- | --- | --- |
| `codec.hash(text, algorithm="sha256")` | Hash hexadecimal del texto. | `string` |
| `codec.hash_file(path, algorithm="sha256")` | Hash de un archivo por trozos. | `string` |
| `codec.sign(text, key, algorithm="sha256")` | HMAC hexadecimal. | `string` |
| `codec.equals(left, right)` | Comparación en tiempo constante. | `bool` |

Algoritmos válidos: cualquier nombre de `hashlib` (`md5`, `sha1`, `sha224`,
`sha256`, `sha384`, `sha512`, `blake2b`, `blake2s`, `sha3_256`, ...). Los
algoritmos `shake_*` no están soportados. Un nombre desconocido lanza
`RuntimeError`.

## Identificadores y secretos

| Función | Descripción | Devuelve |
| --- | --- | --- |
| `codec.uuid()` | UUID versión 4. | `string` |
| `codec.uuid5(text)` | UUID versión 5 derivado del texto. | `string` |
| `codec.token(length=32)` | Token hexadecimal criptográficamente seguro. | `string` |
| `codec.password(length=16, symbols=true)` | Contraseña aleatoria. | `string` |

## Ejemplos

```koskript
// Verificar integridad de una descarga
local descarga = filesystem.pathjoin(filesystem.temp(), "python-logo.png")
network.download("https://www.python.org/static/img/python-logo.png", descarga)
print("sha256:", codec.hash_file(descarga))

// Comparar un hash sin filtrar tiempo
local esperado = codec.hash("secreto")
if (codec.equals(codec.hash("secreto"), esperado)) {
    print("coincide")
}

// Firmar un mensaje
local firma = codec.sign("mensaje", "clave-secreta")
print(firma)

// Codificar datos para una URL
local query = codec.url_encode("nombre=Koshell & versión=2.0")
print("https://ejemplo.com/api?" + query)

// Generar credenciales
print("usuario_" + codec.token(8))
print(codec.password(20))
```

## Notas

- `base64_decode` usa validación estricta: texto corrupto lanza `RuntimeError`.
- `hash` y `sign` trabajan sobre texto UTF-8; usa `hash_file` para binarios.
- `equals` acepta cualquier valor y lo convierte a string antes de comparar.
