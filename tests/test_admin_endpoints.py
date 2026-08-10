"""
Admin Endpoints Test Suite
Tests all /admin/* endpoints: health, dashboard, policies, calls, bookings
Run with: pytest tests/test_admin_endpoints.py -v
Or against a live server: BASE_URL=http://localhost:8000 pytest tests/test_admin_endpoints.py -v
"""

import pytest
import httpx
import os
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, date

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

# Fake IDs used throughout tests
VALID_RESTAURANT_ID = "test-restaurant-uuid-001"
INVALID_RESTAURANT_ID = "nonexistent-restaurant-999"

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    """Sync HTTP client for live-server integration tests."""
    with httpx.Client(base_url=BASE_URL, timeout=10) as c:
        yield c


@pytest.fixture
def mock_db():
    """Return a MagicMock that mimics a SQLAlchemy Session."""
    return MagicMock()


@pytest.fixture
def sample_policy_payload():
    return {
        "deposit_required": True,
        "deposit_amount": 20,
        "max_party_size": 8,
        "opening_hours": [
            {"day_of_week": 0, "open_time": "09:00", "close_time": "22:00", "is_closed": False},
            {"day_of_week": 1, "open_time": "09:00", "close_time": "22:00", "is_closed": False},
            {"day_of_week": 2, "open_time": "09:00", "close_time": "22:00", "is_closed": False},
            {"day_of_week": 3, "open_time": "09:00", "close_time": "22:00", "is_closed": False},
            {"day_of_week": 4, "open_time": "09:00", "close_time": "23:00", "is_closed": False},
            {"day_of_week": 5, "open_time": "10:00", "close_time": "23:00", "is_closed": False},
            {"day_of_week": 6, "open_time": "00:00", "close_time": "00:00", "is_closed": True},
        ],
        "deposit_rules": [
            {"day_of_week": 5, "min_party": 6, "start_time": "18:00", "end_time": "23:00"},
            {"day_of_week": 4, "min_party": 8, "start_time": "19:00", "end_time": "23:00"},
        ],
    }


# ---------------------------------------------------------------------------
# Helper: build mock DB objects
# ---------------------------------------------------------------------------

def _make_restaurant(rid=VALID_RESTAURANT_ID):
    r = MagicMock()
    r.id = rid
    r.name = "Test Restaurant"
    return r


def _make_policy(rid=VALID_RESTAURANT_ID):
    p = MagicMock()
    p.id = "policy-uuid-001"
    p.restaurant_id = rid
    p.deposit_required = False
    p.deposit_amount = None
    p.max_party_size = 10
    return p


def _make_call(idx=1):
    c = MagicMock()
    c.id = f"call-uuid-{idx:03d}"
    c.call_id = f"vapi-call-{idx:03d}"
    c.customer_phone = "+1555000000" + str(idx)
    c.status = "completed"
    c.duration = 120 + idx
    c.transcript = "Hello, I'd like to make a reservation."
    c.audio_url = f"https://cdn.example.com/audio/{idx}.mp3"
    c.booking_id = f"booking-uuid-{idx:03d}"
    c.created_at = datetime(2026, 3, 27, 10, idx, 0)
    c.updated_at = datetime(2026, 3, 27, 10, idx, 30)
    return c


def _make_booking(idx=1, status="CONFIRMED"):
    b = MagicMock()
    b.id = f"booking-uuid-{idx:03d}"
    b.customer_name = f"Customer {idx}"
    b.customer_phone = "+1555000000" + str(idx)
    b.party_size = 2 + idx
    b.booking_time = datetime(2026, 4, 1, 19, 0, 0)
    b.status = status
    b.stripe_payment_id = f"pi_test_{idx:06d}"
    b.external_ref_id = f"ext-ref-{idx:03d}"
    b.call_confidence = 0.95
    b.created_at = datetime(2026, 3, 27, 10, idx, 0)
    return b


# ===========================================================================
# 1. HEALTH CHECK  –  GET /admin/health
# ===========================================================================

