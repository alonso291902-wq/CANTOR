import os
from typing import Optional
from app.http_parser import HTTPRequest
from app.http_response import HTTPResponse


class Router:
    def __init__(self, directory: Optional[str] = None):
        self.directory = os.path.abspath(directory) if directory else None

    def route(self, request: HTTPRequest) -> HTTPResponse:
        method = request.method.upper()
        path = request.path

        # 1. Root route: GET /
        if path == "/":
            if method == "GET":
                return HTTPResponse.ok()
            return HTTPResponse(status_code=405)

        # 2. Echo route: GET /echo/<str>
        if path.startswith("/echo/"):
            if method == "GET":
                echo_str = path[len("/echo/"):]
                return HTTPResponse.ok(body=echo_str, content_type="text/plain")
            return HTTPResponse(status_code=405)

        # 3. User-Agent route: GET /user-agent
        if path == "/user-agent":
            if method == "GET":
                user_agent = request.get_header("User-Agent", default="")
                return HTTPResponse.ok(body=user_agent, content_type="text/plain")
            return HTTPResponse(status_code=405)

        # 4. Files route: GET or POST /files/<filename>
        if path.startswith("/files/"):
            filename = path[len("/files/"):]

            # Security: Prevent path traversal attacks
            safe_filename = os.path.basename(filename)
            if not self.directory or safe_filename != filename:
                return HTTPResponse.not_found()

            file_path = os.path.join(self.directory, safe_filename)

            if method == "GET":
                if os.path.isfile(file_path):
                    with open(file_path, "rb") as f:
                        file_data = f.read()
                    resp = HTTPResponse.ok(
                        body=file_data,
                        content_type="application/octet-stream",
                    )
                    return resp
                return HTTPResponse.not_found()

            elif method == "POST":
                os.makedirs(self.directory, exist_ok=True)
                with open(file_path, "wb") as f:
                    f.write(request.body)
                return HTTPResponse.created()

            return HTTPResponse(status_code=405)

        # Default fallback: 404 Not Found
        return HTTPResponse.not_found()
