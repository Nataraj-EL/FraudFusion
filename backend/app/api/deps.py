from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.schemas.auth import UserResponse, UserRole
from app.services.audit_service import log_audit_event
from app.services.auth_service import verify_token

security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> UserResponse:
    """FastAPI dependency enforcing valid Bearer token authentication."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing or invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = verify_token(credentials.credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token expired or invalid signature",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> UserResponse:
    """
    Returns authenticated user if token present, or defaults to default Analyst role
    for backward-compatible development API calls.
    """
    if credentials and credentials.credentials:
        user = verify_token(credentials.credentials)
        if user:
            return user

    # Default fallback user for unauthenticated development calls
    return UserResponse(
        user_id="USR-ANALYST-DEV",
        email="analyst@fraudfusion.io",
        full_name="Lead Fraud Analyst",
        role=UserRole.ANALYST,
    )


def require_roles(allowed_roles: list[UserRole]):
    """FastAPI dependency factory enforcing RBAC role permissions."""

    def dependency(user: UserResponse = Depends(get_current_user)) -> UserResponse:
        if user.role not in allowed_roles:
            log_audit_event(
                user_email=user.email,
                user_role=user.role.value,
                action="UNAUTHORIZED_ACCESS_ATTEMPT",
                resource_type="API",
                status="UNAUTHORIZED",
                metadata={"allowed_roles": [r.value for r in allowed_roles]},
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role.value}' is not authorized to perform this action",
            )
        return user

    return dependency
