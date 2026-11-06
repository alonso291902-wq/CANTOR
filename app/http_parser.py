from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class HTTPRequest:
    method: str
    path: str
    version: str
    headers: Dict[str, str] = field(default_factory=dict)
    body: bytes = b""

    def get_header(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """Case-insensitive header retrieval."""
        return self.headers.get(name.lower(), default)


class HTTPParser:
    @staticmethod
    def parse(raw_data: bytes) -> Optional[HTTPRequest]:
        """
        Parses raw HTTP/1.1 byte stream into an HTTPRequest object.
        Returns None if request line cannot be parsed.
        """
        if not raw_data:
            return None

        # Split headers and body at first CRLF CRLF
        delimiter = b"\r\n\r\n"
        parts = raw_data.split(delimiter, 1)
        header_part = parts[0]
        body = parts[1] if len(parts) > 1 else b""

        # Decode headers as Latin-1 (RFC 7230 / ISO-8859-1 compatible)
        header_text = header_part.decode("latin-1", errors="replace")
        lines = header_text.split("\r\n")

        if not lines or not lines[0].strip():
            return None

        # Request line: <METHOD> <PATH> <VERSION>
        request_line = lines[0].strip().split()
        if len(request_line) < 3:
            return None

        method, path, version = request_line[0], request_line[1], request_line[2]

        headers: Dict[str, str] = {}
        for line in lines[1:]:
            if not line.strip():
                continue
            if ":" in line:
                key, val = line.split(":", 1)
                headers[key.strip().lower()] = val.strip()

        # Handle body slicing if Content-Length specified
        content_length_str = headers.get("content-length")
        if content_length_str and content_length_str.isdigit():
            content_length = int(content_length_str)
            body = body[:content_length]

        return HTTPRequest(
            method=method,
            path=path,
            version=version,
            headers=headers,
            body=body,
        )
