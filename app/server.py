import logging
import socket
import threading
from typing import Optional

from app.http_parser import HTTPParser
from app.http_response import HTTPResponse
from app.router import Router

logger = logging.getLogger(__name__)


class HTTPServer:
    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 4221,
        directory: Optional[str] = None,
    ):
        self.host = host
        self.port = port
        self.router = Router(directory=directory)
        self.server_socket: Optional[socket.socket] = None
        self._running = False

    def handle_client(self, client_sock: socket.socket, client_addr: tuple):
        """Processes an individual client TCP connection."""
        try:
            client_sock.settimeout(5.0)
            raw_data = bytearray()

            # Read initial chunk containing HTTP headers
            while b"\r\n\r\n" not in raw_data:
                chunk = client_sock.recv(4096)
                if not chunk:
                    break
                raw_data.extend(chunk)

            if not raw_data:
                return

            # Determine if a full body is expected via Content-Length
            header_end = raw_data.find(b"\r\n\r\n")
            if header_end != -1:
                header_text = raw_data[:header_end].decode("latin-1", errors="replace")
                content_length = 0
                for line in header_text.split("\r\n"):
                    if line.lower().startswith("content-length:"):
                        try:
                            content_length = int(line.split(":", 1)[1].strip())
                        except ValueError:
                            pass
                        break

                bytes_needed = (header_end + 4 + content_length) - len(raw_data)
                while bytes_needed > 0:
                    chunk = client_sock.recv(min(4096, bytes_needed))
                    if not chunk:
                        break
                    raw_data.extend(chunk)
                    bytes_needed -= len(chunk)

            # Parse request
            request = HTTPParser.parse(bytes(raw_data))
            if not request:
                response = HTTPResponse.bad_request()
            else:
                response = self.router.route(request)
                accept_encoding = request.get_header("Accept-Encoding")
                response.apply_compression(accept_encoding)

            client_sock.sendall(response.to_bytes())

        except socket.timeout:
            pass
        except Exception as e:
            logger.error(f"Error handling connection from {client_addr}: {e}")
        finally:
            client_sock.close()

    def start(self):
        """Starts the multi-threaded HTTP server."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(128)
        self._running = True

        logger.info(f"Server started on {self.host}:{self.port} (Serving files from: {self.router.directory})")

        try:
            while self._running:
                try:
                    client_sock, client_addr = self.server_socket.accept()
                except socket.timeout:
                    continue
                except OSError:
                    break

                # Spawn worker thread for concurrent request processing
                thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_sock, client_addr),
                    daemon=True,
                )
                thread.start()
        finally:
            self.stop()

    def stop(self):
        """Stops the server and closes the listening socket."""
        self._running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass
            self.server_socket = None
        logger.info("Server stopped.")
