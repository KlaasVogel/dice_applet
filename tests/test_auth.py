import pytest
from httpx import AsyncClient
from sqlalchemy import select

from dice_applet.db.base import get_session
from dice_applet.db.models import School, Teacher, TeacherSchool, TeacherSchoolStatus
from dice_applet.main import app
from dice_applet.services.auth import COOKIE_NAME, create_admin_token, create_teacher_token, hash_password


async def _get_session():
    gen = app.dependency_overrides[get_session]()
    session = await gen.__anext__()
    return session, gen


def _set_admin_cookie(client: AsyncClient) -> None:
    client.cookies.set(COOKIE_NAME, create_admin_token())


def _set_teacher_cookie(client: AsyncClient, teacher_id: int) -> None:
    client.cookies.set(COOKIE_NAME, create_teacher_token(teacher_id))


@pytest.mark.asyncio
async def test_register_invalid_email_domain(client: AsyncClient) -> None:
    response = await client.post(
        "/auth/register",
        json={"email": "teacher@gmail.com", "password": "secret", "new_school_name": "Carmel"},
    )
    assert response.status_code == 400
    assert "carmelhengelo.nl" in response.json()["detail"]


@pytest.mark.asyncio
async def test_register_must_provide_exactly_one_school(client: AsyncClient) -> None:
    response = await client.post(
        "/auth/register",
        json={"email": "a@carmelhengelo.nl", "password": "secret"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_register_both_school_and_new_name_rejected(client: AsyncClient) -> None:
    response = await client.post(
        "/auth/register",
        json={"email": "a@carmelhengelo.nl", "password": "secret", "school_id": 1, "new_school_name": "X"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_register_new_school(client: AsyncClient) -> None:
    response = await client.post(
        "/auth/register",
        json={"email": "teacher@carmelhengelo.nl", "password": "hunter2", "new_school_name": "Carmel Hengelo"},
    )
    assert response.status_code == 202
    assert response.json() == {"ok": True, "pending": True}


@pytest.mark.asyncio
async def test_register_new_school_creates_inactive_school(client: AsyncClient) -> None:
    await client.post(
        "/auth/register",
        json={"email": "t2@carmelhengelo.nl", "password": "hunter2", "new_school_name": "Test School"},
    )
    session, gen = await _get_session()
    school = (await session.execute(select(School).where(School.name == "Test School"))).scalar_one()
    assert school.is_active is False
    ts = (await session.execute(
        select(TeacherSchool).where(TeacherSchool.school_id == school.id)
    )).scalar_one()
    assert ts.status == TeacherSchoolStatus.pending_admin
    try:
        await gen.__anext__()
    except StopAsyncIteration:
        pass


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient) -> None:
    payload = {"email": "dup@carmelhengelo.nl", "password": "hunter2", "new_school_name": "Carmel Dup"}
    await client.post("/auth/register", json=payload)
    response = await client.post(
        "/auth/register",
        json={"email": "dup@carmelhengelo.nl", "password": "other", "new_school_name": "Other School"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_register_existing_school(client: AsyncClient) -> None:
    session, gen = await _get_session()
    school = School(name="Existing School", is_active=True)
    session.add(school)
    await session.commit()
    await session.refresh(school)
    school_id = school.id
    try:
        await gen.__anext__()
    except StopAsyncIteration:
        pass

    response = await client.post(
        "/auth/register",
        json={"email": "new@carmelhengelo.nl", "password": "hunter2", "school_id": school_id},
    )
    assert response.status_code == 202


@pytest.mark.asyncio
async def test_register_inactive_school_rejected(client: AsyncClient) -> None:
    session, gen = await _get_session()
    school = School(name="Inactive School", is_active=False)
    session.add(school)
    await session.commit()
    await session.refresh(school)
    school_id = school.id
    try:
        await gen.__anext__()
    except StopAsyncIteration:
        pass

    response = await client.post(
        "/auth/register",
        json={"email": "new2@carmelhengelo.nl", "password": "hunter2", "school_id": school_id},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_logout(client: AsyncClient) -> None:
    response = await client.post("/auth/logout")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


@pytest.mark.asyncio
async def test_me_unauthenticated(client: AsyncClient) -> None:
    response = await client.get("/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_as_admin(client: AsyncClient) -> None:
    _set_admin_cookie(client)
    resp = await client.get("/auth/me")
    assert resp.status_code == 200
    assert resp.json() == {"role": "admin", "teacher_id": None, "email": None}


@pytest.mark.asyncio
async def test_me_as_teacher(client: AsyncClient) -> None:
    session, gen = await _get_session()
    teacher = Teacher(email="me@carmelhengelo.nl", password_hash=hash_password("p"))
    session.add(teacher)
    await session.commit()
    await session.refresh(teacher)
    teacher_id = teacher.id
    try:
        await gen.__anext__()
    except StopAsyncIteration:
        pass

    _set_teacher_cookie(client, teacher_id)
    resp = await client.get("/auth/me")
    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "teacher"
    assert data["teacher_id"] == teacher_id
    assert data["email"] == "me@carmelhengelo.nl"


@pytest.mark.asyncio
async def test_teacher_login_blocked_while_pending(client: AsyncClient) -> None:
    """A teacher with only pending links cannot log in."""
    session, gen = await _get_session()
    school = School(name="Pending School", is_active=False)
    teacher = Teacher(email="pending@carmelhengelo.nl", password_hash=hash_password("pass"))
    session.add_all([school, teacher])
    await session.flush()
    session.add(TeacherSchool(teacher_id=teacher.id, school_id=school.id, status=TeacherSchoolStatus.pending_admin))
    await session.commit()
    try:
        await gen.__anext__()
    except StopAsyncIteration:
        pass

    resp = await client.post("/auth/login", json={"email": "pending@carmelhengelo.nl", "password": "pass"})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_teacher_login_success_after_approval(client: AsyncClient) -> None:
    """Teacher can log in after their TeacherSchool is approved."""
    session, gen = await _get_session()
    school = School(name="Approved School", is_active=True)
    teacher = Teacher(email="approved@carmelhengelo.nl", password_hash=hash_password("pass"))
    session.add_all([school, teacher])
    await session.flush()
    session.add(TeacherSchool(teacher_id=teacher.id, school_id=school.id, status=TeacherSchoolStatus.approved))
    await session.commit()
    try:
        await gen.__anext__()
    except StopAsyncIteration:
        pass

    resp = await client.post("/auth/login", json={"email": "approved@carmelhengelo.nl", "password": "pass"})
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}
