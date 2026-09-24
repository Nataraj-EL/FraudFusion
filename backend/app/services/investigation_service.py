import json
import sqlite3
from typing import Any

from app.core.database import get_db_connection
from app.schemas.investigation import (
    DashboardSummary,
    FundFlowEdge,
    FundFlowNode,
    FundFlowVisualizationData,
    InvestigationDetail,
    TransactionListResponse,
    TransactionSummaryItem,
)
from app.services.persistence import (
    get_normalized_transaction,
    get_risk_report_from_db,
    save_risk_report,
)
from app.services.report_service import generate_risk_report
from app.services.risk_engine import evaluate_risk_score


def get_dashboard_summary(
    conn: sqlite3.Connection | None = None, user_role: str = "Viewer"
) -> DashboardSummary:
    """Retrieves real summary statistics, risk distribution, pending items, and audit logs."""
    own_conn = False
    if conn is None:
        conn = get_db_connection()
        own_conn = True

    try:
        # Total transactions
        cursor = conn.execute("SELECT COUNT(*) as count FROM normalized_transactions")
        total_tx = cursor.fetchone()["count"]

        # Risk band distribution
        counts_cursor = conn.execute(
            """
            SELECT COALESCE(rr.risk_band, 'Unassessed') as band, COUNT(*) as count
            FROM normalized_transactions nt
            LEFT JOIN risk_reports rr ON nt.transaction_id = rr.transaction_id
            GROUP BY band
            """
        )
        band_counts = {
            "Very Low": 0,
            "Low": 0,
            "Medium": 0,
            "High": 0,
            "Critical": 0,
            "Unassessed": 0,
        }
        for r in counts_cursor.fetchall():
            band = r["band"]
            band_counts[band] = r["count"]

        # Recent high risk transactions (High/Critical)
        high_risk_cursor = conn.execute(
            """
            SELECT nt.transaction_id, nt.source_type, nt.account_id, nt.recipient_id,
                   nt.amount, nt.currency, nt.channel, nt.payment_method, nt.timestamp,
                   rr.consolidated_score, COALESCE(rr.risk_band, 'Unassessed') as risk_band,
                   rr.recommended_action, COALESCE(rr.str_status, 'NOT_REQUIRED') as str_status,
                   CASE WHEN rr.report_id IS NOT NULL THEN 'REPORT_GENERATED'
                        ELSE 'UNASSESSED' END as report_status
            FROM normalized_transactions nt
            JOIN risk_reports rr ON nt.transaction_id = rr.transaction_id
            WHERE rr.risk_band IN ('High', 'Critical')
            ORDER BY nt.timestamp DESC
            LIMIT 10
            """
        )
        recent_high_risk = [
            TransactionSummaryItem(
                transaction_id=r["transaction_id"],
                source_type=r["source_type"],
                account_id=r["account_id"],
                recipient_id=r["recipient_id"],
                amount=r["amount"],
                currency=r["currency"],
                channel=r["channel"],
                payment_method=r["payment_method"],
                timestamp=r["timestamp"],
                consolidated_score=r["consolidated_score"],
                risk_band=r["risk_band"],
                recommended_action=r["recommended_action"],
                str_status=r["str_status"],
                report_status=r["report_status"],
            )
            for r in high_risk_cursor.fetchall()
        ]

        # Pending investigations (High/Critical or unassessed high-value transactions)
        pending_cursor = conn.execute(
            """
            SELECT nt.transaction_id, nt.source_type, nt.account_id, nt.recipient_id,
                   nt.amount, nt.currency, nt.channel, nt.payment_method, nt.timestamp,
                   rr.consolidated_score, COALESCE(rr.risk_band, 'Unassessed') as risk_band,
                   rr.recommended_action, COALESCE(rr.str_status, 'NOT_REQUIRED') as str_status,
                   CASE WHEN rr.report_id IS NOT NULL THEN 'REPORT_GENERATED'
                        ELSE 'UNASSESSED' END as report_status
            FROM normalized_transactions nt
            LEFT JOIN risk_reports rr ON nt.transaction_id = rr.transaction_id
            WHERE rr.risk_band IN ('High', 'Critical') OR rr.risk_band IS NULL
            ORDER BY nt.timestamp DESC
            LIMIT 10
            """
        )
        pending_investigations = [
            TransactionSummaryItem(
                transaction_id=r["transaction_id"],
                source_type=r["source_type"],
                account_id=r["account_id"],
                recipient_id=r["recipient_id"],
                amount=r["amount"],
                currency=r["currency"],
                channel=r["channel"],
                payment_method=r["payment_method"],
                timestamp=r["timestamp"],
                consolidated_score=r["consolidated_score"],
                risk_band=r["risk_band"],
                recommended_action=r["recommended_action"],
                str_status=r["str_status"],
                report_status=r["report_status"],
            )
            for r in pending_cursor.fetchall()
        ]

        # Audit activity (only for Analyst or Admin)
        recent_audit_logs: list[dict[str, Any]] = []
        if user_role in ("Analyst", "Admin"):
            audit_cursor = conn.execute(
                """
                SELECT id, timestamp, user_email, user_role, action, resource_type,
                       transaction_id, status, metadata_json
                FROM audit_logs
                ORDER BY timestamp DESC
                LIMIT 8
                """
            )
            for r in audit_cursor.fetchall():
                recent_audit_logs.append(
                    {
                        "id": r["id"],
                        "timestamp": r["timestamp"],
                        "user_email": r["user_email"],
                        "user_role": r["user_role"],
                        "action": r["action"],
                        "resource_type": r["resource_type"],
                        "transaction_id": r["transaction_id"],
                        "status": r["status"],
                        "metadata": json.loads(r["metadata_json"]),
                    }
                )

        return DashboardSummary(
            total_transactions=total_tx,
            risk_band_counts=band_counts,
            recent_high_risk=recent_high_risk,
            pending_investigations=pending_investigations,
            recent_audit_logs=recent_audit_logs,
        )
    finally:
        if own_conn:
            conn.close()


