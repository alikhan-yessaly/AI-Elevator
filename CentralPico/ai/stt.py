import os
import socket
import ssl
import ujson
import gc


class STT:
    def __init__(self, host, path, api_key):
        self.host     = host
        self.path     = path
        self.api_key  = api_key
        self.boundary = "PicoWStreamBoundary"

    def transcribe_from_file(self, file_path):
        file_size = os.stat(file_path)[6]

        def field(name, value):
            return "--{}\r\nContent-Disposition: form-data; name=\"{}\"\r\n\r\n{}\r\n".format(
                self.boundary, name, value)

        fields = [
            field("language",        "auto"),
            field("response_format", "json"),
            field("temperature",     "1"),
            field("include_raw",     "false"),
            field("stream",          "false"),
        ]

        file_header = (
            "--{}\r\nContent-Disposition: form-data; name=\"audio\"; filename=\"{}\"\r\n"
            "Content-Type: audio/wav\r\n\r\n"
        ).format(self.boundary, file_path.split("/")[-1])
        file_footer = "\r\n--{}--\r\n".format(self.boundary)

        content_length = (sum(len(f) for f in fields)
                          + len(file_header) + file_size + len(file_footer))

        gc.collect()

        raw_s = None
        s     = None
        try:
            addr  = socket.getaddrinfo(self.host, 443)[0][-1]
            raw_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            raw_s.settimeout(20)
            raw_s.connect(addr)
            s = ssl.wrap_socket(raw_s, server_hostname=self.host)

            headers = (
                "POST {} HTTP/1.1\r\n"
                "Host: {}\r\n"
                "X-API-Key: {}\r\n"
                "Content-Type: multipart/form-data; boundary={}\r\n"
                "Content-Length: {}\r\n"
                "Connection: close\r\n\r\n"
            ).format(self.path, self.host, self.api_key, self.boundary, content_length)

            s.write(headers.encode())
            for f in fields:
                s.write(f.encode())
            s.write(file_header.encode())

            buf = bytearray(512)
            with open(file_path, "rb") as f:
                while True:
                    n = f.readinto(buf)
                    if n == 0:
                        break
                    s.write(buf[:n])

            s.write(file_footer.encode())

            while True:
                line = s.readline()
                if not line or line == b"\r\n":
                    break

            body = bytearray()
            while True:
                chunk = s.read(256)
                if not chunk:
                    break
                body.extend(chunk)

            return ujson.loads(body.decode())["text"]

        finally:
            try:
                if s is not None:
                    s.close()
                elif raw_s is not None:
                    raw_s.close()
            except Exception:
                pass
