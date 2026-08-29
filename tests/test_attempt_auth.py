import pytest

from app.main import app
from tests.helpers import (
    auth_client,
    jawapan_betul_untuk,
    seed_questions,
    start_attempt,
)


@pytest.fixture()
def guru_a(client, user_factory):
    return user_factory(
        username="guru.a",
        role="admin",
        nama_first="Siti",
        nama_last="Aminah",
    )


@pytest.fixture()
def guru_b(client, user_factory):
    return user_factory(
        username="guru.b",
        role="admin",
        nama_first="Raj",
        nama_last="Kumar",
    )


@pytest.fixture()
def super_client(user_factory):
    user_factory(
        username="pentadbir",
        role="super_admin",
        nama_first="Pentadbir",
        nama_last="Sekolah",
    )
    return auth_client(app, "pentadbir")


def jawapan_semua_betul(attempt, seeded):
    peta = {s["id"]: s for s in seeded}
    return [
        {"question_id": s["id"], "data_jawapan": jawapan_betul_untuk(peta[s["id"]])}
        for s in attempt["soalan"]
    ]


def test_murid_mula_attempt_nama_dari_profil(super_client, user_factory):
    user_factory(
        username="murid.test",
        role="murid",
        nama_first="Ahmad",
        nama_last="bin Ali",
    )
    seed_questions(super_client, count=10)
    client = auth_client(app, "murid.test")
    attempt = start_attempt(client)
    assert attempt["nama_peserta"] == "Ahmad bin Ali"


def test_attempt_ownership_murid_lain_403(super_client, user_factory):
    seed_questions(super_client, count=10)
    user_factory(
        username="murid.a",
        role="murid",
        nama_first="Ahmad",
        nama_last="bin Ali",
    )
    murid_a = auth_client(app, "murid.a")
    attempt = start_attempt(murid_a)

    user_factory(
        username="murid.b",
        role="murid",
        nama_first="Siti",
        nama_last="Aminah",
    )
    murid_b = auth_client(app, "murid.b")

    # murid B tidak boleh lihat result attempt murid A
    response = murid_b.get(f"/api/v1/quiz-attempts/{attempt['id']}/result")
    assert response.status_code == 403
    assert response.json()["detail"]["kod"] == "TIADA_KEBENARAN"

    # murid B tidak nampak attempt murid A dalam senarai
    response = murid_b.get("/api/v1/quiz-attempts")
    assert response.json()["meta"]["total_items"] == 0


def test_staff_skop_kelas_attempt(
    super_client, user_factory, guru_a, guru_b, kelas_factory, assign_owner
):
    seeded = seed_questions(super_client, count=10)
    kelas_a = kelas_factory(nama="6 Bijak", darjah=6)
    kelas_b = kelas_factory(nama="5 Cerdas", darjah=5)
    assign_owner(guru_id=guru_a.id, kelas_id=kelas_a.id)
    assign_owner(guru_id=guru_b.id, kelas_id=kelas_b.id)

    user_factory(
        username="murid.a",
        role="murid",
        nama_first="Ahmad",
        nama_last="bin Ali",
        kelas_id=kelas_a.id,
    )
    user_factory(
        username="murid.b",
        role="murid",
        nama_first="Siti",
        nama_last="Aminah",
        kelas_id=kelas_b.id,
    )

    murid_a = auth_client(app, "murid.a")
    attempt_a = start_attempt(murid_a)
    submit_ok(murid_a, attempt_a, seeded)

    murid_b = auth_client(app, "murid.b")
    start_attempt(murid_b)

    guru_a_client = auth_client(app, "guru.a")

    # guru A nampak attempt murid kelas sendiri sahaja
    response = guru_a_client.get("/api/v1/quiz-attempts")
    assert response.json()["meta"]["total_items"] == 1
    assert response.json()["data"][0]["nama_peserta"] == "Ahmad bin Ali"

    # guru A boleh baca result attempt murid kelas sendiri
    response = guru_a_client.get(f"/api/v1/quiz-attempts/{attempt_a['id']}/result")
    assert response.status_code == 200

    # guru A tidak nampak attempt murid kelas guru B
    response_b = guru_a_client.get(
        "/api/v1/quiz-attempts",
        params={"participant_name": "Siti"},
    )
    assert response_b.status_code == 200
    assert response_b.json()["meta"]["total_items"] == 0