def list_transactions(
    search: str | None = None,
    risk_band: str | None = None,
    account_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
    conn: sqlite3.Connection | None = None,
) -> TransactionListResponse:
    """Searches and filters persisted transactions with pagination."""
    own_conn = False
    if conn is None:
        conn = get_db_connection()
        own_conn = True

    try:
        where_clauses: list[str] = []
        params: list[Any] = []

        if search:
            s_pat = f"%{search.strip()}%"
            where_clauses.append(
                "(nt.transaction_id LIKE ? OR nt.account_id LIKE ? OR nt.recipient_id LIKE ?)"
            )
            params.extend([s_pat, s_pat, s_pat])

        if risk_band:
            rb_clean = risk_band.strip()
            if rb_clean.lower() == "unassessed":
                where_clauses.append("rr.risk_band IS NULL")
            else:
                where_clauses.append("rr.risk_band = ?")
                params.append(rb_clean)

        if account_id:
            ac_pat = f"%{account_id.strip()}%"
            where_clauses.append("(nt.account_id LIKE ? OR nt.recipient_id LIKE ?)")
            params.extend([ac_pat, ac_pat])

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        # Count total matching
        count_sql = f"""
            SELECT COUNT(*) as count
            FROM normalized_transactions nt
            LEFT JOIN risk_reports rr ON nt.transaction_id = rr.transaction_id
            {where_sql}
        """
        cursor = conn.execute(count_sql, params)
        total_count = cursor.fetchone()["count"]

        # Fetch page items
        query_sql = f"""
            SELECT nt.transaction_id, nt.source_type, nt.account_id, nt.recipient_id,
                   nt.amount, nt.currency, nt.channel, nt.payment_method, nt.timestamp,
                   rr.consolidated_score, COALESCE(rr.risk_band, 'Unassessed') as risk_band,
                   rr.recommended_action, COALESCE(rr.str_status, 'NOT_REQUIRED') as str_status,
                   CASE WHEN rr.report_id IS NOT NULL THEN 'REPORT_GENERATED'
                        ELSE 'UNASSESSED' END as report_status
            FROM normalized_transactions nt
            LEFT JOIN risk_reports rr ON nt.transaction_id = rr.transaction_id
            {where_sql}
            ORDER BY nt.timestamp DESC
            LIMIT ? OFFSET ?
        """
        page_params = params + [limit, offset]
        rows_cursor = conn.execute(query_sql, page_params)
        items = [
            TransactionSummaryItem(
                transaction_id=r["transaction_id"],
                source_type=r["source_type"],
                account_id=r["account_id"],
                recipient_id=r["recipient_id"],
                amount=r["amount"],
                currency=r["currency"],
                channel=r["channel"],
                payment_method=r["payment_method"],
                timestamp=r["timestamp"],
                consolidated_score=r["consolidated_score"],
                risk_band=r["risk_band"],
                recommended_action=r["recommended_action"],
                str_status=r["str_status"],
                report_status=r["report_status"],
            )
            for r in rows_cursor.fetchall()
        ]

        return TransactionListResponse(total=total_count, items=items)
    finally:
        if own_conn:
            conn.close()


