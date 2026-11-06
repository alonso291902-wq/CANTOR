import gzip
import os
import socket
import tempfile
import threading
import time
import unittest

from app.server import HTTPServer


class TestHTTPServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.port = 4221
        cls.server = HTTPServer(host="127.0.0.1", port=cls.port, directory=cls.temp_dir.name)
        cls.server_thread = threading.Thread(target=cls.server.start, daemon=True)
        cls.server_thread.start()
        time.sleep(0.3)  # Allow socket to bind and start listening

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()
        cls.temp_dir.cleanup()

    def send_raw_request(self, request_bytes: bytes) -> bytes:
        """Helper to send raw bytes over TCP socket and receive response."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(2.0)
            sock.connect(("127.0.0.1", self.port))
            sock.sendall(request_bytes)
            chunks = []
            while True:
                try:
                    data = sock.recv(4096)
                    if not data:
                        break
                    chunks.append(data)
                except socket.timeout:
                    break
            return b"".join(chunks)

    def test_root_path_200(self):
        req = b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n"
        res = self.send_raw_request(req)
        self.assertTrue(res.startswith(b"HTTP/1.1 200 OK\r\n"))

    def test_unknown_path_404(self):
        req = b"GET /some-nonexistent-path HTTP/1.1\r\nHost: localhost\r\n\r\n"
        res = self.send_raw_request(req)
        self.assertTrue(res.startswith(b"HTTP/1.1 404 Not Found\r\n"))

    def test_echo_path(self):
        req = b"GET /echo/abc-xyz HTTP/1.1\r\nHost: localhost\r\n\r\n"
        res = self.send_raw_request(req)
        self.assertIn(b"HTTP/1.1 200 OK", res)
        self.assertIn(b"Content-Type: text/plain", res)
        self.assertIn(b"Content-Length: 7", res)
        self.assertTrue(res.endswith(b"\r\n\r\nabc-xyz"))

    def test_user_agent(self):
        agent_str = "CustomClient/2.0"
        req = f"GET /user-agent HTTP/1.1\r\nHost: localhost\r\nUser-Agent: {agent_str}\r\n\r\n".encode()
        res = self.send_raw_request(req)
        self.assertIn(b"HTTP/1.1 200 OK", res)
        self.assertTrue(res.endswith(f"\r\n\r\n{agent_str}".encode()))

    def test_file_create_and_read(self):
        filename = "test_doc.txt"
        file_content = b"Content inside generated file."

        # POST /files/test_doc.txt
        post_req = (
            f"POST /files/{filename} HTTP/1.1\r\n"
            f"Host: localhost\r\n"
            f"Content-Length: {len(file_content)}\r\n\r\n"
        ).encode() + file_content

        post_res = self.send_raw_request(post_req)
        self.assertIn(b"HTTP/1.1 201 Created", post_res)

        # GET /files/test_doc.txt
        get_req = f"GET /files/{filename} HTTP/1.1\r\nHost: localhost\r\n\r\n".encode()
        get_res = self.send_raw_request(get_req)
        self.assertIn(b"HTTP/1.1 200 OK", get_res)
        self.assertIn(b"Content-Type: application/octet-stream", get_res)
        self.assertTrue(get_res.endswith(b"\r\n\r\n" + file_content))

    def test_file_path_traversal_protection(self):
        req = b"GET /files/../etc/passwd HTTP/1.1\r\nHost: localhost\r\n\r\n"
        res = self.send_raw_request(req)
        self.assertIn(b"HTTP/1.1 404 Not Found", res)

    def test_gzip_compression(self):
        echo_str = "compress-this-response-body-string"
        req = (
            f"GET /echo/{echo_str} HTTP/1.1\r\n"
            f"Host: localhost\r\n"
            f"Accept-Encoding: gzip, deflate\r\n\r\n"
        ).encode()

        res = self.send_raw_request(req)
        self.assertIn(b"HTTP/1.1 200 OK", res)
        self.assertIn(b"Content-Encoding: gzip", res)

        parts = res.split(b"\r\n\r\n", 1)
        self.assertEqual(len(parts), 2)
        compressed_body = parts[1]
        decompressed = gzip.decompress(compressed_body)
        self.assertEqual(decompressed.decode("utf-8"), echo_str)

    def test_concurrent_connections(self):
        errors = []

        def client_worker(idx):
            try:
                val = f"worker-{idx}"
                req = f"GET /echo/{val} HTTP/1.1\r\nHost: localhost\r\n\r\n".encode()
                res = self.send_raw_request(req)
                if not res.endswith(f"\r\n\r\n{val}".encode()):
                    errors.append(f"Worker {idx} mismatch")
            except Exception as e:
                errors.append(f"Worker {idx} error: {e}")

        threads = [threading.Thread(target=client_worker, args=(i,)) for i in range(15)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Concurrent client errors: {errors}")


if __name__ == "__main__":
    unittest.main()