def submit_ok(client, attempt, seeded):
    response = client.post(
        f"/api/v1/quiz-attempts/{attempt['id']}/submit",
        json={"jawapan": jawapan_semua_betul(attempt, seeded)},
    )
    assert response.status_code == 200, response.text


def test_super_admin_lihat_semua_attempt(
    super_client, user_factory, kelas_factory, guru_a, assign_owner
):
    seeded = seed_questions(super_client, count=10)
    kelas_a = kelas_factory(nama="6 Bijak", darjah=6)
    assign_owner(guru_id=guru_a.id, kelas_id=kelas_a.id)
    user_factory(
        username="murid.a",
        role="murid",
        nama_first="Ahmad",
        nama_last="bin Ali",
        kelas_id=kelas_a.id,
    )
    murid_a = auth_client(app, "murid.a")
    attempt = start_attempt(murid_a)
    submit_ok(murid_a, attempt, seeded)

    response = super_client.get("/api/v1/quiz-attempts")
    assert response.json()["meta"]["total_items"] == 1

    response = super_client.get(f"/api/v1/quiz-attempts/{attempt['id']}/result")
    assert response.status_code == 200


def test_pratonton_tanpa_jawapan(super_client):
    seed_questions(super_client, count=10)
    response = super_client.get(
        "/api/v1/kuiz/pratonton",
        params={"topic_id": 1, "tahap_kesukaran": "mudah"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 10
    body = str(data)
    assert "jawapan_betul" not in body
    assert all("pilihan" in item for item in data)


def test_pratonton_murid_403(user_factory):
    user_factory(username="murid.test", role="murid")
    client = auth_client(app, "murid.test")
    response = client.get(
        "/api/v1/kuiz/pratonton",
        params={"topic_id": 1, "tahap_kesukaran": "mudah"},
    )
    assert response.status_code == 403
    assert response.json()["detail"]["kod"] == "TIADA_KEBENARAN"


def test_pratonton_soalan_tidak_mencukupi_400(super_client):
    seed_questions(super_client, count=9)
    response = super_client.get(
        "/api/v1/kuiz/pratonton",
        params={"topic_id": 1, "tahap_kesukaran": "mudah"},
    )
    assert response.status_code == 400
    assert response.json()["detail"]["kod"] == "SOALAN_TIDAK_MENCUKUPI"


def test_staff_tidak_boleh_hantar_attempt(super_client, user_factory):
    seed_questions(super_client, count=10)
    user_factory(
        username="murid.a",
        role="murid",
        nama_first="Ahmad",
        nama_last="bin Ali",
    )
    murid_a = auth_client(app, "murid.a")
    attempt = start_attempt(murid_a)

    response = super_client.post(
        f"/api/v1/quiz-attempts/{attempt['id']}/submit",
        json={"jawapan": []},
    )
    assert response.status_code == 403
    assert response.json()["detail"]["kod"] == "TIADA_KEBENARAN"


def test_semua_endpoint_tanpa_autentikasi_401(client):
    endpoints = [
        ("get", "/api/v1/quiz-attempts"),
        ("post", "/api/v1/quiz-attempts"),
        ("get", "/api/v1/quiz-attempts/1/result"),
        ("post", "/api/v1/quiz-attempts/1/submit"),
        ("get", "/api/v1/kuiz/pratonton?topic_id=1"),
    ]
    for method, url in endpoints:
        response = getattr(client, method)(url)
        assert response.status_code == 401, f"{method} {url}"
        assert response.json()["detail"]["kod"] == "SESI_TAMAT", url