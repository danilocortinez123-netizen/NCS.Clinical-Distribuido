import jwt
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

from ..config import settings

PUBLIC_PATHS = {
    "/",
    "/health",
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/docs",
    "/openapi.json",
    "/static",
    "/favicon.ico",
}


class JWTAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if any(path.startswith(p) for p in PUBLIC_PATHS):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=HTTP_401_UNAUTHORIZED,
                content={"error": "Token de acceso requerido"},
            )

        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm],
            )
            request.state.user = payload
        except jwt.ExpiredSignatureError:
            return JSONResponse(
                status_code=HTTP_401_UNAUTHORIZED,
                content={"error": "Token expirado"},
            )
        except jwt.InvalidTokenError:
            return JSONResponse(
                status_code=HTTP_403_FORBIDDEN,
                content={"error": "Token inválido"},
            )

        return await call_next(request)
