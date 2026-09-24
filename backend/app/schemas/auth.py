from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, Field


class UserRole(str, Enum):
    VIEWER = "Viewer"
    ANALYST = "Analyst"
    ADMIN = "Admin"


class LoginRequest(BaseModel):
    email: str = Field(..., description="User login email address")
    password: str = Field(..., description="User account password")


class UserResponse(BaseModel):
    user_id: str = Field(..., description="Unique user identifier e.g. USR-001")
    email: str = Field(..., description="User email address")
    full_name: str = Field(..., description="User full display name")
    role: UserRole = Field(..., description="User RBAC role: Viewer, Analyst, or Admin")
    created_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="Account creation timestamp",
    )


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="Signed authentication token")
    token_type: str = Field(default="bearer", description="Token category")
    user: UserResponse = Field(..., description="Authenticated user profile details")


class UserCreateRequest(BaseModel):
    email: str = Field(..., description="New user email address")
    full_name: str = Field(..., description="New user full name")
    role: UserRole = Field(..., description="Assigned RBAC role")
    password: str = Field(..., description="Initial account password")