def get_fund_flow_visualization(
    transaction_id: str, conn: sqlite3.Connection | None = None
) -> FundFlowVisualizationData | None:
    """Generates structured fund-flow node/edge network topology for a transaction."""
    own_conn = False
    if conn is None:
        conn = get_db_connection()
        own_conn = True

    try:
        tx = get_normalized_transaction(transaction_id, conn)
        if not tx:
            return None

        # Extract fund flow metrics from source metadata
        ff_metrics = tx.source_metadata.get("ff_metrics", {})
        in_degree = float(ff_metrics.get("in_degree", 1.0))
        out_degree = float(ff_metrics.get("out_degree", 1.0))
        retained_bal = float(
            ff_metrics.get("retained_balance", ff_metrics.get("balance_after", 0.0))
        )
        total_sent = float(ff_metrics.get("total_sent", tx.amount))
        holding_mins = float(ff_metrics.get("holding_minutes", 60.0))

        # Check suspicious conditions
        short_holding = holding_mins < 60.0
        near_zero_balance = total_sent > 0 and (retained_bal / max(1.0, total_sent)) < 0.1
        min_deg = min(in_degree, out_degree)
        max_deg = max(in_degree, out_degree)
        balanced_flow = min_deg > 0 and (min_deg / max_deg) >= 0.8

        nodes: list[FundFlowNode] = [
            FundFlowNode(
                id=tx.account_id,
                label=f"Origin ({tx.account_id})",
                role="sender",
                risk_level="normal",
            )
        ]

        # Intermediate nodes if pass-through or multi-hop detected
        intermediate_id = f"HOP-{tx.transaction_id[:8]}"
        has_intermediate = balanced_flow or short_holding or in_degree > 1 or out_degree > 1
        if has_intermediate:
            relay_risk = "critical" if (short_holding and near_zero_balance) else "suspicious"
            nodes.append(
                FundFlowNode(
                    id=intermediate_id,
                    label=f"Relay Node ({intermediate_id})",
                    role="intermediate",
                    risk_level=relay_risk,
                )
            )

        rec_risk = (
            "critical" if near_zero_balance else "suspicious" if balanced_flow else "normal"
        )
        nodes.append(
            FundFlowNode(
                id=tx.recipient_id,
                label=f"Beneficiary ({tx.recipient_id})",
                role="recipient",
                risk_level=rec_risk,
            )
        )

        edges: list[FundFlowEdge] = []
        if has_intermediate:
            edges.append(
                FundFlowEdge(
                    source=tx.account_id,
                    target=intermediate_id,
                    amount=tx.amount,
                    currency=tx.currency,
                    holding_minutes=holding_mins,
                    flow_type="INBOUND_RELAY",
                    is_suspicious=short_holding,
                )
            )
            edges.append(
                FundFlowEdge(
                    source=intermediate_id,
                    target=tx.recipient_id,
                    amount=total_sent,
                    currency=tx.currency,
                    holding_minutes=holding_mins,
                    flow_type="RAPID_DRAIN" if near_zero_balance else "OUTBOUND_TRANSFER",
                    is_suspicious=near_zero_balance or balanced_flow,
                )
            )
        else:
            edges.append(
                FundFlowEdge(
                    source=tx.account_id,
                    target=tx.recipient_id,
                    amount=tx.amount,
                    currency=tx.currency,
                    holding_minutes=holding_mins,
                    flow_type="DIRECT_TRANSFER",
                    is_suspicious=short_holding or near_zero_balance,
                )
            )

        explanation = (
            f"Fund Flow topology for TX '{tx.transaction_id}': "
            f"Transfer of {tx.amount:.2f} {tx.currency} from {tx.account_id} to {tx.recipient_id}. "
            f"Metrics: In-Degree={in_degree:.0f}, Out-Degree={out_degree:.0f}, "
            f"Retained Balance={retained_bal:.2f} {tx.currency}, Dwell={holding_mins:.1f}m."
        )

        metrics = {
            "in_degree": in_degree,
            "out_degree": out_degree,
            "retained_balance": retained_bal,
            "total_sent": total_sent,
            "holding_minutes": holding_mins,
            "short_holding_flag": short_holding,
            "near_zero_balance_flag": near_zero_balance,
            "balanced_flow_flag": balanced_flow,
        }

        return FundFlowVisualizationData(
            transaction_id=tx.transaction_id,
            nodes=nodes,
            edges=edges,
            metrics=metrics,
            explanation=explanation,
        )
    finally:
        if own_conn:
            conn.close()


