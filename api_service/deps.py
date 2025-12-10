from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

bearer_scheme = HTTPBearer()

# Extract token (no OAuth2PasswordBearer)
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    token = credentials.credentials
    return {"token": token}

# Example protected route
@router.get("/protected")
def protected_route(request: Request, user=Depends(get_current_user)):
    current_user = getattr(request.state, "user", None)

    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    return {
        "message": f"Hello, {current_user['username']}! This is protected.",
        "user": current_user
    }
