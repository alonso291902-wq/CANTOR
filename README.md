# Build Your Own HTTP Server in Python 🚀

A lightweight, zero-dependency, concurrent **HTTP/1.1 Server** built completely from scratch using Python's standard library `socket` and `threading` modules.

Inspired by [codecrafters-io/build-your-own-x](https://github.com/codecrafters-io/build-your-own-x).

---

## 🌟 Features

- **Raw TCP Sockets**: Direct socket management (`socket.socket`, `bind`, `listen`, `accept`).
- **HTTP/1.1 Compliant Parser**: Parses Request Line (`METHOD`, `PATH`, `VERSION`), case-insensitive HTTP headers, and handles `Content-Length` bounded bodies.
- **Dynamic Routing**:
  - `GET /` — Health check endpoint (`200 OK`).
  - `GET /echo/<string>` — Returns dynamic echo response with correct `Content-Type` and `Content-Length`.
  - `GET /user-agent` — Inspects and returns the caller's `User-Agent` header value.
  - `GET /files/<filename>` — Reads and streams file data as `application/octet-stream`.
  - `POST /files/<filename>` — Receives body stream and writes file to disk (`201 Created`).
- **Path Traversal Protection**: Prevents `../` directory escape attacks when serving or saving files.
- **HTTP Compression**: Supports `gzip` compression when requested via `Accept-Encoding: gzip`.
- **Concurrency**: Thread-per-connection architecture supporting concurrent requests without blocking.
- **Zero Third-Party Dependencies**: Pure Python standard library.

---

## 🏗️ Architecture

```
CANTOR/
├── app/
│   ├── __init__.py        # Package exports
│   ├── http_parser.py     # HTTPRequest data model & stream parser
│   ├── http_response.py   # HTTPResponse builder & gzip compression
│   ├── router.py          # Route dispatcher & file system handler
│   ├── server.py          # Multi-threaded TCP listener & connection runner
│   └── main.py            # CLI entrypoint with argument parsing
├── tests/
│   └── test_server.py     # Comprehensive automated end-to-end socket tests
├── .gitignore
└── README.md
```

---

## 🚀 Quick Start

### 1. Run the Server
```bash
python3 -m app.main --port 4221 --directory ./files
```

Options:
- `--host`: Host to bind (default: `0.0.0.0`)
- `--port`: Port number (default: `4221`)
- `--directory`: Path to directory for file storage & retrieval (optional)
- `--log-level`: Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`)

---

## 🧪 Testing with `curl`

### 1. Basic Health Check
```bash
curl -v http://localhost:4221/
```
```http
HTTP/1.1 200 OK
Content-Length: 0
```

### 2. Echo Endpoint
```bash
curl -v http://localhost:4221/echo/hello-cantor
```
```http
HTTP/1.1 200 OK
Content-Type: text/plain
Content-Length: 12

hello-cantor
```

### 3. Read User-Agent
```bash
curl -v -H "User-Agent: MyCustomClient/1.0" http://localhost:4221/user-agent
```
```http
HTTP/1.1 200 OK
Content-Type: text/plain
Content-Length: 18

MyCustomClient/1.0
```

### 4. Gzip Compression
```bash
curl -v -H "Accept-Encoding: gzip" http://localhost:4221/echo/test-compression --output - | gunzip
```
```http
HTTP/1.1 200 OK
Content-Type: text/plain
Content-Encoding: gzip
Content-Length: 46
```

### 5. File Upload (POST)
```bash
curl -v -X POST --data "Hello, persistent storage!" http://localhost:4221/files/sample.txt
```
```http
HTTP/1.1 201 Created
Content-Length: 0
```

### 6. File Download (GET)
```bash
curl -v http://localhost:4221/files/sample.txt
```
```http
HTTP/1.1 200 OK
Content-Type: application/octet-stream
Content-Length: 26

Hello, persistent storage!
```

---

## 🔬 Running Automated Tests

Run the test suite with Python's built-in `unittest`:
```bash
python3 -m unittest discover tests
```
