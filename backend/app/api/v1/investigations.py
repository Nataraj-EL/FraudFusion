from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_current_user
from app.schemas.auth import UserResponse
from app.schemas.investigation import (
    DashboardSummary,
    FundFlowVisualizationData,
    InvestigationDetail,
    TransactionListResponse,
)
from app.services.audit_service import log_audit_event
from app.services.investigation_service import (
    get_dashboard_summary,
    get_fund_flow_visualization,
    get_transaction_investigation_detail,
    list_transactions,
)

router = APIRouter()


@router.get(
    "/summary",
    response_model=DashboardSummary,
    status_code=status.HTTP_200_OK,
    summary="Get analyst dashboard summary statistics",
)
async def get_dashboard(
    current_user: UserResponse = Depends(get_current_user),
) -> DashboardSummary:
    """Returns real summary metrics, risk breakdown, high risk items, and audit activity."""
    summary = get_dashboard_summary(user_role=current_user.role.value)
    log_audit_event(
        user_email=current_user.email,
        user_role=current_user.role.value,
        action="VIEW_DASHBOARD",
        resource_type="INVESTIGATION",
        status="SUCCESS",
        metadata={"total_transactions": summary.total_transactions},
    )
    return summary


@router.get(
    "/transactions",
    response_model=TransactionListResponse,
    status_code=status.HTTP_200_OK,
    summary="List and filter transactions with risk assessment state",
)
async def search_transactions(
    search: str | None = Query(None, description="Search ID/account/recipient"),
    risk_band: str | None = Query(None, description="Filter by risk band"),
    account_id: str | None = Query(None, description="Filter by account ID"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: UserResponse = Depends(get_current_user),
) -> TransactionListResponse:
    """Searches and filters normalized transactions along with stored risk assessments."""
    res = list_transactions(
        search=search,
        risk_band=risk_band,
        account_id=account_id,
        limit=limit,
        offset=offset,
    )
    log_audit_event(
        user_email=current_user.email,
        user_role=current_user.role.value,
        action="SEARCH_TRANSACTIONS",
        resource_type="TRANSACTION",
        status="SUCCESS",
        metadata={
            "search": search,
            "risk_band": risk_band,
            "account_id": account_id,
            "count": len(res.items),
            "total": res.total,
        },
    )
    return res


@router.get(
    "/transactions/{transaction_id}",
    response_model=InvestigationDetail,
    status_code=status.HTTP_200_OK,
    summary="Get complete investigation detail for a single transaction",
)
async def get_investigation_detail(
    transaction_id: str,
    current_user: UserResponse = Depends(get_current_user),
) -> InvestigationDetail:
    """Returns transaction details, subscores, factors, topology, and audit history."""
    detail = get_transaction_investigation_detail(transaction_id)
    if not detail:
        log_audit_event(
            user_email=current_user.email,
            user_role=current_user.role.value,
            action="VIEW_INVESTIGATION",
            resource_type="TRANSACTION",
            transaction_id=transaction_id,
            status="FAILURE",
            metadata={"reason": "Transaction not found"},
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction '{transaction_id}' not found",
        )

    score_val = detail.risk_report.consolidated_score if detail.risk_report else None
    band_val = detail.risk_report.risk_band if detail.risk_report else None
    log_audit_event(
        user_email=current_user.email,
        user_role=current_user.role.value,
        action="VIEW_INVESTIGATION",
        resource_type="TRANSACTION",
        transaction_id=transaction_id,
        status="SUCCESS",
        metadata={"consolidated_score": score_val, "risk_band": band_val},
    )
    return detail


@router.get(
    "/transactions/{transaction_id}/fund-flow",
    response_model=FundFlowVisualizationData,
    status_code=status.HTTP_200_OK,
    summary="Get fund flow node and edge network topology for visualization",
)
async def get_fund_flow_topology(
    transaction_id: str,
    current_user: UserResponse = Depends(get_current_user),
) -> FundFlowVisualizationData:
    """Returns nodes, edges, flow direction, and risk indicators for fund-flow visualization."""
    topology = get_fund_flow_visualization(transaction_id)
    if not topology:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fund flow topology for transaction '{transaction_id}' not found",
        )

    log_audit_event(
        user_email=current_user.email,
        user_role=current_user.role.value,
        action="VIEW_FUND_FLOW",
        resource_type="FUND_FLOW",
        transaction_id=transaction_id,
        status="SUCCESS",
        metadata={"nodes_count": len(topology.nodes), "edges_count": len(topology.edges)},
    )
    return topology
