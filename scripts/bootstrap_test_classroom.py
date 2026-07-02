#!/usr/bin/env python3
"""Bootstrap a teacher, school, and classroom against a running dev API.

Milestone 5 (teacher dashboard UI) doesn't exist yet, but the backend
endpoints it will use (registration, admin approval, classroom creation)
already work. This script drives them directly so the Milestone 3 student
flow can be tested end-to-end without a UI for classroom creation.

Usage:
    .venv/bin/python3 scripts/bootstrap_test_classroom.py

Prompts for the admin password (matches TEACHER_PASSWORD_HASH in .env).
Safe to re-run: reuses the teacher/school if they already exist and just
creates a fresh classroom (and thus a fresh join code) each time.
"""

from __future__ import annotations

import argparse
import getpass
import sys

import httpx

SESSION_COOKIE = "dice_session"


def login(client: httpx.Client, payload: dict) -> httpx.Response:
    """POST /auth/login and re-arm the client's cookie jar for plain-http local use.

    The API sets the session cookie with Secure=True. httpx's cookie jar (like a
    browser) refuses to send Secure cookies back over http://, so without this the
    cookie from a successful login would silently be dropped on every later request.
    """
    response = client.post("/auth/login", json=payload)
    value = response.cookies.get(SESSION_COOKIE)
    if value:
        client.cookies.set(SESSION_COOKIE, value)
    return response


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the bootstrap script."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="API base URL")
    parser.add_argument("--admin-password", default=None, help="Admin password (prompted if omitted)")
    parser.add_argument("--teacher-email", default="test.teacher@carmelhengelo.nl")
    parser.add_argument("--teacher-password", default="testpassword123")
    parser.add_argument("--school-name", default="Test School")
    parser.add_argument("--classroom-name", default="Test Classroom")
    return parser.parse_args()


def fail(message: str, response: httpx.Response | None = None) -> None:
    """Print an error and exit non-zero."""
    print(f"ERROR: {message}", file=sys.stderr)
    if response is not None:
        print(f"  {response.status_code} {response.text}", file=sys.stderr)
    sys.exit(1)


def ensure_teacher_approved(
    client: httpx.Client, admin_password: str, email: str, password: str, school_name: str
) -> None:
    """Register the teacher/school and approve them as admin, if not already done."""
    probe = login(client, {"email": email, "password": password})
    if probe.status_code == 200:
        print(f"Teacher {email} already approved, reusing.")
        return
    if probe.status_code == 403:
        print(f"Teacher {email} registered but pending approval, approving now.")
    elif probe.status_code == 401:
        print(f"Registering teacher {email} ...")
        register = client.post(
            "/auth/register",
            json={"email": email, "password": password, "new_school_name": school_name},
        )
        if register.status_code != 202:
            fail("Registration failed", register)
    else:
        fail("Unexpected response during teacher login probe", probe)

    admin_client = httpx.Client(base_url=client.base_url)
    admin_login = login(admin_client, {"password": admin_password})
    if admin_login.status_code != 200:
        fail("Admin login failed - check --admin-password", admin_login)

    requests_resp = admin_client.get("/admin/requests")
    if requests_resp.status_code != 200:
        fail("Failed to list pending requests", requests_resp)
    pending = [r for r in requests_resp.json() if r["teacher_email"] == email]
    if not pending:
        fail(f"No pending request found for {email} - already approved elsewhere?")
    request_id = pending[0]["id"]
    approve = admin_client.post(f"/admin/requests/{request_id}/approve")
    if approve.status_code != 200:
        fail("Approval failed", approve)
    print(f"Approved teacher {email} for school '{school_name}'.")


def main() -> None:
    """Bootstrap a teacher, school, and classroom, then print the join code."""
    args = parse_args()
    admin_password = args.admin_password or getpass.getpass("Admin password: ")

    client = httpx.Client(base_url=args.base_url)

    ensure_teacher_approved(client, admin_password, args.teacher_email, args.teacher_password, args.school_name)

    teacher_login = login(client, {"email": args.teacher_email, "password": args.teacher_password})
    if teacher_login.status_code != 200:
        fail("Teacher login failed after approval", teacher_login)

    schools = client.get("/teacher/schools")
    if schools.status_code != 200:
        fail("Failed to list schools", schools)
    matches = [s for s in schools.json() if s["name"] == args.school_name]
    if not matches:
        fail(f"School '{args.school_name}' not found among teacher's approved schools")
    school_id = matches[0]["id"]

    classroom = client.post("/teacher/classrooms", json={"name": args.classroom_name, "school_id": school_id})
    if classroom.status_code != 200:
        fail("Classroom creation failed", classroom)
    data = classroom.json()

    print()
    print("Classroom ready:")
    print(f"  name:       {data['name']}")
    print(f"  join_code:  {data['join_code']}")
    print()
    print(f"Use join_code '{data['join_code']}' in the frontend student join screen to test Milestone 3.")


if __name__ == "__main__":
    main()
