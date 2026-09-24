from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field

from app.api.deps import get_optional_user
from app.schemas.auth import UserResponse
from app.schemas.report import RiskReport
from app.schemas.transaction import Transaction
from app.services.audit_service import log_audit_event
from app.services.persistence import (
    get_normalized_transaction,
    get_risk_report_from_db,
    save_risk_report,
)
from app.services.report_service import (
    export_report_to_csv,
    export_report_to_html,
    export_report_to_json,
    generate_risk_report,
)
from app.services.risk_engine import evaluate_risk_score

router = APIRouter()


class GenerateReportRequest(BaseModel):
    transaction: Transaction = Field(..., description="Transaction data to evaluate and report")
    custom_metrics: dict[str, Any] = Field(
        default_factory=dict, description="Optional ad-hoc metrics"
    )


def _get_or_generate_report(transaction_id: str) -> RiskReport:
    """Helper to fetch stored report or generate on the fly from stored canonical transaction."""
    stored_report = get_risk_report_from_db(transaction_id)
    if stored_report:
        return stored_report

    norm_tx = get_normalized_transaction(transaction_id)
    if norm_tx:
        assessment = evaluate_risk_score(norm_tx)
        report = generate_risk_report(assessment, norm_tx)
        save_risk_report(report)
        return report

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Report or transaction '{transaction_id}' not found",
    )


@router.post(
    "/reports/generate",
    response_model=RiskReport,
    status_code=status.HTTP_200_OK,
    summary="Evaluate transaction and generate full RiskReport & STR draft",
)
async def generate_report_endpoint(
    payload: GenerateReportRequest,
    current_user: UserResponse = Depends(get_optional_user),
) -> RiskReport:
    """
    Evaluates transaction risk score, generates human-readable report,
    creates STR draft if High or Critical risk, and persists to SQLite.
    """
    assessment = evaluate_risk_score(
        transaction=payload.transaction, custom_metrics=payload.custom_metrics
    )
    report = generate_risk_report(assessment, payload.transaction)
    save_risk_report(report)

    log_audit_event(
        user_email=current_user.email,
        user_role=current_user.role.value,
        action="GENERATE_REPORT",
        resource_type="REPORT",
        transaction_id=report.transaction_id,
        status="SUCCESS",
        metadata={"str_status": report.str_status, "risk_band": report.risk_band},
    )

    if report.str_draft:
        log_audit_event(
            user_email=current_user.email,
            user_role=current_user.role.value,
            action="GENERATE_STR",
            resource_type="STR_DRAFT",
            transaction_id=report.transaction_id,
            status="SUCCESS",
            metadata={"str_id": report.str_draft.str_id},
        )

    return report


@router.get(
    "/reports/{transaction_id}",
    response_model=RiskReport,
    status_code=status.HTTP_200_OK,
    summary="Get RiskReport JSON for a transaction",
)
async def get_report_endpoint(
    transaction_id: str,
    current_user: UserResponse = Depends(get_optional_user),
) -> RiskReport:
    """Retrieves full RiskReport by transaction_id."""
    report = _get_or_generate_report(transaction_id)
    log_audit_event(
        user_email=current_user.email,
        user_role=current_user.role.value,
        action="VIEW_REPORT",
        resource_type="REPORT",
        transaction_id=transaction_id,
        status="SUCCESS",
    )
    return report


@router.get(
    "/reports/{transaction_id}/download",
    status_code=status.HTTP_200_OK,
    summary="Download RiskReport in JSON, CSV, HTML, or PDF format",
)
async def download_report_endpoint(
    transaction_id: str,
    format: str = Query("html", pattern="^(json|csv|html|pdf)$"),
    current_user: UserResponse = Depends(get_optional_user),
) -> Response:
    """Downloads report formatted as JSON, CSV, or standalone HTML/PDF document."""
    report = _get_or_generate_report(transaction_id)
    fmt = format.lower()

    log_audit_event(
        user_email=current_user.email,
        user_role=current_user.role.value,
        action="EXPORT_REPORT",
        resource_type="REPORT",
        transaction_id=transaction_id,
        status="SUCCESS",
        metadata={"format": fmt},
    )

    if fmt == "json":
        return Response(
            content=export_report_to_json(report),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=report_{transaction_id}.json"},
        )
    elif fmt == "csv":
        return Response(
            content=export_report_to_csv(report),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=summary_{transaction_id}.csv"},
        )
    else:  # html or pdf
        ext = "pdf" if fmt == "pdf" else "html"
        return Response(
            content=export_report_to_html(report),
            media_type="text/html",
            headers={"Content-Disposition": f"inline; filename=report_{transaction_id}.{ext}"},
        )


@router.get(
    "/export/{transaction_id}",
    status_code=status.HTTP_200_OK,
    summary="Export risk summary in specified format",
)
async def export_report_endpoint(
    transaction_id: str,
    format: str = Query("json", pattern="^(json|csv|html|pdf)$"),
    current_user: UserResponse = Depends(get_optional_user),
) -> Response:
    """Exports risk report formatted as JSON, CSV, or HTML string."""
    return await download_report_endpoint(
        transaction_id=transaction_id, format=format, current_user=current_user
    )
