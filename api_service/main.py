from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth import router as auth_router
from mssql_routes import router as mssql_router
from middleware import jwt_middleware

app = FastAPI(title="Policy KYC API")

# -----------------------------
# CORS CONFIG
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace later for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# JWT Middleware
# -----------------------------
app.middleware("http")(jwt_middleware)

# -----------------------------
# Root endpoint
# -----------------------------
@app.get("/")
def root():
    return {"message": "API is running"}

# -----------------------------
# Routers
# -----------------------------
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(mssql_router, prefix="/mssql", tags=["MSSQL"])


# -----------------------------
# Custom OpenAPI (Swagger)
# -----------------------------
from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Policy KYC API",
        version="1.0.0",
        description="API for KYC and MSSQL integration",
        routes=app.routes,
    )

    # Security Scheme
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }

    # APPLY SECURITY GLOBALLY (IMPORTANT FOR SWAGGER)
    openapi_schema["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