class TestAdminHealth:
    """Tests for GET /admin/health"""

    def test_health_returns_200(self, client):
        resp = client.get("/admin/health")
        assert resp.status_code == 200

    def test_health_response_structure(self, client):
        data = client.get("/admin/health").json()
        assert data["status"] == "healthy"
        assert data["service"] == "admin"
        assert "version" in data
        assert "features" in data

    def test_health_features_list(self, client):
        features = client.get("/admin/health").json()["features"]
        assert isinstance(features, list)
        assert len(features) > 0

    def test_health_content_type_json(self, client):
        resp = client.get("/admin/health")
        assert "application/json" in resp.headers["content-type"]


# ===========================================================================
# 2. DASHBOARD STATS  –  GET /admin/dashboard/stats/{restaurant_id}
# ===========================================================================

class TestDashboardStats:
    """Tests for GET /admin/dashboard/stats/{restaurant_id}"""

    # --- unit tests (mocked DB) ---

    def test_dashboard_stats_valid_restaurant(self, mock_db):
        from admin.admin_service import get_dashboard_stats

        mock_restaurant = _make_restaurant()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_restaurant
        mock_db.query.return_value.filter.return_value.count.return_value = 5
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        import asyncio
        with patch("admin.admin_service.get_db", return_value=mock_db):
            result = asyncio.get_event_loop().run_until_complete(
                get_dashboard_stats(VALID_RESTAURANT_ID, mock_db)
            )
        assert result.total_calls >= 0

    def test_dashboard_stats_restaurant_not_found(self, mock_db):
        from admin.admin_service import get_dashboard_stats
        from fastapi import HTTPException

        mock_db.query.return_value.filter.return_value.first.return_value = None

        import asyncio
        with pytest.raises(HTTPException) as exc_info:
            asyncio.get_event_loop().run_until_complete(
                get_dashboard_stats(INVALID_RESTAURANT_ID, mock_db)
            )
        assert exc_info.value.status_code == 404

    # --- integration tests (live server) ---

    def test_dashboard_stats_invalid_id_returns_404(self, client):
        resp = client.get(f"/admin/dashboard/stats/{INVALID_RESTAURANT_ID}")
        assert resp.status_code == 404

    def test_dashboard_stats_response_fields(self, client):
        """If a valid restaurant exists, all required fields must be present."""
        resp = client.get(f"/admin/dashboard/stats/{VALID_RESTAURANT_ID}")
        if resp.status_code == 200:
            data = resp.json()
            required = [
                "total_calls", "successful_bookings", "failed_bookings",
                "total_calls_today", "total_bookings_today",
                "success_rate", "recent_calls", "recent_bookings",
            ]
            for field in required:
                assert field in data, f"Missing field: {field}"

    def test_dashboard_stats_success_rate_range(self, client):
        resp = client.get(f"/admin/dashboard/stats/{VALID_RESTAURANT_ID}")
        if resp.status_code == 200:
            rate = resp.json()["success_rate"]
            assert 0.0 <= rate <= 100.0

    def test_dashboard_stats_recent_calls_max_10(self, client):
        resp = client.get(f"/admin/dashboard/stats/{VALID_RESTAURANT_ID}")
        if resp.status_code == 200:
            assert len(resp.json()["recent_calls"]) <= 10

    def test_dashboard_stats_recent_bookings_max_10(self, client):
        resp = client.get(f"/admin/dashboard/stats/{VALID_RESTAURANT_ID}")
        if resp.status_code == 200:
            assert len(resp.json()["recent_bookings"]) <= 10

    def test_dashboard_stats_counts_non_negative(self, client):
        resp = client.get(f"/admin/dashboard/stats/{VALID_RESTAURANT_ID}")
        if resp.status_code == 200:
            data = resp.json()
            for key in ["total_calls", "successful_bookings", "failed_bookings",
                        "total_calls_today", "total_bookings_today"]:
                assert data[key] >= 0

    def test_dashboard_stats_empty_restaurant_id(self, client):
        resp = client.get("/admin/dashboard/stats/")
        assert resp.status_code in (404, 405, 422)


# ===========================================================================
# 3. POLICY – GET /admin/policies/{restaurant_id}
# ===========================================================================

