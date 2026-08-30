import pytest

from app.main import app
from tests.helpers import (
    auth_client,
    create_question,
    login,
    seed_questions,
    soalan_aneka,
    soalan_betul_salah,
    soalan_isi_kosong,
    soalan_padanan,
)


@pytest.fixture()
def admin_client(user_factory):
    user_factory(
        username="pentadbir",
        role="super_admin",
        nama_first="Pentadbir",
        nama_last="Sekolah",
    )
    return auth_client(app, "pentadbir")


def test_cipta_soalan_aneka_pilihan(admin_client):
    response = admin_client.post("/api/v1/questions", json=soalan_aneka())
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["id"] == 1
    assert data["topic_nama"] == "Nombor dan Operasi"
    assert data["jenis_soalan"] == "aneka_pilihan"
    assert data["status"] == "aktif"
    assert data["pilihan"]["A"] == "54"
    assert data["jawapan_betul"] == {"pilihan": "B"}


def test_cipta_soalan_tanpa_autentikasi_401(client):
    response = client.post("/api/v1/questions", json=soalan_aneka())
    assert response.status_code == 401
    assert response.json()["detail"]["kod"] == "SESI_TAMAT"


def test_cipta_soalan_murid_403(client, user_factory):
    user_factory(username="murid.test", role="murid")
    login(client, "murid.test")
    response = client.post("/api/v1/questions", json=soalan_aneka())
    assert response.status_code == 403
    assert response.json()["detail"]["kod"] == "TIADA_KEBENARAN"


def test_cipta_soalan_topic_tidak_wujud_404(admin_client):
    response = admin_client.post("/api/v1/questions", json=soalan_aneka(topic_id=999))
    assert response.status_code == 404
    body = response.json()["detail"]
    assert body["kod"] == "SUMBER_TIDAK_DIJUMPAI"
    assert body["mesej"] == "Topik tidak dijumpai."


def test_cipta_isi_kosong_tanpa_penanda_400(admin_client):
    payload = soalan_isi_kosong(teks="Hasil tambah 25 dan 30 ialah 55.")
    response = admin_client.post("/api/v1/questions", json=payload)
    assert response.status_code == 400
    body = response.json()["detail"]
    assert body["kod"] == "PENANDA_TEMPAT_KOSONG_TIADA"


def test_cipta_aneka_pilihan_tanpa_pilihan_C_422(admin_client):
    payload = soalan_aneka(pilihan={"A": "1", "B": "2", "C": "", "D": "4"})
    response = admin_client.post("/api/v1/questions", json=payload)
    assert response.status_code == 422
    body = response.json()["detail"]
    assert body["kod"] == "VALIDASI_GAGAL"
    assert "butiran" in body


def test_cipta_payload_tamper_medan_tambahan_422(admin_client):
    payload = soalan_aneka()
    payload["adalah_betul"] = True
    response = admin_client.post("/api/v1/questions", json=payload)
    assert response.status_code == 422


def test_cipta_padanan_duplikasi_kiri_422(admin_client):
    payload = soalan_padanan(
        pasangan=[
            {"kiri": "A", "kanan": "X"},
            {"kiri": "A", "kanan": "Y"},
        ]
    )
    response = admin_client.post("/api/v1/questions", json=payload)
    assert response.status_code == 422


def test_had_10_soalan_aktif_409(admin_client):
    seed_questions(admin_client, count=10)
    response = admin_client.post("/api/v1/questions", json=soalan_aneka())
    assert response.status_code == 409
    assert response.json()["detail"]["kod"] == "HAD_SOALAN_DICAPAI"


def test_had_10_dikira_mengikut_kombinasi(admin_client):
    seed_questions(admin_client, count=10)
    response = admin_client.post(
        "/api/v1/questions",
        json=soalan_aneka(tahap="sukar"),
    )
    assert response.status_code == 201


def test_nyahaktif_soalan_membenarkan_cipta_baru(admin_client):
    seed_questions(admin_client, count=10)
    response = admin_client.patch(
        "/api/v1/questions/1/status", json={"status": "tidak_aktif"}
    )
    assert response.status_code == 200
    response = admin_client.post("/api/v1/questions", json=soalan_aneka())
    assert response.status_code == 201


def test_senarai_soalan_penapis_dan_paginasi(admin_client):
    seed_questions(admin_client, count=10)
    admin_client.post("/api/v1/questions", json=soalan_aneka(tahap="sukar"))

    response = admin_client.get(
        "/api/v1/questions",
        params={"question_type": "aneka_pilihan", "page": 1, "page_size": 5},
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["data"]) == 5
    assert body["meta"] == {
        "page": 1,
        "page_size": 5,
        "total_items": 11,
        "total_pages": 3,
    }

    response = admin_client.get(
        "/api/v1/questions",
        params={"difficulty": "sukar", "status": "aktif"},
    )
    assert response.status_code == 200
    assert response.json()["meta"]["total_items"] == 1


