from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from app.core.exceptions import NotFoundError
from app.schemas.schemas import AdminUserUpdate, EtlTriggerIn
from tests.conftest import MockResult


def _make_user(**overrides: object) -> MagicMock:
    user = MagicMock()
    user.user_id = uuid.uuid4()
    user.email = "admin@fifa.com"
    user.display_name = "Admin FIFA"
    user.role = "admin"
    user.is_active = True
    user.created_at = datetime.now(UTC)
    user.update_at = datetime.now(UTC)
    user.refresh_jti = None
    for k, v in overrides.items():
        setattr(user, k, v)
    return user


class TestListUser:
    async def test_list_all(self, admin_service, mock_db) -> None:
        users = [_make_user(), _make_user(role="reader")]
        mock_db.execute.side_effect = [
            MockResult(scalar_one=len(users)),
            MockResult(scalars_list=users),
        ]

        result = await admin_service.list_user()

        assert result.total == 2
        assert len(result.items) == 2

    async def test_list_filter_by_role(self, admin_service, mock_db) -> None:
        users = [_make_user(role="admin")]
        mock_db.execute.side_effect = [
            MockResult(scalar_one=1),
            MockResult(scalars_list=users),
        ]

        result = await admin_service.list_user(role="admin")

        assert len(result.items) == 1
        assert result.items[0].role == "admin"

    async def test_list_filter_by_active(self, admin_service, mock_db) -> None:
        mock_db.execute.side_effect = [
            MockResult(scalar_one=0),
            MockResult(scalars_list=[]),
        ]

        result = await admin_service.list_user(is_active=True)

        assert result.items == []

    async def test_list_empty(self, admin_service, mock_db) -> None:
        mock_db.execute.side_effect = [
            MockResult(scalar_one=0),
            MockResult(scalars_list=[]),
        ]

        result = await admin_service.list_user()

        assert result.total == 0


class TestGetUser:
    async def test_get_success(self, admin_service, mock_db) -> None:
        user = _make_user()
        mock_db.execute.return_value = MockResult(scalar_one=user)

        result = await admin_service.get_user(str(user.user_id))

        assert result.email == "admin@fifa.com"

    async def test_get_not_found(self, admin_service, mock_db) -> None:
        mock_db.execute.return_value = MockResult(scalar_one=None)

        with pytest.raises(NotFoundError, match="Usuario no encontrado"):
            await admin_service.get_user(str(uuid.uuid4()))


class TestUpdateUser:
    async def test_update_role(self, admin_service, mock_db) -> None:
        user = _make_user(role="admin")
        mock_db.execute.return_value = MockResult(scalar_one=user)
        data = AdminUserUpdate(role="editor")

        result = await admin_service.update_user(str(user.user_id), data)

        assert result.role == "editor"

    async def test_update_deactivate(self, admin_service, mock_db) -> None:
        user = _make_user(is_active=True)
        mock_db.execute.return_value = MockResult(scalar_one=user)
        data = AdminUserUpdate(role="admin", is_active=False)

        result = await admin_service.update_user(str(user.user_id), data)

        assert result.is_active is False

    async def test_update_not_found(self, admin_service, mock_db) -> None:
        mock_db.execute.return_value = MockResult(scalar_one=None)
        data = AdminUserUpdate(role="reader")

        with pytest.raises(NotFoundError):
            await admin_service.update_user(str(uuid.uuid4()), data)


class TestSoftDeleteUser:
    async def test_soft_delete_sets_inactive(self, admin_service, mock_db) -> None:
        user = _make_user(is_active=True)
        mock_db.execute.return_value = MockResult(scalar_one=user)

        await admin_service.soft_delete_user(str(user.user_id))

        assert user.is_active is False

    async def test_soft_delete_not_found(self, admin_service, mock_db) -> None:
        mock_db.execute.return_value = MockResult(scalar_one=None)

        with pytest.raises(NotFoundError):
            await admin_service.soft_delete_user(str(uuid.uuid4()))


class TestTriggerEtl:
    async def test_trigger_success(self, admin_service, mock_db) -> None:
        data = EtlTriggerIn(dataset="all")

        result = await admin_service.trigger_etl(data, triggered_by="admin-1")

        assert result["status"] == "queued"
        assert result["dataset"] == "all"
        mock_db.add.assert_called_once()
        mock_db.flush.assert_awaited_once()

    async def test_trigger_with_dataset(self, admin_service, mock_db) -> None:
        data = EtlTriggerIn(dataset="matches")

        result = await admin_service.trigger_etl(data, triggered_by="admin-1")

        assert result["dataset"] == "matches"


class TestGetEtlStatus:
    async def test_status_with_results(self, admin_service, mock_db) -> None:
        run = MagicMock()
        run.run_id = 1
        run.dataset = "all"
        run.worker = "celery"
        run.status = "success"
        run.started_at = datetime.now(UTC)
        run.finished_at = datetime.now(UTC)
        run.rows_loaded = 1000
        run.rows_rejected = 5
        run.duration_s = 30.5
        run.triggered_by = "admin-1"
        mock_db.execute.return_value = MockResult(scalar_one=run)

        result = await admin_service.get_etl_status(dataset="all")

        assert result.status == "success"

    async def test_status_no_results(self, admin_service, mock_db) -> None:
        mock_db.execute.return_value = MockResult(scalar_one=None)

        result = await admin_service.get_etl_status(dataset="players")

        assert result.status == "success"


class TestGetDeadLetters:
    async def test_dead_letters_success(self, admin_service, mock_db) -> None:
        dl = MagicMock()
        dl.dl_id = 1
        dl.source_table = "matches"
        dl.source_row_id = 100
        dl.error_code = "INVALID_DATE"
        dl.error_detail = "Bad date format"
        dl.rejected_at = datetime.now(UTC)
        mock_db.execute.side_effect = [
            MockResult(scalar_one=1),
            MockResult(scalars_list=[dl]),
        ]

        result = await admin_service.get_dead_letters(page=1, page_size=20)

        assert result.total == 1

    async def test_dead_letters_empty(self, admin_service, mock_db) -> None:
        mock_db.execute.side_effect = [
            MockResult(scalar_one=0),
            MockResult(scalars_list=[]),
        ]

        result = await admin_service.get_dead_letters()

        assert result.items == []


class TestRefreshWarehouse:
    async def test_refresh_success(self, admin_service, mock_db) -> None:
        mock_db.execute.return_value = MockResult()

        result = await admin_service.refresh_warehouse()

        assert result["status"] == "ok"
        mock_db.execute.assert_awaited_once()


class TestGetAuditLog:
    async def test_audit_log_success(self, admin_service, mock_db) -> None:
        log_entry = MagicMock()
        log_entry.log_id = 1
        log_entry.schema_name = "public"
        log_entry.table_name = "users"
        log_entry.operation = "U"
        log_entry.changed_by = "admin-1"
        log_entry.changed_at = datetime.now(UTC)
        mock_db.execute.side_effect = [
            MockResult(scalar_one=1),
            MockResult(scalars_list=[log_entry]),
        ]

        result = await admin_service.get_audit_log(table_name="users", operation="U")

        assert result["total"] == 1
        assert len(result["items"]) == 1

    async def test_audit_log_empty(self, admin_service, mock_db) -> None:
        mock_db.execute.side_effect = [
            MockResult(scalar_one=0),
            MockResult(scalars_list=[]),
        ]

        result = await admin_service.get_audit_log()

        assert result["total"] == 0
