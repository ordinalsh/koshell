# network

HTTP, DNS y comprobaciones de conectividad. Usa `requests` para HTTP y sockets
para lo demás.

```koskript
local r = network.get("https://api.github.com/repos/alesis-buzz/koskript")
if (r.ok) {
    local repo = network.get_json("https://api.github.com/repos/alesis-buzz/koskript")
    print(repo.full_name, repo.stargazers_count)
}
```

## Peticiones HTTP

| Función | Descripción | Devuelve |
| --- | --- | --- |
| `network.request(method, url, headers=null, params=null, data=null, json=null, timeout=10)` | Petición genérica. | `map` |
| `network.get(url, headers=null, timeout=10)` | GET. | `map` |
| `network.post(url, data=null, json=null, headers=null, timeout=10)` | POST. | `map` |
| `network.put(url, data=null, json=null, headers=null, timeout=10)` | PUT. | `map` |
| `network.patch(url, data=null, json=null, headers=null, timeout=10)` | PATCH. | `map` |
| `network.delete(url, headers=null, timeout=10)` | DELETE. | `map` |
| `network.head(url, headers=null, timeout=10)` | HEAD. | `map` |
| `network.get_json(url, headers=null, timeout=10)` | GET y decodifica JSON. | valor |
| `network.post_json(url, value, headers=null, timeout=10)` | POST con JSON y decodifica la respuesta. | valor |

Todas las peticiones devuelven un map con:

| Campo | Tipo | Descripción |
| --- | --- | --- |
| `ok` | `bool` | `true` si el código HTTP es menor que 400. |
| `status` | `int` | Código HTTP. |
| `reason` | `string` | Frase del código (`"OK"`, `"Not Found"`). |
| `text` | `string` | Cuerpo de la respuesta. |
| `url` | `string` | URL final (tras redirecciones). |
| `headers` | `map` | Cabeceras de la respuesta. |
| `elapsed` | `float` | Segundos que tardó. |

En `post`, `put`, `patch` y `request`, `data` envía un formulario (map) o texto
plano y `json` serializa cualquier valor como JSON. Los `headers` y `params`
son maps.

## Descargas y conectividad

| Función | Descripción | Devuelve |
| --- | --- | --- |
| `network.download(url, path, timeout=60)` | Descarga un archivo a disco por trozos. | `map` |
| `network.is_online(host="1.1.1.1", port=53, timeout=2)` | ¿Se puede conectar al host/puerto? | `bool` |
| `network.port_open(host, port, timeout=1)` | ¿Está abierto ese puerto TCP? | `bool` |
| `network.resolve(host)` | Resuelve un nombre a IP. `null` si falla. | `string` |
| `network.local_ip()` | IP local usada para salir a internet. | `string` |
| `network.public_ip(timeout=5)` | IP pública. `null` si no hay conexión. | `string` |

`download` devuelve `{ "ok", "path", "size", "status" }`.

## Ejemplos

```koskript
// Cabeceras y formulario
local r = network.post("https://httpbin.org/post",
    { "nombre": "koshell" }, null,
    { "User-Agent": "Koshell/2.0" })
print(r.status, r.elapsed)

// Descargar un archivo
local destino = filesystem.pathjoin(filesystem.temp(), "logo.png")
local d = network.download("https://www.python.org/static/img/python-logo.png", destino)
print(d.size, "bytes en", d.path)

// Comprobar si un servicio está arriba
if (network.port_open("localhost", 5432)) {
    print("PostgreSQL disponible")
}

// Guardar una respuesta JSON
local datos = network.get_json("https://api.ipify.org?format=json")
data.write_json("ip.json", datos)
```

## Notas

- Los `timeout` están en segundos y aplican a la conexión y a la lectura.
- Si se agota el tiempo o falla la conexión, se lanza `RuntimeError` (excepto
  `resolve`, `public_ip` y las comprobaciones booleanas, que devuelven
  `null`/`false`).
- `get_json` y `post_json` lanzan `RuntimeError` si la respuesta no es JSON
  válido.
- `network` no cifra nada por su cuenta: HTTPS lo gestiona `requests`.
