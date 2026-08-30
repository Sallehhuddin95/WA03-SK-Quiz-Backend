import pytest

from app.main import app
from tests.helpers import auth_client, login


@pytest.fixture()
def super_client(user_factory):
    user_factory(
        username="pentadbir",
        role="super_admin",
        nama_first="Pentadbir",
        nama_last="Sekolah",
    )
    return auth_client(app, "pentadbir")


@pytest.fixture()
def guru_a_client(user_factory, kelas_factory, assign_owner):
    kelas = kelas_factory(nama="6 Bijak", darjah=6)
    guru = user_factory(
        username="guru.a",
        role="admin",
        nama_first="Siti",
        nama_last="Aminah",
    )
    assign_owner(guru_id=guru.id, kelas_id=kelas.id)
    client = auth_client(app, "guru.a")
    client.kelas_a = kelas
    client.guru_a = guru
    return client


@pytest.fixture()
def kelas_lain(kelas_factory):
    return kelas_factory(nama="5 Cerdas", darjah=5)


def payload_murid(**ubah):
    payload = {
        "nama_first": "Ahmad",
        "nama_last": "bin Ali",
        "username": "ahmad.ali",
        "role": "murid",
        "kata_laluan_awal": "rahasia123",
        "kelas_id": 1,
    }
    payload.update(ubah)
    return payload


def payload_admin(**ubah):
    payload = {
        "nama_first": "Siti",
        "nama_last": "Aminah",
        "username": "siti.aminah",
        "role": "admin",
        "kata_laluan_awal": "rahasia123",
    }
    payload.update(ubah)
    return payload


def test_super_admin_cipta_admin_201(super_client):
    response = super_client.post("/api/v1/users", json=payload_admin())
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["username"] == "siti.aminah"
    assert data["role"] == "admin"
    assert data["aktif"] is True
    assert data["mesti_tukar_kata_laluan"] is True
    assert data["kelas_id"] is None


