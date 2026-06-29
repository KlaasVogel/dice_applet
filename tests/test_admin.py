import bcrypt
import pytest
from httpx import AsyncClient
from sqlalchemy import select

from dice_applet.db.base import get_session
from dice_applet.db.models import School, Teacher, TeacherSchool, TeacherSchoolStatus
from dice_applet.main import app
from dice_applet.services.auth import COOKIE_NAME, create_admin_token, hash_password


async def _get_session():
    gen = app.dependency_overrides[get_session]()
    session = await gen.__anext__()
    return session, gen


def _set_admin_cookie(client: AsyncClient) -> None:
    client.cookies.set(COOKIE_NAME, create_admin_token())


@pytest.mark.asyncio
async def test_admin_required(client: AsyncClient) -> None:
    response = await client.get("/admin/requests")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_pending_requests_empty(client: AsyncClient) -> None:
    _set_admin_cookie(client)
    response = await client.get("/admin/requests")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_approve_pending_admin_request(client: AsyncClient) -> None:
    session, gen = await _get_session()
    school = School(name="New School", is_active=False)
    teacher = Teacher(email="t@carmelhengelo.nl", password_hash=hash_password("pass"))
    session.add_all([school, teacher])
    await session.flush()
    ts = TeacherSchool(teacher_id=teacher.id, school_id=school.id, status=TeacherSchoolStatus.pending_admin)
    session.add(ts)
    await session.commit()
    ts_id = ts.id
    school_id = school.id
    try:
        await gen.__anext__()
    except StopAsyncIteration:
        pass

    _set_admin_cookie(client)

    resp = await client.get("/admin/requests")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["status"] == "pending_admin"

    approve = await client.post(f"/admin/requests/{ts_id}/approve")
    assert approve.status_code == 200

    session2, gen2 = await _get_session()
    updated_school = await session2.get(School, school_id)
    assert updated_school is not None
    assert updated_school.is_active is True
    updated_ts = await session2.get(TeacherSchool, ts_id)
    assert updated_ts is not None
    assert updated_ts.status == TeacherSchoolStatus.approved
    try:
        await gen2.__anext__()
    except StopAsyncIteration:
        pass


@pytest.mark.asyncio
async def test_reject_pending_request(client: AsyncClient) -> None:
    session, gen = await _get_session()
    school = School(name="Reject School", is_active=False)
    teacher = Teacher(email="r@carmelhengelo.nl", password_hash=hash_password("pass"))
    session.add_all([school, teacher])
    await session.flush()
    ts = TeacherSchool(teacher_id=teacher.id, school_id=school.id, status=TeacherSchoolStatus.pending_admin)
    session.add(ts)
    await session.commit()
    ts_id = ts.id
    try:
        await gen.__anext__()
    except StopAsyncIteration:
        pass

    _set_admin_cookie(client)
    resp = await client.post(f"/admin/requests/{ts_id}/reject")
    assert resp.status_code == 200

    session2, gen2 = await _get_session()
    updated_ts = await session2.get(TeacherSchool, ts_id)
    assert updated_ts is not None
    assert updated_ts.status == TeacherSchoolStatus.rejected
    try:
        await gen2.__anext__()
    except StopAsyncIteration:
        pass


@pytest.mark.asyncio
async def test_list_schools(client: AsyncClient) -> None:
    session, gen = await _get_session()
    session.add_all([
        School(name="Alpha School", is_active=True),
        School(name="Beta School", is_active=False),
    ])
    await session.commit()
    try:
        await gen.__anext__()
    except StopAsyncIteration:
        pass

    _set_admin_cookie(client)
    resp = await client.get("/admin/schools")
    assert resp.status_code == 200
    names = [s["name"] for s in resp.json()]
    assert "Alpha School" in names
    assert "Beta School" in names


@pytest.mark.asyncio
async def test_list_teachers(client: AsyncClient) -> None:
    session, gen = await _get_session()
    session.add(Teacher(email="listed@carmelhengelo.nl", password_hash=hash_password("p")))
    await session.commit()
    try:
        await gen.__anext__()
    except StopAsyncIteration:
        pass

    _set_admin_cookie(client)
    resp = await client.get("/admin/teachers")
    assert resp.status_code == 200
    emails = [t["email"] for t in resp.json()]
    assert "listed@carmelhengelo.nl" in emails
