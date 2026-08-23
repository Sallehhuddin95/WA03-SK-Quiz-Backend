PENANDA_TEMPAT_KOSONG = "______"


def normalisasi_teks(value: str) -> str:
    return value.strip().lower()


def grade_answer(
    jenis_soalan: str,
    jawapan_murid: dict | None,
    jawapan_betul: dict | None,
) -> bool:
    if jawapan_murid is None or jawapan_betul is None:
        return False

    if jenis_soalan == "aneka_pilihan":
        return jawapan_murid.get("pilihan") == jawapan_betul.get("pilihan")

    if jenis_soalan == "isi_tempat_kosong":
        teks = jawapan_murid.get("teks")
        if not isinstance(teks, str) or not teks.strip():
            return False
        murid = normalisasi_teks(teks)
        diterima = jawapan_betul.get("jawapan_diterima") or []
        return any(
            isinstance(jawapan, str)
            and normalisasi_teks(jawapan) == murid
            for jawapan in diterima
        )

    if jenis_soalan == "betul_salah":
        return jawapan_murid.get("nilai") == jawapan_betul.get("nilai")

    if jenis_soalan == "padanan":
        murid_pasangan = jawapan_murid.get("pasangan") or []
        betul_pasangan = jawapan_betul.get("pasangan") or []
        if len(murid_pasangan) != len(betul_pasangan):
            return False
        murid_set = {
            frozenset((pasangan.get("kiri"), pasangan.get("kanan")))
            for pasangan in murid_pasangan
        }
        betul_set = {
            frozenset((pasangan.get("kiri"), pasangan.get("kanan")))
            for pasangan in betul_pasangan
        }
        return murid_set == betul_set

    return False