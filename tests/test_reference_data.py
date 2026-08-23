def test_senarai_subjects(client):
    response = client.get("/api/v1/subjects")
    assert response.status_code == 200
    data = response.json()["data"]
    assert [s["nama"] for s in data] == ["Matematik"]
    assert data[0]["id"] == 1


def test_senarai_tahun_subject(client):
    response = client.get("/api/v1/subjects/1/tahun")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data == [{"id": 1, "subject_id": 1, "nama": "Tahun 6"}]


def test_tahun_subject_tidak_wujud_404(client):
    response = client.get("/api/v1/subjects/999/tahun")
    assert response.status_code == 404
    body = response.json()
    assert body["detail"]["kod"] == "SUMBER_TIDAK_DIJUMPAI"
    assert body["detail"]["mesej"] == "Mata pelajaran tidak dijumpai."


def test_senarai_topics(client):
    response = client.get("/api/v1/tahun/1/topics")
    assert response.status_code == 200
    data = response.json()["data"]
    assert [t["nama"] for t in data] == [
        "Nombor dan Operasi",
        "Ukuran dan Geometri",
        "Pengurusan Data",
    ]
    assert data[0]["tahun_id"] == 1


def test_topics_tahun_tidak_wujud_404(client):
    response = client.get("/api/v1/tahun/999/topics")
    assert response.status_code == 404
    assert response.json()["detail"]["kod"] == "SUMBER_TIDAK_DIJUMPAI"
    assert response.json()["detail"]["mesej"] == "Tahun tidak dijumpai."