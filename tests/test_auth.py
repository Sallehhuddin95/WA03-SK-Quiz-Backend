from datetime import datetime, timedelta, timezone

from app.core.security import hash_session_token
from app.repositories.session import SessionRepository
from tests.helpers import login

COOKIE = "sk_quiz_sesi"


def test_login_berjaya_set_cookie(client, user_factory):
    user_factory(username="murid.test", role="murid")
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "murid.test", "kata_laluan": "rahasia123"},
    )
    assert response.status_code == 200
    set_cookie = response.headers.get("set-cookie", "")
    assert COOKIE in set_cookie
    assert "HttpOnly" in set_cookie
    data = response.json()["data"]
    assert data["username"] == "murid.test"
    assert data["role"] == "murid"
    assert data["mesti_tukar_kata_laluan"] is False


def test_login_murid_sertakan_kelas(client, user_factory, kelas_factory):
    kelas = kelas_factory(nama="6 Bijak", darjah=6)
    user_factory(username="murid.test", role="murid", kelas_id=kelas.id)
    data = login(client, "murid.test")
    assert data["kelas"] == {"id": kelas.id, "nama": "6 Bijak", "darjah": 6}


def test_login_staff_tiada_kelas(client, user_factory):
    user_factory(username="guru.test", role="admin")
    data = login(client, "guru.test")
    assert data["kelas"] is None


def test_login_kata_laluan_salah_401(client, user_factory):
    user_factory(username="murid.test", role="murid")
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "murid.test", "kata_laluan": "salah12345"},
    )
    assert response.status_code == 401
    body = response.json()["detail"]
    assert body["kod"] == "KELAYAKAN_TIDAK_SAH"
    assert body["mesej"] == "Nama pengguna atau kata laluan tidak sah."


def test_login_pengguna_tidak_wujud_401_sama(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "tiada.orang", "kata_laluan": "rahasia123"},
    )
    assert response.status_code == 401
    assert response.json()["detail"]["kod"] == "KELAYAKAN_TIDAK_SAH"


def test_login_akaun_tidak_aktif_403(client, user_factory):
    user_factory(username="murid.test", role="murid", aktif=False)
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "murid.test", "kata_laluan": "rahasia123"},
    )
    assert response.status_code == 403
    assert response.json()["detail"]["kod"] == "AKAUN_TIDAK_AKTIF"


def test_logout_revoke_sesi(client, user_factory):
    user_factory(username="murid.test", role="murid")
    login(client, "murid.test")
    response = client.post("/api/v1/auth/logout")
    assert response.status_code == 204

    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["detail"]["kod"] == "SESI_TAMAT"


def test_logout_tanpa_sesi_401(client):
    response = client.post("/api/v1/auth/logout")
    assert response.status_code == 401
    assert response.json()["detail"]["kod"] == "SESI_TAMAT"


def test_me_pulangkan_pengguna_sesi(client, user_factory):
    user_factory(
        username="guru.test",
        role="admin",
        nama_first="Siti",
        nama_last="Aminah",
    )
    login(client, "guru.test")
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["username"] == "guru.test"
    assert data["nama_first"] == "Siti"
    assert data["role"] == "admin"


def test_change_password_flow(client, user_factory):
    user_factory(username="murid.test", role="murid")
    login(client, "murid.test")

    response = client.post(
        "/api/v1/auth/change-password",
        json={
            "kata_laluan_semasa": "rahasia123",
            "kata_laluan_baru": "baru12345",
        },
    )
    assert response.status_code == 200

    # sesi semasa kekal sah
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 200

    # kata laluan lama tidak lagi sah
    client.post("/api/v1/auth/logout")
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "murid.test", "kata_laluan": "rahasia123"},
    )
    assert response.status_code == 401

    data = login(client, "murid.test", "baru12345")
    assert data["username"] == "murid.test"


def test_change_password_semasa_salah_401(client, user_factory):
    user_factory(username="murid.test", role="murid")
    login(client, "murid.test")
    response = client.post(
        "/api/v1/auth/change-password",
        json={
            "kata_laluan_semasa": "salah12345",
            "kata_laluan_baru": "baru12345",
        },
    )
    assert response.status_code == 401
    assert response.json()["detail"]["kod"] == "KELAYAKAN_TIDAK_SAH"


def test_mesti_tukar_kata_laluan_sekat_tindakan_lain(client, user_factory):
    user_factory(
        username="murid.test", role="murid", mesti_tukar_kata_laluan=True
    )
    login(client, "murid.test")

    # me dibenarkan supaya frontend boleh hidrat keadaan sesi
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 200
    assert response.json()["data"]["mesti_tukar_kata_laluan"] is True

    # endpoint lain disekat
    response = client.get("/api/v1/subjects")
    assert response.status_code == 403
    assert response.json()["detail"]["kod"] == "KATA_LALUAN_PERLU_DITUKAR"

    # selepas tukar kata laluan, akses normal kembali
    response = client.post(
        "/api/v1/auth/change-password",
        json={
            "kata_laluan_semasa": "rahasia123",
            "kata_laluan_baru": "baru12345",
        },
    )
    assert response.status_code == 200
    response = client.get("/api/v1/subjects")
    assert response.status_code == 200


def test_sesi_expired_ditolak(client, user_factory, db):
    user = user_factory(username="murid.test", role="murid")
    token = "token-sesi-expired"
    repository = SessionRepository()
    now = datetime.now(timezone.utc)
    repository.create(
        db,
        token_hash=hash_session_token(token),
        user_id=user.id,
        expires_at=now - timedelta(hours=1),
        last_seen_at=now,
    )
    db.commit()
    client.cookies.set(COOKIE, token)

    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["detail"]["kod"] == "SESI_TAMAT"


def test_sesi_direvoke_ditolak(client, user_factory, db):
    user = user_factory(username="murid.test", role="murid")
    token = "token-sesi-revoke"
    repository = SessionRepository()
    now = datetime.now(timezone.utc)
    session = repository.create(
        db,
        token_hash=hash_session_token(token),
        user_id=user.id,
        expires_at=now + timedelta(days=1),
        last_seen_at=now,
    )
    repository.revoke(db, session)
    db.commit()
    client.cookies.set(COOKIE, token)

    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["detail"]["kod"] == "SESI_TAMAT"