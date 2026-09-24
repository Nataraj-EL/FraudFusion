from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user, require_roles
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    UserCreateRequest,
    UserResponse,
    UserRole,
)
from app.services.audit_service import log_audit_event
from app.services.auth_service import (
    authenticate_user,
    create_token,
    create_user_record,
    get_all_users,
)

router = APIRouter()


@router.post(
    "/auth/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user and return signed access token",
)
async def login_endpoint(payload: LoginRequest) -> TokenResponse:
    """Authenticates email and password credentials, returning signed bearer token."""
    user = authenticate_user(payload.email, payload.password)
    if not user:
        log_audit_event(
            user_email=payload.email.strip().lower(),
            user_role="UNKNOWN",
            action="USER_LOGIN",
            resource_type="AUTH",
            status="FAILED",
            metadata={"reason": "Invalid credentials"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_token(user)
    log_audit_event(
        user_email=user.email,
        user_role=user.role.value,
        action="USER_LOGIN",
        resource_type="AUTH",
        status="SUCCESS",
    )

    return TokenResponse(access_token=token, token_type="bearer", user=user)


@router.get(
    "/auth/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user profile",
)
async def get_me_endpoint(user: UserResponse = Depends(get_current_user)) -> UserResponse:
    """Returns profile details for currently authenticated user."""
    return user


@router.get(
    "/users",
    response_model=list[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="List all registered RBAC users (Admin only)",
)
async def list_users_endpoint(
    admin_user: UserResponse = Depends(require_roles([UserRole.ADMIN])),
) -> list[UserResponse]:
    """Retrieves list of all registered RBAC users."""
    log_audit_event(
        user_email=admin_user.email,
        user_role=admin_user.role.value,
        action="LIST_USERS",
        resource_type="USER_MANAGEMENT",
        status="SUCCESS",
    )
    return get_all_users()


@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new RBAC user (Admin only)",
)
async def create_user_endpoint(
    payload: UserCreateRequest,
    admin_user: UserResponse = Depends(require_roles([UserRole.ADMIN])),
) -> UserResponse:
    """Creates a new user account with assigned RBAC role."""
    try:
        new_user = create_user_record(
            email=payload.email,
            full_name=payload.full_name,
            role=payload.role,
            password=payload.password,
        )
        log_audit_event(
            user_email=admin_user.email,
            user_role=admin_user.role.value,
            action="CREATE_USER",
            resource_type="USER_MANAGEMENT",
            status="SUCCESS",
            metadata={"created_user_email": new_user.email, "role": new_user.role.value},
        )
        return new_user
    except Exception as exc:
        log_audit_event(
            user_email=admin_user.email,
            user_role=admin_user.role.value,
            action="CREATE_USER",
            resource_type="USER_MANAGEMENT",
            status="FAILED",
            metadata={"error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create user: {exc}",
        ) from exc