def test_senarai_soalan_page_tidak_sah_400(admin_client):
    response = admin_client.get("/api/v1/questions", params={"page": 0})
    assert response.status_code == 400
    assert response.json()["detail"]["kod"] == "PARAMETER_TIDAK_SAH"


def test_get_soalan_by_id(admin_client):
    created = create_question(admin_client, soalan_aneka())
    response = admin_client.get(f"/api/v1/questions/{created['id']}")
    assert response.status_code == 200
    assert response.json()["data"]["id"] == created["id"]


def test_get_soalan_tidak_wujud_404(admin_client):
    response = admin_client.get("/api/v1/questions/999")
    assert response.status_code == 404
    assert response.json()["detail"]["kod"] == "SUMBER_TIDAK_DIJUMPAI"


def test_kemaskini_soalan_abaikan_jenis_soalan(admin_client):
    created = create_question(admin_client, soalan_aneka())
    payload = soalan_aneka(
        teks="Soalan dikemaskini: Berapakah 9 darab 8?",
        jawapan_betul={"pilihan": "A"},
    )
    payload["jenis_soalan"] = "betul_salah"
    response = admin_client.put(f"/api/v1/questions/{created['id']}", json=payload)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["jenis_soalan"] == "aneka_pilihan"
    assert data["teks_soalan"].startswith("Soalan dikemaskini")


def test_kemaskini_soalan_status_ke_aktif_melebihi_had_409(admin_client):
    seed_questions(admin_client, count=10)
    admin_client.patch("/api/v1/questions/1/status", json={"status": "tidak_aktif"})
    response = admin_client.post("/api/v1/questions", json=soalan_aneka())
    assert response.status_code == 201
    response = admin_client.patch("/api/v1/questions/1/status", json={"status": "aktif"})
    assert response.status_code == 409
    assert response.json()["detail"]["kod"] == "HAD_SOALAN_DICAPAI"


def test_padam_soalan(admin_client):
    created = create_question(admin_client, soalan_aneka())
    response = admin_client.delete(f"/api/v1/questions/{created['id']}")
    assert response.status_code == 200
    assert response.json()["data"] == {"mesej": "Soalan berjaya dipadam."}
    response = admin_client.get(f"/api/v1/questions/{created['id']}")
    assert response.status_code == 404


def test_padam_soalan_tidak_wujud_404(admin_client):
    response = admin_client.delete("/api/v1/questions/999")
    assert response.status_code == 404