def get_transaction_investigation_detail(
    transaction_id: str, conn: sqlite3.Connection | None = None
) -> InvestigationDetail | None:
    """Retrieves investigation detail including transaction, report, and audit history."""

    own_conn = False
    if conn is None:
        conn = get_db_connection()
        own_conn = True

    try:
        tx = get_normalized_transaction(transaction_id, conn)
        if not tx:
            return None

        # Fetch risk report (or generate & persist if unassessed)
        report = get_risk_report_from_db(transaction_id, conn)
        if not report:
            assessment = evaluate_risk_score(transaction=tx)
            report = generate_risk_report(assessment=assessment, transaction=tx)
            save_risk_report(report, conn)

        # Fund flow topology
        ff_data = get_fund_flow_visualization(transaction_id, conn)

        # Fetch audit history for this transaction
        audit_cursor = conn.execute(
            """
            SELECT id, timestamp, user_email, user_role, action, resource_type,
                   transaction_id, status, metadata_json
            FROM audit_logs
            WHERE transaction_id = ?
            ORDER BY timestamp DESC
            """,
            (transaction_id,),
        )
        audit_history: list[dict[str, Any]] = []
        for r in audit_cursor.fetchall():
            audit_history.append(
                {
                    "id": r["id"],
                    "timestamp": r["timestamp"],
                    "user_email": r["user_email"],
                    "user_role": r["user_role"],
                    "action": r["action"],
                    "resource_type": r["resource_type"],
                    "transaction_id": r["transaction_id"],
                    "status": r["status"],
                    "metadata": json.loads(r["metadata_json"]),
                }
            )

        return InvestigationDetail(
            transaction=tx,
            risk_report=report,
            fund_flow=ff_data,
            audit_history=audit_history,
        )
    finally:
        if own_conn:
            conn.close()
