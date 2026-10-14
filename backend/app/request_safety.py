"""Bound request bodies before JSON/multipart parsing, including chunked requests."""
from starlette.responses import JSONResponse


class BodyLimitMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] not in ("POST", "PUT", "PATCH"):
            return await self.app(scope, receive, send)
        path = scope["path"]
        limit = 64 * 1024
        if "/initialRegistrations/" in path:
            limit = 30 * 1024 * 1024  # 20 MB of base64 annexes plus registration text.
        elif "/projects/" in path or "/admin/media/" in path or ("/innovatec/" in path and path.endswith(("/documentos", "/archivos"))):
            limit = 9 * 1024 * 1024
        for key, value in scope.get("headers", []):
            if key == b"content-type" and value.split(b";", 1)[0].strip().lower() == b"application/x-www-form-urlencoded":
                # All existing endpoints use JSON or multipart uploads; avoid an
                # unnecessary parser whose field limits differ in Starlette 0.x.
                return await JSONResponse({"detail": "Envía JSON o multipart/form-data para archivos."}, status_code=415)(scope, receive, send)
            if key == b"content-length":
                try:
                    length = int(value)
                    if length < 0:
                        raise ValueError()
                    too_large = length > limit
                except ValueError:
                    return await JSONResponse({"detail": "El tamaño de la solicitud no es válido."}, status_code=400)(scope, receive, send)
                if too_large:
                    return await self.reject(scope, receive, send)
        messages, size = [], 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            size += len(message.get("body", b""))
            if size > limit:
                return await self.reject(scope, receive, send)
            messages.append(message)
            if not message.get("more_body", False):
                break
        iterator = iter(messages)

        async def bounded_receive():
            return next(iterator, None) or await receive()

        await self.app(scope, bounded_receive, send)

    async def reject(self, scope, receive, send):
        await JSONResponse({"detail": "La solicitud supera el tamaño permitido."}, status_code=413)(scope, receive, send)
