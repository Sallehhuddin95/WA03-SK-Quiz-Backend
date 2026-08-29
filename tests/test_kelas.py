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


def payload_kelas(**ubah):
    payload = {"nama": "6 Bijak", "darjah": 6}
    payload.update(ubah)
    return payload


def test_super_admin_cipta_kelas_201(super_client):
    response = super_client.post("/api/v1/kelas", json=payload_kelas())
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["nama"] == "6 Bijak"
    assert data["darjah"] == 6
    assert data["guru_owners"] == []
    assert data["shared_with"] == []


def test_admin_tidak_boleh_cipta_kelas_403(client, user_factory):
    user_factory(username="guru.a", role="admin")
    login(client, "guru.a")
    response = client.post("/api/v1/kelas", json=payload_kelas())
    assert response.status_code == 403
    assert response.json()["detail"]["kod"] == "TIADA_KEBENARAN"


def test_murid_tidak_boleh_cipta_kelas_403(client, user_factory):
    user_factory(username="murid.test", role="murid")
    login(client, "murid.test")
    response = client.post("/api/v1/kelas", json=payload_kelas())
    assert response.status_code == 403


def test_cipta_kelas_duplikat_409(super_client):
    super_client.post("/api/v1/kelas", json=payload_kelas())
    response = super_client.post("/api/v1/kelas", json=payload_kelas())
    assert response.status_code == 409
    assert response.json()["detail"]["kod"] == "KONFLIK_SUMBER"


