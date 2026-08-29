import pytest

from app.main import app
from tests.helpers import (
    auth_client,
    jawapan_betul_untuk,
    jawapan_salah_untuk,
    seed_questions,
    start_attempt,
)


@pytest.fixture()
def murid_client(user_factory):
    user_factory(username="murid.test", role="murid")
    return auth_client(app, "murid.test")


@pytest.fixture()
def staff_client(user_factory):
    user_factory(
        username="pentadbir",
        role="super_admin",
        nama_first="Pentadbir",
        nama_last="Sekolah",
    )
    return auth_client(app, "pentadbir")


def submit(client, attempt, jawapan_list):
    return client.post(
        f"/api/v1/quiz-attempts/{attempt['id']}/submit",
        json={"jawapan": jawapan_list},
    )


def soalan_by_id(seeded):
    return {s["id"]: s for s in seeded}


def jawapan_semua_betul(attempt, seeded):
    peta = soalan_by_id(seeded)
    return [
        {"question_id": s["id"], "data_jawapan": jawapan_betul_untuk(peta[s["id"]])}
        for s in attempt["soalan"]
    ]


def jawapan_semua_salah(attempt, seeded):
    peta = soalan_by_id(seeded)
    return [
        {"question_id": s["id"], "data_jawapan": jawapan_salah_untuk(peta[s["id"]])}
        for s in attempt["soalan"]
    ]


def test_mula_percubaan_201(staff_client, murid_client):
    seed_questions(staff_client, count=10)
    attempt = start_attempt(murid_client)
    assert attempt["status"] == "dalam_progres"
    assert attempt["jumlah_soalan"] == 10
    assert len(attempt["soalan"]) == 10
    assert attempt["topic_nama"] == "Nombor dan Operasi"
    assert attempt["nama_peserta"] == "Ahmad bin Ali"
    assert attempt["skor"] is None
    assert attempt["masa_hantar"] is None


def test_mula_percubaan_tanpa_autentikasi_401(client):
    response = client.post(
        "/api/v1/quiz-attempts",
        json={"topic_id": 1, "tahap_kesukaran": "mudah"},
    )
    assert response.status_code == 401
    assert response.json()["detail"]["kod"] == "SESI_TAMAT"


def test_mula_percubaan_staff_403(staff_client):
    seed_questions(staff_client, count=10)
    response = staff_client.post(
        "/api/v1/quiz-attempts",
        json={"topic_id": 1, "tahap_kesukaran": "mudah"},
    )
    assert response.status_code == 403
    assert response.json()["detail"]["kod"] == "TIADA_KEBENARAN"


def test_mula_percubaan_tidak_dedah_jawapan_betul(staff_client, murid_client):
    seed_questions(staff_client, count=10)
    attempt = start_attempt(murid_client)
    body = str(attempt)
    assert "jawapan_betul" not in body


def test_mula_percubaan_topik_tidak_wujud_404(murid_client):
    response = murid_client.post(
        "/api/v1/quiz-attempts",
        json={"topic_id": 999, "tahap_kesukaran": "mudah"},
    )
    assert response.status_code == 404
    assert response.json()["detail"]["kod"] == "SUMBER_TIDAK_DIJUMPAI"


def test_mula_percubaan_soalan_tidak_mencukupi_400(staff_client, murid_client):
    seed_questions(staff_client, count=9)
    response = murid_client.post(
        "/api/v1/quiz-attempts",
        json={"topic_id": 1, "tahap_kesukaran": "mudah"},
    )
    assert response.status_code == 400
    body = response.json()["detail"]
    assert body["kod"] == "SOALAN_TIDAK_MENCUKUPI"
    assert "9" in body["mesej"]


def test_mula_percubaan_tamper_nama_peserta_422(murid_client):
    response = murid_client.post(
        "/api/v1/quiz-attempts",
        json={
            "topic_id": 1,
            "tahap_kesukaran": "mudah",
            "nama_peserta": "Ali",
        },
    )
    assert response.status_code == 422


def test_hantar_semua_betul_skor_10(staff_client, murid_client):
    seeded = seed_questions(staff_client, count=10)
    attempt = start_attempt(murid_client)
    response = submit(murid_client, attempt, jawapan_semua_betul(attempt, seeded))
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "selesai"
    assert data["skor"] == 10
    assert data["masa_hantar"] is not None
    assert len(data["perincian"]) == 10
    assert all(item["adalah_betul"] for item in data["perincian"])
    assert all(item["jawapan_betul"] is not None for item in data["perincian"])


