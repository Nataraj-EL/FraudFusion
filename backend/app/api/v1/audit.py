from fastapi import APIRouter, Depends, Query, status

from app.api.deps import require_roles
from app.schemas.audit import AuditLogQueryResponse
from app.schemas.auth import UserResponse, UserRole
from app.services.audit_service import get_audit_logs, log_audit_event

router = APIRouter()


@router.get(
    "/audit/logs",
    response_model=AuditLogQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve audit trail log records (Admin only)",
)
async def get_audit_logs_endpoint(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    user_email: str | None = None,
    action: str | None = None,
    transaction_id: str | None = None,
    admin_user: UserResponse = Depends(require_roles([UserRole.ADMIN])),
) -> AuditLogQueryResponse:
    """Retrieves paginated audit log entries for system administrators."""
    log_audit_event(
        user_email=admin_user.email,
        user_role=admin_user.role.value,
        action="VIEW_AUDIT_LOGS",
        resource_type="AUDIT",
        status="SUCCESS",
        metadata={"limit": limit, "offset": offset, "filter_user": user_email},
    )
    return get_audit_logs(
        limit=limit,
        offset=offset,
        user_email=user_email,
        action=action,
        transaction_id=transaction_id,
    )
