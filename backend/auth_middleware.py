"""
Middleware de autenticación para el backend principal
"""
import httpx
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

class AuthenticationMiddleware:
    def __init__(self, auth_service_url: str = "http://auth-service:8001"):
        self.auth_service_url = auth_service_url
        self.security = HTTPBearer()

    async def verify_token(self, token: str) -> dict:
        """Verificar token con el servicio de autenticación"""
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {token}"}
            try:
                response = await client.post(
                    f"{self.auth_service_url}/api/v1/auth/verify-token",
                    headers=headers,
                    timeout=5.0
                )
                if response.status_code == 200:
                    return response.json()
                else:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Token inválido"
                    )
            except httpx.RequestError:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Servicio de autenticación no disponible"
                )

    async def get_current_user(self, credentials: HTTPAuthorizationCredentials) -> dict:
        """Obtener usuario actual desde el token"""
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token requerido"
            )
        
        return await self.verify_token(credentials.credentials)

# Instancia global del middleware
auth_middleware = AuthenticationMiddleware()