def test_togol_status(admin_client):
    created = create_question(admin_client, soalan_aneka())
    response = admin_client.patch(
        f"/api/v1/questions/{created['id']}/status",
        json={"status": "tidak_aktif"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "tidak_aktif"

    response = admin_client.patch(
        f"/api/v1/questions/{created['id']}/status",
        json={"status": "aktif"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "aktif"


def test_togol_status_tidak_sah_422(admin_client):
    created = create_question(admin_client, soalan_aneka())
    response = admin_client.patch(
        f"/api/v1/questions/{created['id']}/status",
        json={"status": "entah"},
    )
    assert response.status_code == 422


def test_cipta_isi_kosong_valid(admin_client):
    response = admin_client.post("/api/v1/questions", json=soalan_isi_kosong())
    assert response.status_code == 201
    assert response.json()["data"]["pilihan"] is None


def test_cipta_betul_salah_valid(admin_client):
    response = admin_client.post("/api/v1/questions", json=soalan_betul_salah())
    assert response.status_code == 201
    assert response.json()["data"]["jawapan_betul"] == {"nilai": True}


def test_cipta_padanan_valid(admin_client):
    response = admin_client.post("/api/v1/questions", json=soalan_padanan())
    assert response.status_code == 201
    assert len(response.json()["data"]["jawapan_betul"]["pasangan"]) == 2


def test_bulk_delete_soalan(admin_client):
    created = create_question(admin_client, soalan_aneka())
    response = admin_client.post(
        "/api/v1/questions/bulk-delete",
        json={"ids": [created["id"]]},
    )
    assert response.status_code == 200
    assert response.json()["data"]["dipadam"] == 1
    response = admin_client.get(f"/api/v1/questions/{created['id']}")
    assert response.status_code == 404


def test_bulk_delete_skip_id_tidak_wujud(admin_client):
    create_question(admin_client, soalan_aneka())
    response = admin_client.post(
        "/api/v1/questions/bulk-delete",
        json={"ids": [1, 999]},
    )
    assert response.status_code == 200
    assert response.json()["data"]["dipadam"] == 1
    response = admin_client.get("/api/v1/questions/1")
    assert response.status_code == 404


def test_bulk_delete_tanpa_autentikasi_401(client):
    response = client.post(
        "/api/v1/questions/bulk-delete", json={"ids": [1]}
    )
    assert response.status_code == 401
    assert response.json()["detail"]["kod"] == "SESI_TAMAT"


def test_bulk_delete_murid_403(client, user_factory):
    user_factory(username="murid.test", role="murid")
    login(client, "murid.test")
    response = client.post(
        "/api/v1/questions/bulk-delete", json={"ids": [1]}
    )
    assert response.status_code == 403
    assert response.json()["detail"]["kod"] == "TIADA_KEBENARAN"


def test_bulk_delete_ids_kosong_422(admin_client):
    response = admin_client.post(
        "/api/v1/questions/bulk-delete", json={"ids": []}
    )
    assert response.status_code == 422
    assert response.json()["detail"]["kod"] == "VALIDASI_GAGAL"


def test_bulk_delete_ids_tidak_sah_422(admin_client):
    response = admin_client.post(
        "/api/v1/questions/bulk-delete", json={"ids": [0]}
    )
    assert response.status_code == 422


def test_bulk_delete_medan_tambahan_422(admin_client):
    response = admin_client.post(
        "/api/v1/questions/bulk-delete", json={"ids": [1], "label": "x"}
    )
    assert response.status_code == 422


def test_bulk_status_nyahaktifkan(admin_client):
    create_question(admin_client, soalan_aneka())
    create_question(admin_client, soalan_aneka())
    response = admin_client.post(
        "/api/v1/questions/bulk-status",
        json={"ids": [1, 2], "status": "tidak_aktif"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["dikemaskini"] == 2
    response = admin_client.get("/api/v1/questions/1")
    assert response.json()["data"]["status"] == "tidak_aktif"
    response = admin_client.get("/api/v1/questions/2")
    assert response.json()["data"]["status"] == "tidak_aktif"


def test_bulk_status_aktif_dalam_batas(admin_client):
    seed_questions(admin_client, count=9)
    inactive = create_question(admin_client, soalan_aneka(status="tidak_aktif"))
    response = admin_client.post(
        "/api/v1/questions/bulk-status",
        json={"ids": [inactive["id"]], "status": "aktif"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["dikemaskini"] == 1
    response = admin_client.get(f"/api/v1/questions/{inactive['id']}")
    assert response.json()["data"]["status"] == "aktif"


def test_bulk_status_aktif_melebihi_had_409(admin_client):
    seed_questions(admin_client, count=10)
    inactive = create_question(admin_client, soalan_aneka(status="tidak_aktif"))
    response = admin_client.post(
        "/api/v1/questions/bulk-status",
        json={"ids": [inactive["id"]], "status": "aktif"},
    )
    assert response.status_code == 409
    assert response.json()["detail"]["kod"] == "HAD_SOALAN_DICAPAI"
    # atomic call reject: soalaran kekal tidak aktif
    response = admin_client.get(f"/api/v1/questions/{inactive['id']}")
    assert response.json()["data"]["status"] == "tidak_aktif"


def test_bulk_status_aktif_kumpulan_melebihi_had_409(admin_client):
    seed_questions(admin_client, count=9)
    a = create_question(admin_client, soalan_aneka(status="tidak_aktif"))
    b = create_question(admin_client, soalan_aneka(status="tidak_aktif"))
    response = admin_client.post(
        "/api/v1/questions/bulk-status",
        json={"ids": [a["id"], b["id"]], "status": "aktif"},
    )
    assert response.status_code == 409
    assert response.json()["detail"]["kod"] == "HAD_SOALAN_DICAPAI"
    for q in (a, b):
        response = admin_client.get(f"/api/v1/questions/{q['id']}")
        assert response.json()["data"]["status"] == "tidak_aktif"


def test_bulk_status_medan_tambahan_422(admin_client):
    response = admin_client.post(
        "/api/v1/questions/bulk-status",
        json={"ids": [1], "status": "aktif", "label": "x"},
    )
    assert response.status_code == 422


def test_bulk_status_status_tidak_sah_422(admin_client):
    response = admin_client.post(
        "/api/v1/questions/bulk-status",
        json={"ids": [1], "status": "entah"},
    )
    assert response.status_code == 422