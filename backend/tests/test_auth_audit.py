import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.schemas.auth import UserRole
from app.services.auth_service import (
    authenticate_user,
    create_token,
    hash_password,
    seed_default_users,
    verify_password,
    verify_token,
)


def test_password_hashing_and_verification():
    """Verify PBKDF2 password hashing and verification logic."""
    raw_pwd = "SecureTestPassword123!"
    pwd_hash = hash_password(raw_pwd)

    assert pwd_hash != raw_pwd
    assert ":" in pwd_hash  # Contains salt:hash format
    assert verify_password(raw_pwd, pwd_hash) is True
    assert verify_password("WrongPassword!", pwd_hash) is False


def test_default_users_seeding_and_auth():
    """Verify default seed users are properly populated and authenticated."""
    seed_default_users()

    admin_user = authenticate_user("admin@fraudfusion.io", "AdminPass123!")
    assert admin_user is not None
    assert admin_user.role == UserRole.ADMIN

    analyst_user = authenticate_user("analyst@fraudfusion.io", "AnalystPass123!")
    assert analyst_user is not None
    assert analyst_user.role == UserRole.ANALYST

    viewer_user = authenticate_user("viewer@fraudfusion.io", "ViewerPass123!")
    assert viewer_user is not None
    assert viewer_user.role == UserRole.VIEWER

    invalid = authenticate_user("admin@fraudfusion.io", "WrongPassword!")
    assert invalid is None


def test_token_signing_and_verification():
    """Verify signed token creation and verification."""
    seed_default_users()
    admin_user = authenticate_user("admin@fraudfusion.io", "AdminPass123!")
    assert admin_user is not None

    token = create_token(admin_user)
    assert isinstance(token, str)
    assert "." in token

    decoded_user = verify_token(token)
    assert decoded_user is not None
    assert decoded_user.email == "admin@fraudfusion.io"
    assert decoded_user.role == UserRole.ADMIN

    # Invalid token test
    assert verify_token("invalid.token.str") is None


@pytest.mark.asyncio
async def test_auth_login_api_endpoint():
    """Test POST /api/v1/auth/login endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Success login
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "analyst@fraudfusion.io", "password": "AnalystPass123!"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["user"]["email"] == "analyst@fraudfusion.io"
        assert data["user"]["role"] == "Analyst"

        token = data["access_token"]
        # GET /me endpoint
        me_resp = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert me_resp.status_code == 200
        assert me_resp.json()["email"] == "analyst@fraudfusion.io"

        # Failed login
        fail_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "analyst@fraudfusion.io", "password": "WrongPassword!"},
        )
        assert fail_resp.status_code == 401


@pytest.mark.asyncio
async def test_rbac_role_authorization_and_viewer_restrictions():
    """Verify RBAC role permissions: Viewer cannot access Admin endpoints, Admin can."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Login Viewer
        v_login = await client.post(
            "/api/v1/auth/login",
            json={"email": "viewer@fraudfusion.io", "password": "ViewerPass123!"},
        )
        v_token = v_login.json()["access_token"]

        # Viewer tries to view audit logs -> 403 Forbidden
        v_audit = await client.get(
            "/api/v1/audit/logs", headers={"Authorization": f"Bearer {v_token}"}
        )
        assert v_audit.status_code == 403

        # Viewer tries to create user -> 403 Forbidden
        v_create = await client.post(
            "/api/v1/users",
            json={
                "email": "hacker@test.com",
                "full_name": "Hacker",
                "role": "Admin",
                "password": "Pwd123!",
            },
            headers={"Authorization": f"Bearer {v_token}"},
        )
        assert v_create.status_code == 403

        # Login Admin
        a_login = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@fraudfusion.io", "password": "AdminPass123!"},
        )
        a_token = a_login.json()["access_token"]

        # Admin views audit logs -> 200 OK
        a_audit = await client.get(
            "/api/v1/audit/logs", headers={"Authorization": f"Bearer {a_token}"}
        )
        assert a_audit.status_code == 200
        audit_data = a_audit.json()
        assert "logs" in audit_data
        assert audit_data["total_count"] >= 1

        # Admin lists users -> 200 OK
        a_users = await client.get(
            "/api/v1/users", headers={"Authorization": f"Bearer {a_token}"}
        )
        assert a_users.status_code == 200
        assert len(a_users.json()) >= 3


@pytest.mark.asyncio
async def test_audit_trail_creation_on_report_and_export():
    """Verify that report generation and download actions create audit log records."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Login Analyst
        an_login = await client.post(
            "/api/v1/auth/login",
            json={"email": "analyst@fraudfusion.io", "password": "AnalystPass123!"},
        )
        an_token = an_login.json()["access_token"]
        headers = {"Authorization": f"Bearer {an_token}"}

        # Analyst evaluates risk and generates report
        payload = {
            "transaction": {
                "transaction_id": "TX-AUDIT-TEST-001",
                "account_id": "ACC-SENDER",
                "recipient_id": "ACC-RECV",
                "amount": 4000.0,
                "currency": "USD",
            },
            "custom_metrics": {
                "device_fingerprint_changed": True,
                "distance_km": 2000.0,
                "local_listing": "blacklist",
            },
        }

        gen_resp = await client.post("/api/v1/reports/generate", json=payload, headers=headers)
        assert gen_resp.status_code == 200

        # Download report format CSV
        dl_resp = await client.get(
            "/api/v1/reports/TX-AUDIT-TEST-001/download?format=csv", headers=headers
        )
        assert dl_resp.status_code == 200

        # Admin verifies audit logs contain GENERATE_REPORT and EXPORT_REPORT events
        ad_login = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@fraudfusion.io", "password": "AdminPass123!"},
        )
        ad_token = ad_login.json()["access_token"]

        audit_resp = await client.get(
            "/api/v1/audit/logs?transaction_id=TX-AUDIT-TEST-001",
            headers={"Authorization": f"Bearer {ad_token}"},
        )
        assert audit_resp.status_code == 200
        logs = audit_resp.json()["logs"]
        actions = [log["action"] for log in logs]
        assert "GENERATE_REPORT" in actions
        assert "EXPORT_REPORT" in actions
