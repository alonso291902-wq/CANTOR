import gzip
from typing import Dict, Optional, Union

STATUS_PHRASES = {
    200: "OK",
    201: "Created",
    400: "Bad Request",
    404: "Not Found",
    405: "Method Not Allowed",
    500: "Internal Server Error",
}


class HTTPResponse:
    def __init__(
        self,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        body: Union[bytes, str] = b"",
    ):
        self.status_code = status_code
        self.headers: Dict[str, str] = headers.copy() if headers else {}
        if isinstance(body, str):
            self.body: bytes = body.encode("utf-8")
        else:
            self.body = body

    def set_header(self, name: str, value: str) -> "HTTPResponse":
        self.headers[name] = value
        return self

    def apply_compression(self, accept_encoding: Optional[str]) -> "HTTPResponse":
        """
        If the client accepts gzip encoding in Accept-Encoding,
        compresses the body and sets Content-Encoding: gzip.
        """
        if not accept_encoding or not self.body:
            return self

        # Accept-Encoding can be a comma-separated list like "gzip, deflate, br"
        encodings = [enc.strip().lower() for enc in accept_encoding.split(",")]
        if "gzip" in encodings:
            self.body = gzip.compress(self.body)
            self.headers["Content-Encoding"] = "gzip"

        return self

    def to_bytes(self) -> bytes:
        """Serializes the HTTP response into raw wire bytes."""
        reason = STATUS_PHRASES.get(self.status_code, "Unknown")
        status_line = f"HTTP/1.1 {self.status_code} {reason}\r\n"

        # Ensure Content-Length is updated
        self.headers["Content-Length"] = str(len(self.body))

        # Build headers
        header_lines = [f"{k}: {v}\r\n" for k, v in self.headers.items()]

        response_bytes = (
            status_line.encode("latin-1")
            + "".join(header_lines).encode("latin-1")
            + b"\r\n"
            + self.body
        )
        return response_bytes

    @classmethod
    def ok(cls, body: Union[bytes, str] = b"", content_type: str = "text/plain") -> "HTTPResponse":
        resp = cls(status_code=200, body=body)
        resp.set_header("Content-Type", content_type)
        return resp

    @classmethod
    def created(cls) -> "HTTPResponse":
        return cls(status_code=201)

    @classmethod
    def not_found(cls) -> "HTTPResponse":
        return cls(status_code=404)

    @classmethod
    def bad_request(cls, message: str = "Bad Request") -> "HTTPResponse":
        resp = cls(status_code=400, body=message)
        resp.set_header("Content-Type", "text/plain")
        return resp