def test_super_admin_cipta_murid_201(super_client, kelas_factory):
    kelas = kelas_factory(nama="6 Bijak", darjah=6)
    response = super_client.post(
        "/api/v1/users", json=payload_murid(kelas_id=kelas.id)
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["role"] == "murid"
    assert data["kelas_id"] == kelas.id


def test_admin_cipta_murid_dalam_kelas_sendiri_201(guru_a_client):
    response = guru_a_client.post(
        "/api/v1/users", json=payload_murid(kelas_id=guru_a_client.kelas_a.id)
    )
    assert response.status_code == 201


def test_admin_cipta_admin_403(guru_a_client):
    response = guru_a_client.post("/api/v1/users", json=payload_admin())
    assert response.status_code == 403
    assert response.json()["detail"]["kod"] == "TIADA_KEBENARAN"


def test_admin_cipta_super_admin_403(guru_a_client):
    response = guru_a_client.post(
        "/api/v1/users", json=payload_murid(role="super_admin")
    )
    assert response.status_code == 403
    assert response.json()["detail"]["kod"] == "TIADA_KEBENARAN"


def test_murid_cipta_pengguna_403(client, user_factory):
    user_factory(username="murid.test", role="murid")
    login(client, "murid.test")
    response = client.post("/api/v1/users", json=payload_murid())
    assert response.status_code == 403
    assert response.json()["detail"]["kod"] == "TIADA_KEBENARAN"


def test_username_duplicate_409(super_client, kelas_factory):
    kelas = kelas_factory(nama="6 Bijak", darjah=6)
    super_client.post("/api/v1/users", json=payload_murid(kelas_id=kelas.id))
    response = super_client.post(
        "/api/v1/users",
        json=payload_murid(
            username="AHMAD.ALI",
            nama_first="Orang",
            nama_last="Lain",
            kelas_id=kelas.id,
        ),
    )
    assert response.status_code == 409
    assert response.json()["detail"]["kod"] == "NAMA_PENGGUNA_WUJUD"


def test_murid_tanpa_kelas_400(super_client):
    response = super_client.post(
        "/api/v1/users",
        json=payload_murid(kelas_id=None),
    )
    assert response.status_code == 400
    assert response.json()["detail"]["kod"] == "DATA_TIDAK_SAH"


def test_admin_dengan_kelas_400(super_client):
    response = super_client.post(
        "/api/v1/users",
        json=payload_admin(kelas_id=1),
    )
    assert response.status_code == 400
    assert response.json()["detail"]["kod"] == "DATA_TIDAK_SAH"


def test_admin_cipta_murid_dalam_kelas_lain_403(guru_a_client, kelas_lain):
    response = guru_a_client.post(
        "/api/v1/users", json=payload_murid(kelas_id=kelas_lain.id)
    )
    assert response.status_code == 403
    assert response.json()["detail"]["kod"] == "TIADA_KEBENARAN"


def test_murid_kelas_tidak_wujud_404(super_client):
    response = super_client.post("/api/v1/users", json=payload_murid(kelas_id=999))
    assert response.status_code == 404
    assert response.json()["detail"]["kod"] == "SUMBER_TIDAK_DIJUMPAI"


def test_reset_password_paksa_tukar_dan_revoke_sesi(guru_a_client):
    response = guru_a_client.post(
        "/api/v1/users", json=payload_murid(kelas_id=guru_a_client.kelas_a.id)
    )
    murid_id = response.json()["data"]["id"]

    murid_client = auth_client(app, "ahmad.ali")
    response = murid_client.get("/api/v1/auth/me")
    assert response.status_code == 200

    response = guru_a_client.post(
        f"/api/v1/users/{murid_id}/reset-password",
        json={"kata_laluan_baru": "baru12345"},
    )
    assert response.status_code == 200

    # semua sesi murid direvoke
    response = murid_client.get("/api/v1/auth/me")
    assert response.status_code == 401

    # log masuk semula dengan kata laluan baru mesti tukar dahulu
    data = login(murid_client, "ahmad.ali", "baru12345")
    assert data["mesti_tukar_kata_laluan"] is True


def test_reset_password_luar_skop_403(guru_a_client, kelas_lain):
    # murid kelas lain di bawah guru lain
    response = guru_a_client.post(
        "/api/v1/users",
        json=payload_murid(kelas_id=kelas_lain.id, username="murid.luar"),
    )
    assert response.status_code == 403


def test_soft_delete_nyahaktif_dan_revoke(guru_a_client):
    response = guru_a_client.post(
        "/api/v1/users", json=payload_murid(kelas_id=guru_a_client.kelas_a.id)
    )
    murid_id = response.json()["data"]["id"]

    murid_client = auth_client(app, "ahmad.ali")
    response = guru_a_client.delete(f"/api/v1/users/{murid_id}")
    assert response.status_code == 204

    # sesi murid direvoke
    response = murid_client.get("/api/v1/auth/me")
    assert response.status_code == 401

    # log masuk disekat
    response = murid_client.post(
        "/api/v1/auth/login",
        json={"username": "ahmad.ali", "kata_laluan": "rahasia123"},
    )
    assert response.status_code == 403
    assert response.json()["detail"]["kod"] == "AKAUN_TIDAK_AKTIF"


def test_senarai_pengguna_skop_kelas(guru_a_client, kelas_lain, user_factory):
    guru_a_client.post(
        "/api/v1/users", json=payload_murid(kelas_id=guru_a_client.kelas_a.id)
    )
    user_factory(username="murid.luar", role="murid", kelas_id=kelas_lain.id)
    user_factory(username="guru.b", role="admin")

    response = guru_a_client.get("/api/v1/users")
    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["total_items"] == 1
    assert body["data"][0]["username"] == "ahmad.ali"
    assert body["data"][0]["kelas_id"] == guru_a_client.kelas_a.id


def test_super_admin_senarai_semua(super_client, guru_a_client):
    guru_a_client.post(
        "/api/v1/users", json=payload_murid(kelas_id=guru_a_client.kelas_a.id)
    )
    super_client.post("/api/v1/users", json=payload_admin())
    response = super_client.get("/api/v1/users")
    assert response.json()["meta"]["total_items"] == 4

    response = super_client.get("/api/v1/users", params={"role": "admin"})
    assert response.json()["meta"]["total_items"] == 2

    response = super_client.get("/api/v1/users", params={"carian": "ahmad"})
    assert response.json()["meta"]["total_items"] == 1


def test_get_pengguna_luar_skop_403(guru_a_client, kelas_lain, user_factory):
    murid_luar = user_factory(
        username="murid.luar", role="murid", kelas_id=kelas_lain.id
    )
    response = guru_a_client.get(f"/api/v1/users/{murid_luar.id}")
    assert response.status_code == 403
    assert response.json()["detail"]["kod"] == "TIADA_KEBENARAN"


def test_get_pengguna_admin_oleh_admin_403(guru_a_client, user_factory):
    guru_b = user_factory(username="guru.b", role="admin")
    response = guru_a_client.get(f"/api/v1/users/{guru_b.id}")
    assert response.status_code == 403
    assert response.json()["detail"]["kod"] == "TIADA_KEBENARAN"


def test_kemaskini_murid_skop_own_sahaja(guru_a_client, kelas_lain):
    response = guru_a_client.post(
        "/api/v1/users", json=payload_murid(kelas_id=guru_a_client.kelas_a.id)
    )
    murid_id = response.json()["data"]["id"]
    response = guru_a_client.patch(
        f"/api/v1/users/{murid_id}",
        json={"nama_first": "Ahmad", "nama_last": "bin Hassan"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["nama_last"] == "bin Hassan"

    # pindah kelas ke luar skop own -> 403
    response = guru_a_client.patch(
        f"/api/v1/users/{murid_id}",
        json={"kelas_id": kelas_lain.id},
    )
    assert response.status_code == 403
    assert response.json()["detail"]["kod"] == "TIADA_KEBENARAN"

    # role tidak boleh diubah: medan tambahan ditolak
    response = guru_a_client.patch(
        f"/api/v1/users/{murid_id}",
        json={"role": "admin"},
    )
    assert response.status_code == 422


def test_bulk_deactivate_murid_sendiri(guru_a_client):
    satu = guru_a_client.post(
        "/api/v1/users",
        json=payload_murid(
            username="murid.satu", kelas_id=guru_a_client.kelas_a.id
        ),
    ).json()["data"]
    dua = guru_a_client.post(
        "/api/v1/users",
        json=payload_murid(
            username="murid.dua", kelas_id=guru_a_client.kelas_a.id
        ),
    ).json()["data"]

    murid_satu = auth_client(app, "murid.satu")
    murid_dua = auth_client(app, "murid.dua")
    assert murid_satu.get("/api/v1/auth/me").status_code == 200
    assert murid_dua.get("/api/v1/auth/me").status_code == 200

    response = guru_a_client.post(
        "/api/v1/users/bulk-deactivate",
        json={"ids": [satu["id"], dua["id"]]},
    )
    assert response.status_code == 200
    assert response.json()["data"]["dinyahaktifkan"] == 2

    # sesi kedua-dua murid direvoke
    assert murid_satu.get("/api/v1/auth/me").status_code == 401
    assert murid_dua.get("/api/v1/auth/me").status_code == 401

    # log masuk disekat
    for username in ("murid.satu", "murid.dua"):
        assert murid_satu.post(
            "/api/v1/auth/login",
            json={"username": username, "kata_laluan": "rahasia123"},
        ).status_code == 403


def test_bulk_deactivate_luar_skop_403(guru_a_client, kelas_lain, user_factory):
    dalam = guru_a_client.post(
        "/api/v1/users",
        json=payload_murid(
            username="murid.dalam", kelas_id=guru_a_client.kelas_a.id
        ),
    ).json()["data"]
    luar = user_factory(
        username="murid.luar", role="murid", kelas_id=kelas_lain.id
    )

    response = guru_a_client.post(
        "/api/v1/users/bulk-deactivate",
        json={"ids": [dalam["id"], luar.id]},
    )
    assert response.status_code == 403
    assert response.json()["detail"]["kod"] == "TIADA_KEBENARAN"

    # atomic reject: murid dalam skop masih aktif
    response = guru_a_client.get(f"/api/v1/users/{dalam['id']}")
    assert response.json()["data"]["aktif"] is True


def test_bulk_deactivate_tidak_wujud_404(guru_a_client):
    response = guru_a_client.post(
        "/api/v1/users/bulk-deactivate", json={"ids": [999]}
    )
    assert response.status_code == 404
    assert response.json()["detail"]["kod"] == "SUMBER_TIDAK_DIJUMPAI"


def test_bulk_deactivate_admin_oleh_admin_403(guru_a_client, user_factory):
    guru_b = user_factory(username="guru.b", role="admin")
    response = guru_a_client.post(
        "/api/v1/users/bulk-deactivate", json={"ids": [guru_b.id]}
    )
    assert response.status_code == 403
    assert response.json()["detail"]["kod"] == "TIADA_KEBENARAN"


def test_bulk_deactivate_tanpa_autentikasi_401(client):
    response = client.post(
        "/api/v1/users/bulk-deactivate", json={"ids": [1]}
    )
    assert response.status_code == 401
    assert response.json()["detail"]["kod"] == "SESI_TAMAT"


def test_bulk_deactivate_murid_403(client, user_factory):
    user_factory(username="murid.test", role="murid")
    login(client, "murid.test")
    response = client.post(
        "/api/v1/users/bulk-deactivate", json={"ids": [1]}
    )
    assert response.status_code == 403
    assert response.json()["detail"]["kod"] == "TIADA_KEBENARAN"


def test_bulk_deactivate_ids_kosong_422(guru_a_client):
    response = guru_a_client.post(
        "/api/v1/users/bulk-deactivate", json={"ids": []}
    )
    assert response.status_code == 422
    assert response.json()["detail"]["kod"] == "VALIDASI_GAGAL"


def test_bulk_deactivate_medan_tambahan_422(guru_a_client):
    response = guru_a_client.post(
        "/api/v1/users/bulk-deactivate",
        json={"ids": [1], "status": "tidak_aktif"},
    )
    assert response.status_code == 422