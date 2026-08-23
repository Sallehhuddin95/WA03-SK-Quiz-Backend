from tests.helpers import (
    jawapan_betul_untuk,
    jawapan_salah_untuk,
    seed_questions,
    start_attempt,
)


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


def test_mula_percubaan_201(client):
    seed_questions(client, count=10)
    attempt = start_attempt(client)
    assert attempt["status"] == "dalam_progres"
    assert attempt["jumlah_soalan"] == 10
    assert len(attempt["soalan"]) == 10
    assert attempt["topic_nama"] == "Nombor dan Operasi"
    assert attempt["skor"] is None
    assert attempt["masa_hantar"] is None


def test_mula_percubaan_tidak_dedah_jawapan_betul(client):
    seed_questions(client, count=10)
    attempt = start_attempt(client)
    body = str(attempt)
    assert "jawapan_betul" not in body


def test_mula_percubaan_topik_tidak_wujud_404(client):
    response = client.post(
        "/api/v1/quiz-attempts",
        json={"topic_id": 999, "tahap_kesukaran": "mudah", "nama_peserta": "Ali"},
    )
    assert response.status_code == 404
    assert response.json()["detail"]["kod"] == "SUMBER_TIDAK_DIJUMPAI"


def test_mula_percubaan_soalan_tidak_mencukupi_400(client):
    seed_questions(client, count=9)
    response = client.post(
        "/api/v1/quiz-attempts",
        json={"topic_id": 1, "tahap_kesukaran": "mudah", "nama_peserta": "Ali"},
    )
    assert response.status_code == 400
    body = response.json()["detail"]
    assert body["kod"] == "SOALAN_TIDAK_MENCUKUPI"
    assert "9" in body["mesej"]


def test_mula_percubaan_nama_kosong_422(client):
    response = client.post(
        "/api/v1/quiz-attempts",
        json={"topic_id": 1, "tahap_kesukaran": "mudah", "nama_peserta": "   "},
    )
    assert response.status_code == 422


def test_hantar_semua_betul_skor_10(client):
    seeded = seed_questions(client, count=10)
    attempt = start_attempt(client)
    response = submit(client, attempt, jawapan_semua_betul(attempt, seeded))
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "selesai"
    assert data["skor"] == 10
    assert data["masa_hantar"] is not None
    assert len(data["perincian"]) == 10
    assert all(item["adalah_betul"] for item in data["perincian"])
    assert all(item["jawapan_betul"] is not None for item in data["perincian"])


def test_hantar_semua_salah_skor_0(client):
    seeded = seed_questions(client, count=10)
    attempt = start_attempt(client)
    response = submit(client, attempt, jawapan_semua_salah(attempt, seeded))
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["skor"] == 0
    assert all(not item["adalah_betul"] for item in data["perincian"])


def test_hantar_tamper_medan_adalah_betul_422(client):
    seeded = seed_questions(client, count=10)
    attempt = start_attempt(client)
    jawapan = jawapan_semua_betul(attempt, seeded)
    jawapan[0]["adalah_betul"] = True
    jawapan[0]["skor"] = 10
    response = submit(client, attempt, jawapan)
    assert response.status_code == 422


def test_hantar_9_jawapan_422(client):
    seeded = seed_questions(client, count=10)
    attempt = start_attempt(client)
    jawapan = jawapan_semua_betul(attempt, seeded)[:9]
    response = submit(client, attempt, jawapan)
    assert response.status_code == 422


def test_hantar_question_id_duplikasi_422(client):
    seeded = seed_questions(client, count=10)
    attempt = start_attempt(client)
    jawapan = jawapan_semua_betul(attempt, seeded)
    jawapan[1]["question_id"] = jawapan[0]["question_id"]
    response = submit(client, attempt, jawapan)
    assert response.status_code == 422


def test_hantar_question_id_bukan_milik_percubaan_400(client):
    seeded = seed_questions(client, count=10)
    attempt = start_attempt(client)
    jawapan = jawapan_semua_betul(attempt, seeded)
    jawapan[0]["question_id"] = 99999
    response = submit(client, attempt, jawapan)
    assert response.status_code == 400
    assert response.json()["detail"]["kod"] == "SOALAN_TIDAK_SAH"


def test_hantar_dua_kali_409(client):
    seeded = seed_questions(client, count=10)
    attempt = start_attempt(client)
    response = submit(client, attempt, jawapan_semua_betul(attempt, seeded))
    assert response.status_code == 200
    response = submit(client, attempt, jawapan_semua_betul(attempt, seeded))
    assert response.status_code == 409
    assert response.json()["detail"]["kod"] == "KUIZ_TELAH_SELESAI"


def test_get_result_selesai(client):
    seeded = seed_questions(client, count=10)
    attempt = start_attempt(client)
    submit(client, attempt, jawapan_semua_betul(attempt, seeded))

    response = client.get(f"/api/v1/quiz-attempts/{attempt['id']}/result")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "selesai"
    assert data["skor"] == 10
    assert len(data["perincian"]) == 10