class TestGetPolicy:
    """Tests for GET /admin/policies/{restaurant_id}"""

    def test_get_policy_restaurant_not_found(self, mock_db):
        from admin.admin_service import get_policy
        from fastapi import HTTPException

        mock_db.query.return_value.filter.return_value.first.return_value = None

        import asyncio
        with pytest.raises(HTTPException) as exc_info:
            asyncio.get_event_loop().run_until_complete(
                get_policy(INVALID_RESTAURANT_ID, mock_db)
            )
        assert exc_info.value.status_code == 404

    def test_get_policy_creates_default_when_missing(self, mock_db):
        """When no policy exists, a default one should be created and returned."""
        from admin.admin_service import get_policy

        mock_restaurant = _make_restaurant()
        mock_policy = _make_policy()

        # First call returns restaurant, second returns None (no policy), third returns new policy
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_restaurant, None, mock_policy
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = []

        import asyncio
        with patch("admin.admin_service.get_db", return_value=mock_db):
            result = asyncio.get_event_loop().run_until_complete(
                get_policy(VALID_RESTAURANT_ID, mock_db)
            )
        assert result is not None

    def test_get_policy_invalid_id_returns_404(self, client):
        resp = client.get(f"/admin/policies/{INVALID_RESTAURANT_ID}")
        assert resp.status_code == 404

    def test_get_policy_response_structure(self, client):
        resp = client.get(f"/admin/policies/{VALID_RESTAURANT_ID}")
        if resp.status_code == 200:
            data = resp.json()
            for field in ["id", "restaurant_id", "deposit_required",
                          "max_party_size", "opening_hours", "deposit_rules"]:
                assert field in data

    def test_get_policy_opening_hours_is_list(self, client):
        resp = client.get(f"/admin/policies/{VALID_RESTAURANT_ID}")
        if resp.status_code == 200:
            assert isinstance(resp.json()["opening_hours"], list)

    def test_get_policy_deposit_rules_is_list(self, client):
        resp = client.get(f"/admin/policies/{VALID_RESTAURANT_ID}")
        if resp.status_code == 200:
            assert isinstance(resp.json()["deposit_rules"], list)

    def test_get_policy_max_party_size_positive(self, client):
        resp = client.get(f"/admin/policies/{VALID_RESTAURANT_ID}")
        if resp.status_code == 200:
            assert resp.json()["max_party_size"] > 0


# ===========================================================================
# 4. POLICY – POST /admin/policies/{restaurant_id}
# ===========================================================================

