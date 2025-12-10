import os
from dotenv import load_dotenv
from fastapi import Request, status
from fastapi.responses import JSONResponse
from jose import jwt, JWTError

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

# NEW: backend-to-backend token
BACKEND_TOKEN = os.getenv("BACKEND_TOKEN")


# Paths requiring authentication
PROTECTED_PATHS = ["/mssql"]


async def jwt_middleware(request: Request, call_next):
    path = request.url.path

    print("PATH:", path)
    print("HEADER:", request.headers.get("Authorization"))

    # Skip auth for non-protected routes
    if not any(path.startswith(p) for p in PROTECTED_PATHS):
        return await call_next(request)

    auth_header = request.headers.get("Authorization")

    # Check header exist
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Missing or invalid Authorization header"},
        )

    # Extract token part
    token = auth_header.split(" ")[1]

    # ----------------------------------------------------------
    # 1. BACKEND TOKEN BYPASS (Django -> FastAPI internal calls)
    # ----------------------------------------------------------
    if token == BACKEND_TOKEN:
        request.state.user = "django-backend"
        return await call_next(request)

    # ----------------------------------------------------------
    # 2. NORMAL JWT VALIDATION
    # ----------------------------------------------------------
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        request.state.user = payload.get("sub")

        if request.state.user is None:
            raise JWTError("User not found in token")

    except JWTError:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid or expired token"},
        )

    return await call_next(request)