def test_get_result_dalam_progres_409(client):
    seed_questions(client, count=10)
    attempt = start_attempt(client)
    response = client.get(f"/api/v1/quiz-attempts/{attempt['id']}/result")
    assert response.status_code == 409
    assert response.json()["detail"]["kod"] == "KUIZ_BELUM_SELESAI"


def test_get_result_dalam_progres_dengan_include_questions(client):
    seed_questions(client, count=10)
    attempt = start_attempt(client)
    response = client.get(
        f"/api/v1/quiz-attempts/{attempt['id']}/result",
        params={"include_questions": "true"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "dalam_progres"
    assert len(data["soalan"]) == 10
    assert "jawapan_betul" not in str(data)


def test_get_result_tidak_wujud_404(client):
    response = client.get("/api/v1/quiz-attempts/999/result")
    assert response.status_code == 404


def test_isi_kosong_normalisasi_huruf_dan_ruang(client):
    seeded = seed_questions(client, count=10, jenis="isi_tempat_kosong")
    attempt = start_attempt(client)
    jawapan = jawapan_semua_betul(attempt, seeded)
    teks_betul = jawapan[0]["data_jawapan"]["teks"]
    jawapan[0]["data_jawapan"] = {"teks": f"  {teks_betul.upper()}  "}
    response = submit(client, attempt, jawapan)
    assert response.json()["data"]["perincian"][0]["adalah_betul"] is True


def test_isi_kosong_teks_kosong_salah(client):
    seeded = seed_questions(client, count=10, jenis="isi_tempat_kosong")
    attempt = start_attempt(client)
    jawapan = jawapan_semua_betul(attempt, seeded)
    jawapan[0]["data_jawapan"] = {"teks": "   "}
    response = submit(client, attempt, jawapan)
    data = response.json()["data"]
    assert data["perincian"][0]["adalah_betul"] is False
    assert data["skor"] == 9


def test_betul_salah_penggredan(client):
    seeded = seed_questions(client, count=10, jenis="betul_salah")
    attempt = start_attempt(client)
    jawapan = jawapan_semua_betul(attempt, seeded)
    jawapan[0]["data_jawapan"] = {"nilai": not jawapan[0]["data_jawapan"]["nilai"]}
    response = submit(client, attempt, jawapan)
    data = response.json()["data"]
    assert data["perincian"][0]["adalah_betul"] is False
    assert data["skor"] == 9


def test_padanan_set_tertib_diabaikan(client):
    seeded = seed_questions(client, count=10, jenis="padanan")
    attempt = start_attempt(client)
    jawapan = jawapan_semua_betul(attempt, seeded)
    pasangan = jawapan[0]["data_jawapan"]["pasangan"]
    jawapan[0]["data_jawapan"] = {"pasangan": list(reversed(pasangan))}
    response = submit(client, attempt, jawapan)
    assert response.json()["data"]["perincian"][0]["adalah_betul"] is True


def test_padanan_pasangan_salah_false(client):
    seeded = seed_questions(client, count=10, jenis="padanan")
    attempt = start_attempt(client)
    jawapan = jawapan_semua_betul(attempt, seeded)
    pasangan = jawapan[0]["data_jawapan"]["pasangan"]
    jawapan[0]["data_jawapan"] = {
        "pasangan": [
            {"kiri": pasangan[0]["kiri"], "kanan": pasangan[1]["kanan"]},
            {"kiri": pasangan[1]["kiri"], "kanan": pasangan[0]["kanan"]},
        ]
    }
    response = submit(client, attempt, jawapan)
    data = response.json()["data"]
    assert data["perincian"][0]["adalah_betul"] is False
    assert data["skor"] == 9


def test_senarai_attempts_penapis(client):
    seeded = seed_questions(client, count=10)
    attempt = start_attempt(client, nama_peserta="Ali")
    submit(client, attempt, jawapan_semua_betul(attempt, seeded))
    start_attempt(client, nama_peserta="Siti")

    response = client.get(
        "/api/v1/quiz-attempts",
        params={"participant_name": "ali", "status": "selesai"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["total_items"] == 1
    assert body["data"][0]["nama_peserta"] == "Ali"
    assert body["data"][0]["skor"] == 10
    assert body["data"][0]["topic_nama"] == "Nombor dan Operasi"

    response = client.get("/api/v1/quiz-attempts")
    assert response.json()["meta"]["total_items"] == 2


def test_result_soalan_dipadam_papar_placeholder(client):
    seeded = seed_questions(client, count=10)
    attempt = start_attempt(client)
    submit(client, attempt, jawapan_semua_betul(attempt, seeded))

    soalan_ids = [s["id"] for s in attempt["soalan"]]
    for question_id in soalan_ids:
        client.delete(f"/api/v1/questions/{question_id}")

    response = client.get(f"/api/v1/quiz-attempts/{attempt['id']}/result")
    assert response.status_code == 200
    perincian = response.json()["data"]["perincian"]
    assert all(item["teks_soalan"] == "Soalan telah dipadam" for item in perincian)
    assert all(item["jawapan_betul"] is None for item in perincian)
    assert all(item["jawapan_murid"] is not None for item in perincian)