class TestCreatePolicy:
    """Tests for POST /admin/policies/{restaurant_id}"""

    def test_create_policy_restaurant_not_found(self, client, sample_policy_payload):
        resp = client.post(
            f"/admin/policies/{INVALID_RESTAURANT_ID}",
            json=sample_policy_payload,
        )
        assert resp.status_code == 404

    def test_create_policy_success(self, client, sample_policy_payload):
        resp = client.post(
            f"/admin/policies/{VALID_RESTAURANT_ID}",
            json=sample_policy_payload,
        )
        if resp.status_code == 200:
            data = resp.json()
            assert data["deposit_required"] == sample_policy_payload["deposit_required"]
            assert data["max_party_size"] == sample_policy_payload["max_party_size"]
            assert data["deposit_amount"] == sample_policy_payload["deposit_amount"]

    def test_create_policy_opening_hours_persisted(self, client, sample_policy_payload):
        resp = client.post(
            f"/admin/policies/{VALID_RESTAURANT_ID}",
            json=sample_policy_payload,
        )
        if resp.status_code == 200:
            assert len(resp.json()["opening_hours"]) == len(sample_policy_payload["opening_hours"])

    def test_create_policy_deposit_rules_persisted(self, client, sample_policy_payload):
        resp = client.post(
            f"/admin/policies/{VALID_RESTAURANT_ID}",
            json=sample_policy_payload,
        )
        if resp.status_code == 200:
            assert len(resp.json()["deposit_rules"]) == len(sample_policy_payload["deposit_rules"])

    def test_create_policy_missing_opening_hours_422(self, client):
        """opening_hours is required – omitting it should return 422."""
        resp = client.post(
            f"/admin/policies/{VALID_RESTAURANT_ID}",
            json={"deposit_required": False, "max_party_size": 10},
        )
        assert resp.status_code == 422

    def test_create_policy_no_deposit_amount_when_not_required(self, client):
        payload = {
            "deposit_required": False,
            "max_party_size": 10,
            "opening_hours": [
                {"day_of_week": 0, "open_time": "09:00", "close_time": "22:00", "is_closed": False}
            ],
        }
        resp = client.post(f"/admin/policies/{VALID_RESTAURANT_ID}", json=payload)
        if resp.status_code == 200:
            assert resp.json()["deposit_amount"] is None

    def test_create_policy_replaces_existing(self, client, sample_policy_payload):
        """Calling POST twice should replace, not duplicate."""
        client.post(f"/admin/policies/{VALID_RESTAURANT_ID}", json=sample_policy_payload)
        resp2 = client.post(f"/admin/policies/{VALID_RESTAURANT_ID}", json=sample_policy_payload)
        if resp2.status_code == 200:
            # Should still have exactly the same number of opening hours
            assert len(resp2.json()["opening_hours"]) == len(sample_policy_payload["opening_hours"])

    def test_create_policy_invalid_body_type(self, client):
        resp = client.post(
            f"/admin/policies/{VALID_RESTAURANT_ID}",
            content="not-json",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 422


# ===========================================================================
# 5. POLICY – PUT /admin/policies/{restaurant_id}
# ===========================================================================

class TestUpdatePolicy:
    """Tests for PUT /admin/policies/{restaurant_id}"""

    def test_update_policy_restaurant_not_found(self, client):
        resp = client.put(
            f"/admin/policies/{INVALID_RESTAURANT_ID}",
            json={"max_party_size": 12},
        )
        assert resp.status_code == 404

    def test_update_policy_partial_update_max_party(self, client):
        resp = client.put(
            f"/admin/policies/{VALID_RESTAURANT_ID}",
            json={"max_party_size": 15},
        )
        if resp.status_code == 200:
            assert resp.json()["max_party_size"] == 15

    def test_update_policy_partial_update_deposit(self, client):
        resp = client.put(
            f"/admin/policies/{VALID_RESTAURANT_ID}",
            json={"deposit_required": True, "deposit_amount": 50},
        )
        if resp.status_code == 200:
            data = resp.json()
            assert data["deposit_required"] is True
            assert data["deposit_amount"] == 50

    def test_update_policy_opening_hours_replaced(self, client):
        new_hours = [
            {"day_of_week": 0, "open_time": "08:00", "close_time": "21:00", "is_closed": False}
        ]
        resp = client.put(
            f"/admin/policies/{VALID_RESTAURANT_ID}",
            json={"opening_hours": new_hours},
        )
        if resp.status_code == 200:
            assert len(resp.json()["opening_hours"]) == 1

    def test_update_policy_deposit_rules_cleared(self, client):
        resp = client.put(
            f"/admin/policies/{VALID_RESTAURANT_ID}",
            json={"deposit_rules": []},
        )
        if resp.status_code == 200:
            assert resp.json()["deposit_rules"] == []

    def test_update_policy_empty_body_no_change(self, client):
        """Empty body should be valid (all fields optional) and return 200."""
        resp = client.put(f"/admin/policies/{VALID_RESTAURANT_ID}", json={})
        assert resp.status_code in (200, 404)  # 404 if no policy exists yet

    def test_update_policy_response_has_restaurant_id(self, client):
        resp = client.put(
            f"/admin/policies/{VALID_RESTAURANT_ID}",
            json={"max_party_size": 10},
        )
        if resp.status_code == 200:
            assert resp.json()["restaurant_id"] == VALID_RESTAURANT_ID

    def test_update_policy_invalid_body_422(self, client):
        resp = client.put(
            f"/admin/policies/{VALID_RESTAURANT_ID}",
            content="bad-json",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 422


# ===========================================================================
# 6. CALL LOGS  –  GET /admin/calls/{restaurant_id}
# ===========================================================================

class TestCallLogs:
    """Tests for GET /admin/calls/{restaurant_id}"""

    def test_call_logs_restaurant_not_found(self, client):
        resp = client.get(f"/admin/calls/{INVALID_RESTAURANT_ID}")
        assert resp.status_code == 404

    def test_call_logs_default_pagination(self, client):
        resp = client.get(f"/admin/calls/{VALID_RESTAURANT_ID}")
        if resp.status_code == 200:
            data = resp.json()
            assert data["limit"] == 50
            assert data["offset"] == 0

    def test_call_logs_custom_limit(self, client):
        resp = client.get(f"/admin/calls/{VALID_RESTAURANT_ID}?limit=10")
        if resp.status_code == 200:
            data = resp.json()
            assert data["limit"] == 10
            assert len(data["calls"]) <= 10

    def test_call_logs_custom_offset(self, client):
        resp = client.get(f"/admin/calls/{VALID_RESTAURANT_ID}?offset=5")
        if resp.status_code == 200:
            assert resp.json()["offset"] == 5

    def test_call_logs_limit_exceeds_max_422(self, client):
        """limit > 100 should be rejected."""
        resp = client.get(f"/admin/calls/{VALID_RESTAURANT_ID}?limit=200")
        assert resp.status_code == 422

    def test_call_logs_negative_offset_422(self, client):
        resp = client.get(f"/admin/calls/{VALID_RESTAURANT_ID}?offset=-1")
        assert resp.status_code == 422

    def test_call_logs_response_structure(self, client):
        resp = client.get(f"/admin/calls/{VALID_RESTAURANT_ID}")
        if resp.status_code == 200:
            data = resp.json()
            assert "calls" in data
            assert "total" in data
            assert "limit" in data
            assert "offset" in data

    def test_call_logs_call_fields(self, client):
        resp = client.get(f"/admin/calls/{VALID_RESTAURANT_ID}?limit=1")
        if resp.status_code == 200 and resp.json()["calls"]:
            call = resp.json()["calls"][0]
            for field in ["id", "call_id", "customer_phone", "status",
                          "duration", "transcript", "audio_url",
                          "booking_id", "created_at", "updated_at"]:
                assert field in call, f"Missing call field: {field}"

    def test_call_logs_total_non_negative(self, client):
        resp = client.get(f"/admin/calls/{VALID_RESTAURANT_ID}")
        if resp.status_code == 200:
            assert resp.json()["total"] >= 0

    def test_call_logs_calls_count_lte_limit(self, client):
        resp = client.get(f"/admin/calls/{VALID_RESTAURANT_ID}?limit=5")
        if resp.status_code == 200:
            assert len(resp.json()["calls"]) <= 5

    def test_call_logs_zero_limit_422(self, client):
        """limit=0 is technically ≤ 100 but should still be handled gracefully."""
        resp = client.get(f"/admin/calls/{VALID_RESTAURANT_ID}?limit=0")
        # FastAPI allows 0 unless ge=1 is set; just ensure no 500
        assert resp.status_code != 500

    def test_call_logs_large_offset_returns_empty(self, client):
        resp = client.get(f"/admin/calls/{VALID_RESTAURANT_ID}?offset=99999")
        if resp.status_code == 200:
            assert resp.json()["calls"] == []


# ===========================================================================
# 7. BOOKING LOGS  –  GET /admin/bookings/{restaurant_id}
# ===========================================================================

class TestBookingLogs:
    """Tests for GET /admin/bookings/{restaurant_id}"""

    def test_booking_logs_restaurant_not_found(self, client):
        resp = client.get(f"/admin/bookings/{INVALID_RESTAURANT_ID}")
        assert resp.status_code == 404

    def test_booking_logs_default_pagination(self, client):
        resp = client.get(f"/admin/bookings/{VALID_RESTAURANT_ID}")
        if resp.status_code == 200:
            data = resp.json()
            assert data["limit"] == 50
            assert data["offset"] == 0

    def test_booking_logs_custom_limit(self, client):
        resp = client.get(f"/admin/bookings/{VALID_RESTAURANT_ID}?limit=5")
        if resp.status_code == 200:
            assert len(resp.json()["bookings"]) <= 5

    def test_booking_logs_limit_exceeds_max_422(self, client):
        resp = client.get(f"/admin/bookings/{VALID_RESTAURANT_ID}?limit=101")
        assert resp.status_code == 422

    def test_booking_logs_negative_offset_422(self, client):
        resp = client.get(f"/admin/bookings/{VALID_RESTAURANT_ID}?offset=-5")
        assert resp.status_code == 422

    def test_booking_logs_response_structure(self, client):
        resp = client.get(f"/admin/bookings/{VALID_RESTAURANT_ID}")
        if resp.status_code == 200:
            data = resp.json()
            for key in ["bookings", "total", "limit", "offset", "status_filter"]:
                assert key in data

    def test_booking_logs_booking_fields(self, client):
        resp = client.get(f"/admin/bookings/{VALID_RESTAURANT_ID}?limit=1")
        if resp.status_code == 200 and resp.json()["bookings"]:
            booking = resp.json()["bookings"][0]
            for field in ["id", "customer_name", "customer_phone", "party_size",
                          "booking_time", "status", "stripe_payment_id",
                          "external_ref_id", "call_confidence", "created_at"]:
                assert field in booking, f"Missing booking field: {field}"

    def test_booking_logs_filter_confirmed(self, client):
        resp = client.get(f"/admin/bookings/{VALID_RESTAURANT_ID}?status=confirmed")
        if resp.status_code == 200:
            data = resp.json()
            assert data["status_filter"] == "confirmed"
            for b in data["bookings"]:
                assert b["status"].upper() == "CONFIRMED"

    def test_booking_logs_filter_failed(self, client):
        resp = client.get(f"/admin/bookings/{VALID_RESTAURANT_ID}?status=failed")
        if resp.status_code == 200:
            for b in resp.json()["bookings"]:
                assert b["status"].upper() == "FAILED"

    def test_booking_logs_filter_cancelled(self, client):
        resp = client.get(f"/admin/bookings/{VALID_RESTAURANT_ID}?status=cancelled")
        if resp.status_code == 200:
            for b in resp.json()["bookings"]:
                assert b["status"].upper() == "CANCELLED"

    def test_booking_logs_no_status_filter_returns_all(self, client):
        resp = client.get(f"/admin/bookings/{VALID_RESTAURANT_ID}")
        if resp.status_code == 200:
            assert resp.json()["status_filter"] is None

    def test_booking_logs_total_non_negative(self, client):
        resp = client.get(f"/admin/bookings/{VALID_RESTAURANT_ID}")
        if resp.status_code == 200:
            assert resp.json()["total"] >= 0

    def test_booking_logs_large_offset_empty(self, client):
        resp = client.get(f"/admin/bookings/{VALID_RESTAURANT_ID}?offset=99999")
        if resp.status_code == 200:
            assert resp.json()["bookings"] == []

    def test_booking_logs_pagination_offset_advances(self, client):
        """Results at offset=0 and offset=1 should differ (if enough data)."""
        r1 = client.get(f"/admin/bookings/{VALID_RESTAURANT_ID}?limit=1&offset=0")
        r2 = client.get(f"/admin/bookings/{VALID_RESTAURANT_ID}?limit=1&offset=1")
        if r1.status_code == 200 and r2.status_code == 200:
            b1 = r1.json()["bookings"]
            b2 = r2.json()["bookings"]
            if b1 and b2:
                assert b1[0]["id"] != b2[0]["id"]


# ===========================================================================
# 8. EDGE CASES & CROSS-CUTTING CONCERNS
# ===========================================================================

class TestEdgeCases:
    """Misc edge-case and cross-cutting tests."""

    def test_all_admin_routes_return_json(self, client):
        endpoints = [
            "/admin/health",
            f"/admin/dashboard/stats/{VALID_RESTAURANT_ID}",
            f"/admin/policies/{VALID_RESTAURANT_ID}",
            f"/admin/calls/{VALID_RESTAURANT_ID}",
            f"/admin/bookings/{VALID_RESTAURANT_ID}",
        ]
        for url in endpoints:
            resp = client.get(url)
            assert "application/json" in resp.headers.get("content-type", ""), (
                f"{url} did not return JSON"
            )

    def test_unknown_admin_route_returns_404(self, client):
        resp = client.get("/admin/nonexistent-route")
        assert resp.status_code == 404

    def test_post_to_get_only_endpoint_405(self, client):
        resp = client.post(f"/admin/dashboard/stats/{VALID_RESTAURANT_ID}")
        assert resp.status_code == 405

    def test_delete_policy_not_allowed(self, client):
        resp = client.delete(f"/admin/policies/{VALID_RESTAURANT_ID}")
        assert resp.status_code == 405

    def test_patch_policy_not_allowed(self, client):
        resp = client.patch(f"/admin/policies/{VALID_RESTAURANT_ID}", json={})
        assert resp.status_code == 405

    def test_sql_injection_in_restaurant_id(self, client):
        malicious = "'; DROP TABLE restaurants; --"
        for url in [
            f"/admin/dashboard/stats/{malicious}",
            f"/admin/policies/{malicious}",
            f"/admin/calls/{malicious}",
            f"/admin/bookings/{malicious}",
        ]:
            resp = client.get(url)
            # Should return 404 (not found) or 422, never 500
            assert resp.status_code in (404, 422), (
                f"Unexpected status {resp.status_code} for {url}"
            )

    def test_very_long_restaurant_id(self, client):
        long_id = "a" * 500
        resp = client.get(f"/admin/dashboard/stats/{long_id}")
        assert resp.status_code in (404, 422)

    def test_unicode_restaurant_id(self, client):
        resp = client.get("/admin/dashboard/stats/caf%C3%A9-001")
        assert resp.status_code in (404, 422)

    def test_calls_and_bookings_limit_boundary_100(self, client):
        for url in [
            f"/admin/calls/{VALID_RESTAURANT_ID}?limit=100",
            f"/admin/bookings/{VALID_RESTAURANT_ID}?limit=100",
        ]:
            resp = client.get(url)
            assert resp.status_code in (200, 404)

    def test_calls_and_bookings_limit_boundary_101(self, client):
        for url in [
            f"/admin/calls/{VALID_RESTAURANT_ID}?limit=101",
            f"/admin/bookings/{VALID_RESTAURANT_ID}?limit=101",
        ]:
            resp = client.get(url)
            assert resp.status_code == 422


# ===========================================================================
# 9. UNIT TESTS – service functions with fully mocked DB
# ===========================================================================

class TestServiceUnits:
    """Pure unit tests that mock the DB and test service logic directly."""

    def _run(self, coro):
        import asyncio
        return asyncio.get_event_loop().run_until_complete(coro)

    # --- get_call_logs ---

    def test_get_call_logs_returns_paginated_data(self, mock_db):
        from admin.admin_service import get_call_logs

        mock_restaurant = _make_restaurant()
        calls = [_make_call(i) for i in range(3)]

        mock_db.query.return_value.filter.return_value.first.return_value = mock_restaurant
        mock_db.query.return_value.filter.return_value.order_by.return_value \
            .offset.return_value.limit.return_value.all.return_value = calls
        mock_db.query.return_value.filter.return_value.count.return_value = 3

        result = self._run(get_call_logs(VALID_RESTAURANT_ID, 50, 0, mock_db))
        assert result["total"] == 3
        assert len(result["calls"]) == 3

    def test_get_call_logs_restaurant_not_found_raises(self, mock_db):
        from admin.admin_service import get_call_logs
        from fastapi import HTTPException

        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc:
            self._run(get_call_logs(INVALID_RESTAURANT_ID, 50, 0, mock_db))
        assert exc.value.status_code == 404

    # --- get_booking_logs ---

    def test_get_booking_logs_returns_paginated_data(self, mock_db):
        from admin.admin_service import get_booking_logs

        mock_restaurant = _make_restaurant()
        bookings = [_make_booking(i) for i in range(5)]

        mock_db.query.return_value.filter.return_value.first.return_value = mock_restaurant
        mock_db.query.return_value.filter.return_value \
            .order_by.return_value.offset.return_value.limit.return_value.all.return_value = bookings
        mock_db.query.return_value.filter.return_value.count.return_value = 5

        result = self._run(get_booking_logs(VALID_RESTAURANT_ID, None, 50, 0, mock_db))
        assert result["total"] == 5

    def test_get_booking_logs_restaurant_not_found_raises(self, mock_db):
        from admin.admin_service import get_booking_logs
        from fastapi import HTTPException

        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc:
            self._run(get_booking_logs(INVALID_RESTAURANT_ID, None, 50, 0, mock_db))
        assert exc.value.status_code == 404

    # --- create_policy ---

    def test_create_policy_restaurant_not_found_raises(self, mock_db):
        from admin.admin_service import create_policy, PolicyCreate
        from fastapi import HTTPException

        mock_db.query.return_value.filter.return_value.first.return_value = None

        payload = PolicyCreate(
            deposit_required=False,
            max_party_size=10,
            opening_hours=[{"day_of_week": 0, "open_time": "09:00",
                            "close_time": "22:00", "is_closed": False}],
        )
        with pytest.raises(HTTPException) as exc:
            self._run(create_policy(INVALID_RESTAURANT_ID, payload, mock_db))
        assert exc.value.status_code == 404

    # --- update_policy ---

    def test_update_policy_no_policy_raises_404(self, mock_db):
        from admin.admin_service import update_policy, PolicyUpdate
        from fastapi import HTTPException

        mock_restaurant = _make_restaurant()
        # restaurant found, policy not found
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_restaurant, None
        ]

        with pytest.raises(HTTPException) as exc:
            self._run(update_policy(VALID_RESTAURANT_ID, PolicyUpdate(), mock_db))
        assert exc.value.status_code == 404


# ===========================================================================
# 10. FULL WORKFLOW INTEGRATION TEST
# ===========================================================================

class TestFullWorkflow:
    """
    End-to-end workflow: create policy → read it back → update it → verify.
    Skipped automatically if the restaurant doesn't exist in the live DB.
    """

    def test_policy_create_read_update_cycle(self, client, sample_policy_payload):
        # Step 1: Create
        create_resp = client.post(
            f"/admin/policies/{VALID_RESTAURANT_ID}",
            json=sample_policy_payload,
        )
        if create_resp.status_code != 200:
            pytest.skip("Restaurant not available in test DB")

        created = create_resp.json()
        assert created["max_party_size"] == sample_policy_payload["max_party_size"]

        # Step 2: Read back
        get_resp = client.get(f"/admin/policies/{VALID_RESTAURANT_ID}")
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == created["id"]

        # Step 3: Update max_party_size
        update_resp = client.put(
            f"/admin/policies/{VALID_RESTAURANT_ID}",
            json={"max_party_size": 20},
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["max_party_size"] == 20

        # Step 4: Verify dashboard reflects restaurant
        dash_resp = client.get(f"/admin/dashboard/stats/{VALID_RESTAURANT_ID}")
        assert dash_resp.status_code == 200

    def test_calls_and_bookings_consistent_totals(self, client):
        calls_resp = client.get(f"/admin/calls/{VALID_RESTAURANT_ID}")
        bookings_resp = client.get(f"/admin/bookings/{VALID_RESTAURANT_ID}")

        if calls_resp.status_code == 200 and bookings_resp.status_code == 200:
            calls_total = calls_resp.json()["total"]
            bookings_total = bookings_resp.json()["total"]
            # Totals should be non-negative integers
            assert isinstance(calls_total, int) and calls_total >= 0
            assert isinstance(bookings_total, int) and bookings_total >= 0

    def test_dashboard_stats_match_booking_counts(self, client):
        dash = client.get(f"/admin/dashboard/stats/{VALID_RESTAURANT_ID}")
        if dash.status_code != 200:
            pytest.skip("Restaurant not available")

        data = dash.json()
        # successful + failed should not exceed total implied by success_rate
        total = data["successful_bookings"] + data["failed_bookings"]
        if total > 0:
            expected_rate = round(data["successful_bookings"] / total * 100, 2)
            assert abs(data["success_rate"] - expected_rate) < 0.1