def test_kemaskini_kelas(super_client):
    created = super_client.post("/api/v1/kelas", json=payload_kelas()).json()["data"]
    response = super_client.patch(
        f"/api/v1/kelas/{created['id']}",
        json={"nama": "6 Cerdas"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["nama"] == "6 Cerdas"
    assert data["darjah"] == 6


def test_kemaskini_kelas_duplikat_409(super_client):
    super_client.post("/api/v1/kelas", json=payload_kelas())
    kedua = super_client.post(
        "/api/v1/kelas", json=payload_kelas(nama="5 Cerdas", darjah=5)
    ).json()["data"]
    response = super_client.patch(
        f"/api/v1/kelas/{kedua['id']}",
        json={"nama": "6 Bijak", "darjah": 6},
    )
    assert response.status_code == 409


def test_guru_lihat_kelas_own_dan_shared(
    super_client, guru_a, guru_b, kelas_factory, assign_owner
):
    kelas_a = kelas_factory(nama="6 Bijak", darjah=6)
    kelas_b = kelas_factory(nama="5 Cerdas", darjah=5)
    assign_owner(guru_id=guru_a.id, kelas_id=kelas_a.id)
    assign_owner(guru_id=guru_b.id, kelas_id=kelas_b.id)

    super_client.put(
        f"/api/v1/kelas/{kelas_a.id}/share",
        json={"guru_ids": [guru_b.id]},
    )

    guru_b_client = auth_client(app, "guru.b")
    response = guru_b_client.get("/api/v1/kelas")
    assert response.status_code == 200
    data = response.json()["data"]
    assert [k["id"] for k in data] == [kelas_a.id, kelas_b.id]

    kelas_a_item = next(k for k in data if k["id"] == kelas_a.id)
    assert [g["id"] for g in kelas_a_item["guru_owners"]] == [guru_a.id]
    assert [g["id"] for g in kelas_a_item["shared_with"]] == [guru_b.id]


def test_super_admin_lihat_semua_kelas(super_client, kelas_factory):
    kelas_factory(nama="6 Bijak", darjah=6)
    kelas_factory(nama="5 Cerdas", darjah=5)
    response = super_client.get("/api/v1/kelas")
    assert response.status_code == 200
    assert len(response.json()["data"]) == 2


def test_share_kelas_oleh_pemilik(
    super_client, guru_a, guru_b, kelas_factory, assign_owner
):
    kelas_a = kelas_factory(nama="6 Bijak", darjah=6)
    assign_owner(guru_id=guru_a.id, kelas_id=kelas_a.id)

    guru_a_client = auth_client(app, "guru.a")
    response = guru_a_client.put(
        f"/api/v1/kelas/{kelas_a.id}/share",
        json={"guru_ids": [guru_b.id]},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert [g["id"] for g in data["shared_with"]] == [guru_b.id]


def test_share_kelas_oleh_bukan_pemilik_403(
    guru_a, guru_b, kelas_factory, assign_owner
):
    kelas_a = kelas_factory(nama="6 Bijak", darjah=6)
    assign_owner(guru_id=guru_a.id, kelas_id=kelas_a.id)

    guru_b_client = auth_client(app, "guru.b")
    response = guru_b_client.put(
        f"/api/v1/kelas/{kelas_a.id}/share",
        json={"guru_ids": [guru_a.id]},
    )
    assert response.status_code == 403
    assert response.json()["detail"]["kod"] == "TIADA_KEBENARAN"


def test_share_kelas_kepada_pemilik_409(
    super_client, guru_a, kelas_factory, assign_owner
):
    kelas_a = kelas_factory(nama="6 Bijak", darjah=6)
    assign_owner(guru_id=guru_a.id, kelas_id=kelas_a.id)

    response = super_client.put(
        f"/api/v1/kelas/{kelas_a.id}/share",
        json={"guru_ids": [guru_a.id]},
    )
    assert response.status_code == 409
    assert response.json()["detail"]["kod"] == "KONFLIK_SUMBER"


def test_share_kelas_kepada_murid_400(
    super_client, guru_a, user_factory, kelas_factory, assign_owner
):
    kelas_a = kelas_factory(nama="6 Bijak", darjah=6)
    assign_owner(guru_id=guru_a.id, kelas_id=kelas_a.id)
    murid = user_factory(username="murid.test", role="murid")

    response = super_client.put(
        f"/api/v1/kelas/{kelas_a.id}/share",
        json={"guru_ids": [murid.id]},
    )
    assert response.status_code == 400
    assert response.json()["detail"]["kod"] == "DATA_TIDAK_SAH"


def test_share_kelas_senarai_kosong_kosongkan(
    super_client, guru_a, guru_b, kelas_factory, assign_owner
):
    kelas_a = kelas_factory(nama="6 Bijak", darjah=6)
    assign_owner(guru_id=guru_a.id, kelas_id=kelas_a.id)
    super_client.put(
        f"/api/v1/kelas/{kelas_a.id}/share",
        json={"guru_ids": [guru_b.id]},
    )
    response = super_client.put(
        f"/api/v1/kelas/{kelas_a.id}/share",
        json={"guru_ids": []},
    )
    assert response.status_code == 200
    assert response.json()["data"]["shared_with"] == []


def test_share_kelas_baca_sahaja(
    super_client,
    guru_a,
    guru_b,
    user_factory,
    kelas_factory,
    assign_owner,
):
    kelas_a = kelas_factory(nama="6 Bijak", darjah=6)
    assign_owner(guru_id=guru_a.id, kelas_id=kelas_a.id)
    super_client.put(
        f"/api/v1/kelas/{kelas_a.id}/share",
        json={"guru_ids": [guru_b.id]},
    )
    murid = user_factory(
        username="ahmad.ali",
        role="murid",
        nama_first="Ahmad",
        nama_last="bin Ali",
        kelas_id=kelas_a.id,
    )

    guru_b_client = auth_client(app, "guru.b")

    # guru B boleh lihat murid dalam kelas kongsi (skop baca)
    response = guru_b_client.get(f"/api/v1/users/{murid.id}")
    assert response.status_code == 200

    # guru B tidak boleh cipta murid dalam kelas kongsi
    response = guru_b_client.post(
        "/api/v1/users",
        json={
            "nama_first": "Ahmad",
            "nama_last": "bin Ali",
            "username": "ahmad.ali2",
            "role": "murid",
            "kata_laluan_awal": "rahasia123",
            "kelas_id": kelas_a.id,
        },
    )
    assert response.status_code == 403
    assert response.json()["detail"]["kod"] == "TIADA_KEBENARAN"

    # guru B tidak boleh reset kata laluan murid dalam kelas kongsi
    response = guru_b_client.post(
        f"/api/v1/users/{murid.id}/reset-password",
        json={"kata_laluan_baru": "baru12345"},
    )
    assert response.status_code == 403
    assert response.json()["detail"]["kod"] == "TIADA_KEBENARAN"


def test_senarai_gurus_direktori(super_client, guru_a, guru_b, user_factory):
    murid = user_factory(username="murid.test", role="murid")
    guru_tidak_aktif = user_factory(
        username="guru.tidak.aktif", role="admin", aktif=False
    )

    response = super_client.get("/api/v1/gurus")
    assert response.status_code == 200
    data = response.json()["data"]
    ids = [g["id"] for g in data]
    assert guru_a.id in ids
    assert guru_b.id in ids
    assert murid.id not in ids
    assert guru_tidak_aktif.id not in ids
    assert all(set(guru.keys()) == {"id", "nama_first", "nama_last"} for guru in data)


def test_senarai_gurus_murid_403(client, user_factory):
    user_factory(username="murid.test", role="murid")
    login(client, "murid.test")
    response = client.get("/api/v1/gurus")
    assert response.status_code == 403
    assert response.json()["detail"]["kod"] == "TIADA_KEBENARAN"