def test_hantar_semua_salah_skor_0(staff_client, murid_client):
    seeded = seed_questions(staff_client, count=10)
    attempt = start_attempt(murid_client)
    response = submit(murid_client, attempt, jawapan_semua_salah(attempt, seeded))
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["skor"] == 0
    assert all(not item["adalah_betul"] for item in data["perincian"])


def test_hantar_tamper_medan_adalah_betul_422(staff_client, murid_client):
    seeded = seed_questions(staff_client, count=10)
    attempt = start_attempt(murid_client)
    jawapan = jawapan_semua_betul(attempt, seeded)
    jawapan[0]["adalah_betul"] = True
    jawapan[0]["skor"] = 10
    response = submit(murid_client, attempt, jawapan)
    assert response.status_code == 422


def test_hantar_9_jawapan_422(staff_client, murid_client):
    seeded = seed_questions(staff_client, count=10)
    attempt = start_attempt(murid_client)
    jawapan = jawapan_semua_betul(attempt, seeded)[:9]
    response = submit(murid_client, attempt, jawapan)
    assert response.status_code == 422


def test_hantar_question_id_duplikasi_422(staff_client, murid_client):
    seeded = seed_questions(staff_client, count=10)
    attempt = start_attempt(murid_client)
    jawapan = jawapan_semua_betul(attempt, seeded)
    jawapan[1]["question_id"] = jawapan[0]["question_id"]
    response = submit(murid_client, attempt, jawapan)
    assert response.status_code == 422


def test_hantar_question_id_bukan_milik_percubaan_400(staff_client, murid_client):
    seeded = seed_questions(staff_client, count=10)
    attempt = start_attempt(murid_client)
    jawapan = jawapan_semua_betul(attempt, seeded)
    jawapan[0]["question_id"] = 99999
    response = submit(murid_client, attempt, jawapan)
    assert response.status_code == 400
    assert response.json()["detail"]["kod"] == "SOALAN_TIDAK_SAH"


def test_hantar_dua_kali_409(staff_client, murid_client):
    seeded = seed_questions(staff_client, count=10)
    attempt = start_attempt(murid_client)
    response = submit(murid_client, attempt, jawapan_semua_betul(attempt, seeded))
    assert response.status_code == 200
    response = submit(murid_client, attempt, jawapan_semua_betul(attempt, seeded))
    assert response.status_code == 409
    assert response.json()["detail"]["kod"] == "KUIZ_TELAH_SELESAI"


def test_get_result_selesai(staff_client, murid_client):
    seeded = seed_questions(staff_client, count=10)
    attempt = start_attempt(murid_client)
    submit(murid_client, attempt, jawapan_semua_betul(attempt, seeded))

    response = murid_client.get(f"/api/v1/quiz-attempts/{attempt['id']}/result")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "selesai"
    assert data["skor"] == 10
    assert len(data["perincian"]) == 10


def test_get_result_dalam_progres_409(staff_client, murid_client):
    seed_questions(staff_client, count=10)
    attempt = start_attempt(murid_client)
    response = murid_client.get(f"/api/v1/quiz-attempts/{attempt['id']}/result")
    assert response.status_code == 409
    assert response.json()["detail"]["kod"] == "KUIZ_BELUM_SELESAI"


