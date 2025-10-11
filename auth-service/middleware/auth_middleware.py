from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from services.jwt_service import JWTService
import httpx

class AuthMiddleware:
    def __init__(self):
        self.jwt_service = JWTService()
        self.security = HTTPBearer()

    async def verify_token(self, credentials: HTTPAuthorizationCredentials):
        """Verificar token JWT"""
        try:
            payload = self.jwt_service.verify_token(credentials.credentials)
            return payload
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
                headers={"WWW-Authenticate": "Bearer"},
            )

    async def get_current_user_from_backend(self, token: str):
        """Obtener datos del usuario desde el backend principal"""
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {token}"}
            response = await client.get(
                "http://backend:8000/api/v1/users/me",  # URL del backend
                headers=headers
            )
            if response.status_code == 200:
                return response.json()
            return None