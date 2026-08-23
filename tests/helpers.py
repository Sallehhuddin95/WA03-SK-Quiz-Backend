from fastapi.testclient import TestClient


def soalan_aneka(
    *,
    topic_id: int = 1,
    tahap: str = "mudah",
    status: str = "aktif",
    teks: str | None = None,
    pilihan: dict | None = None,
    jawapan_betul: dict | None = None,
) -> dict:
    return {
        "topic_id": topic_id,
        "jenis_soalan": "aneka_pilihan",
        "tahap_kesukaran": tahap,
        "status": status,
        "teks_soalan": teks or "Berapakah hasil darab 7 dan 8?",
        "pilihan": pilihan or {"A": "54", "B": "56", "C": "58", "D": "60"},
        "jawapan_betul": jawapan_betul or {"pilihan": "B"},
    }


def soalan_isi_kosong(
    *,
    topic_id: int = 1,
    tahap: str = "mudah",
    status: str = "aktif",
    teks: str | None = None,
    jawapan_diterima: list[str] | None = None,
) -> dict:
    return {
        "topic_id": topic_id,
        "jenis_soalan": "isi_tempat_kosong",
        "tahap_kesukaran": tahap,
        "status": status,
        "teks_soalan": teks or "Hasil tambah 25 dan 30 ialah ______.",
        "pilihan": None,
        "jawapan_betul": {
            "jawapan_diterima": jawapan_diterima or ["55", "55.0", "lima puluh lima"]
        },
    }


def soalan_betul_salah(
    *,
    topic_id: int = 1,
    tahap: str = "mudah",
    status: str = "aktif",
    teks: str | None = None,
    nilai: bool = True,
) -> dict:
    return {
        "topic_id": topic_id,
        "jenis_soalan": "betul_salah",
        "tahap_kesukaran": tahap,
        "status": status,
        "teks_soalan": teks or "Hasil darab 7 dan 8 ialah 56.",
        "pilihan": None,
        "jawapan_betul": {"nilai": nilai},
    }


def soalan_padanan(
    *,
    topic_id: int = 1,
    tahap: str = "mudah",
    status: str = "aktif",
    teks: str | None = None,
    pasangan: list[dict] | None = None,
) -> dict:
    return {
        "topic_id": topic_id,
        "jenis_soalan": "padanan",
        "tahap_kesukaran": tahap,
        "status": status,
        "teks_soalan": teks or "Padankan bentuk dengan bilangan sisi.",
        "pilihan": None,
        "jawapan_betul": {
            "pasangan": pasangan
            or [
                {"kiri": "Segi tiga", "kanan": "3 sisi"},
                {"kiri": "Segi empat", "kanan": "4 sisi"},
            ]
        },
    }


def create_question(client: TestClient, payload: dict) -> dict:
    response = client.post("/api/v1/questions", json=payload)
    assert response.status_code == 201, response.text
    return response.json()["data"]


def seed_questions(
    client: TestClient,
    *,
    count: int,
    topic_id: int = 1,
    tahap: str = "mudah",
    status: str = "aktif",
    jenis: str = "aneka_pilihan",
) -> list[dict]:
    questions = []
    for i in range(count):
        payload = soalan_aneka(
            topic_id=topic_id,
            tahap=tahap,
            status=status,
            teks=f"Soalan aneka nombor {i + 1}: Berapakah hasil 6 + {i}?",
            pilihan={"A": "1", "B": "2", "C": "3", "D": str(6 + i)},
            jawapan_betul={"pilihan": "D"},
        )
        if jenis == "isi_tempat_kosong":
            payload = soalan_isi_kosong(
                topic_id=topic_id,
                tahap=tahap,
                status=status,
                teks=f"Soalan isi nombor {i + 1}: Hasil 5 + {i} ialah ______.",
                jawapan_diterima=[str(5 + i)],
            )
        elif jenis == "betul_salah":
            payload = soalan_betul_salah(
                topic_id=topic_id,
                tahap=tahap,
                status=status,
                teks=f"Soalan betul/salah nombor {i + 1}: 1 + 1 = {2 + i}.",
                nilai=(i % 2 == 0),
            )
        elif jenis == "padanan":
            payload = soalan_padanan(
                topic_id=topic_id,
                tahap=tahap,
                status=status,
                teks=f"Soalan padanan nombor {i + 1}.",
                pasangan=[
                    {"kiri": f"A{i}", "kanan": f"X{i}"},
                    {"kiri": f"B{i}", "kanan": f"Y{i}"},
                ],
            )
        questions.append(create_question(client, payload))
    return questions


def start_attempt(
    client: TestClient,
    *,
    topic_id: int = 1,
    tahap: str = "mudah",
    nama_peserta: str = "Ali",
) -> dict:
    response = client.post(
        "/api/v1/quiz-attempts",
        json={
            "topic_id": topic_id,
            "tahap_kesukaran": tahap,
            "nama_peserta": nama_peserta,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]


def jawapan_betul_untuk(soalan: dict) -> dict:
    jenis = soalan["jenis_soalan"]
    if jenis == "aneka_pilihan":
        return {"pilihan": soalan["jawapan_betul"]["pilihan"]}
    if jenis == "isi_tempat_kosong":
        return {"teks": soalan["jawapan_betul"]["jawapan_diterima"][0]}
    if jenis == "betul_salah":
        return {"nilai": soalan["jawapan_betul"]["nilai"]}
    if jenis == "padanan":
        return {"pasangan": soalan["jawapan_betul"]["pasangan"]}
    return {}


def jawapan_salah_untuk(soalan: dict) -> dict:
    jenis = soalan["jenis_soalan"]
    if jenis == "aneka_pilihan":
        betul = soalan["jawapan_betul"]["pilihan"]
        salah = next(k for k in ("A", "B", "C", "D") if k != betul)
        return {"pilihan": salah}
    if jenis == "isi_tempat_kosong":
        return {"teks": "jawapan tidak tepat"}
    if jenis == "betul_salah":
        return {"nilai": not soalan["jawapan_betul"]["nilai"]}
    if jenis == "padanan":
        pasangan = soalan["jawapan_betul"]["pasangan"]
        return {"pasangan": [{"kiri": p["kiri"], "kanan": "salah"} for p in pasangan]}
    return {}