def test_get_result_dalam_progres_dengan_include_questions(staff_client, murid_client):
    seed_questions(staff_client, count=10)
    attempt = start_attempt(murid_client)
    response = murid_client.get(
        f"/api/v1/quiz-attempts/{attempt['id']}/result",
        params={"include_questions": "true"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "dalam_progres"
    assert len(data["soalan"]) == 10
    assert "jawapan_betul" not in str(data)


def test_get_result_tidak_wujud_404(murid_client):
    response = murid_client.get("/api/v1/quiz-attempts/999/result")
    assert response.status_code == 404


def test_isi_kosong_normalisasi_huruf_dan_ruang(staff_client, murid_client):
    seeded = seed_questions(staff_client, count=10, jenis="isi_tempat_kosong")
    attempt = start_attempt(murid_client)
    jawapan = jawapan_semua_betul(attempt, seeded)
    teks_betul = jawapan[0]["data_jawapan"]["teks"]
    jawapan[0]["data_jawapan"] = {"teks": f"  {teks_betul.upper()}  "}
    response = submit(murid_client, attempt, jawapan)
    assert response.json()["data"]["perincian"][0]["adalah_betul"] is True


def test_isi_kosong_teks_kosong_salah(staff_client, murid_client):
    seeded = seed_questions(staff_client, count=10, jenis="isi_tempat_kosong")
    attempt = start_attempt(murid_client)
    jawapan = jawapan_semua_betul(attempt, seeded)
    jawapan[0]["data_jawapan"] = {"teks": "   "}
    response = submit(murid_client, attempt, jawapan)
    data = response.json()["data"]
    assert data["perincian"][0]["adalah_betul"] is False
    assert data["skor"] == 9


def test_betul_salah_penggredan(staff_client, murid_client):
    seeded = seed_questions(staff_client, count=10, jenis="betul_salah")
    attempt = start_attempt(murid_client)
    jawapan = jawapan_semua_betul(attempt, seeded)
    jawapan[0]["data_jawapan"] = {"nilai": not jawapan[0]["data_jawapan"]["nilai"]}
    response = submit(murid_client, attempt, jawapan)
    data = response.json()["data"]
    assert data["perincian"][0]["adalah_betul"] is False
    assert data["skor"] == 9


def test_padanan_set_tertib_diabaikan(staff_client, murid_client):
    seeded = seed_questions(staff_client, count=10, jenis="padanan")
    attempt = start_attempt(murid_client)
    jawapan = jawapan_semua_betul(attempt, seeded)
    pasangan = jawapan[0]["data_jawapan"]["pasangan"]
    jawapan[0]["data_jawapan"] = {"pasangan": list(reversed(pasangan))}
    response = submit(murid_client, attempt, jawapan)
    assert response.json()["data"]["perincian"][0]["adalah_betul"] is True


def test_padanan_pasangan_salah_false(staff_client, murid_client):
    seeded = seed_questions(staff_client, count=10, jenis="padanan")
    attempt = start_attempt(murid_client)
    jawapan = jawapan_semua_betul(attempt, seeded)
    pasangan = jawapan[0]["data_jawapan"]["pasangan"]
    jawapan[0]["data_jawapan"] = {
        "pasangan": [
            {"kiri": pasangan[0]["kiri"], "kanan": pasangan[1]["kanan"]},
            {"kiri": pasangan[1]["kiri"], "kanan": pasangan[0]["kanan"]},
        ]
    }
    response = submit(murid_client, attempt, jawapan)
    data = response.json()["data"]
    assert data["perincian"][0]["adalah_betul"] is False
    assert data["skor"] == 9


def test_senarai_attempts_murid_hanya_lihat_sendiri(staff_client, murid_client, user_factory):
    seeded = seed_questions(staff_client, count=10)
    attempt = start_attempt(murid_client)
    submit(murid_client, attempt, jawapan_semua_betul(attempt, seeded))

    user_factory(
        username="murid2",
        role="murid",
        nama_first="Siti",
        nama_last="Aminah",
    )
    murid2 = auth_client(app, "murid2")
    start_attempt(murid2)

    response = murid_client.get("/api/v1/quiz-attempts")
    assert response.status_code == 200
    assert response.json()["meta"]["total_items"] == 1
    assert response.json()["data"][0]["nama_peserta"] == "Ahmad bin Ali"


def test_senarai_attempts_staff_penapis_participant(staff_client, user_factory):
    seeded = seed_questions(staff_client, count=10)
    user_factory(
        username="murid1",
        role="murid",
        nama_first="Ahmad",
        nama_last="bin Ali",
    )
    murid1 = auth_client(app, "murid1")
    attempt = start_attempt(murid1)
    submit(murid1, attempt, jawapan_semua_betul(attempt, seeded))

    user_factory(
        username="murid2",
        role="murid",
        nama_first="Siti",
        nama_last="Aminah",
    )
    murid2 = auth_client(app, "murid2")
    start_attempt(murid2)

    response = staff_client.get(
        "/api/v1/quiz-attempts",
        params={"participant_name": "ahmad", "status": "selesai"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["total_items"] == 1
    assert body["data"][0]["nama_peserta"] == "Ahmad bin Ali"
    assert body["data"][0]["skor"] == 10
    assert body["data"][0]["topic_nama"] == "Nombor dan Operasi"

    response = staff_client.get("/api/v1/quiz-attempts")
    assert response.json()["meta"]["total_items"] == 2


def test_result_soalan_dipadam_papar_placeholder(murid_client, staff_client):
    seeded = seed_questions(staff_client, count=10)
    attempt = start_attempt(murid_client)
    submit(murid_client, attempt, jawapan_semua_betul(attempt, seeded))

    soalan_ids = [s["id"] for s in attempt["soalan"]]
    for question_id in soalan_ids:
        staff_client.delete(f"/api/v1/questions/{question_id}")

    response = murid_client.get(f"/api/v1/quiz-attempts/{attempt['id']}/result")
    assert response.status_code == 200
    perincian = response.json()["data"]["perincian"]
    assert all(item["teks_soalan"] == "Soalan telah dipadam" for item in perincian)
    assert all(item["jawapan_betul"] is None for item in perincian)
    assert all(item["jawapan_murid"] is not None for item in perincian)