"""Seed 90 soalan MVP ke pangkalan data pembangunan.

Guna: uv run python scripts/seed_dev.py
Idempotent: soalan untuk kombinasi topik+tahap yang sudah wujud tidak diulang.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.models.question import Question

# Struktur: topik_id -> tahap -> senarai (jenis, teks, pilihan, jawapan_betul)
SOALAN: dict[int, dict[str, list[tuple[str, str, dict | None, dict]]]] = {
    1: {  # Nombor dan Operasi
        "mudah": [
            ("aneka_pilihan", "Berapakah hasil darab 7 dan 8?", {"A": "54", "B": "56", "C": "58", "D": "60"}, {"pilihan": "B"}),
            ("aneka_pilihan", "Hasil tambah 45 dan 37 ialah berapa?", {"A": "72", "B": "78", "C": "82", "D": "85"}, {"pilihan": "C"}),
            ("aneka_pilihan", "100 tolak 46 bersamaan dengan berapa?", {"A": "54", "B": "55", "C": "64", "D": "66"}, {"pilihan": "A"}),
            ("aneka_pilihan", "Apakah nilai tempat bagi angka 5 dalam nombor 5 243?", {"A": "sa", "B": "puluh", "C": "ratus", "D": "ribu"}, {"pilihan": "D"}),
            ("isi_tempat_kosong", "Hasil tambah 25 dan 30 ialah ______.", None, {"jawapan_diterima": ["55", "lima puluh lima"]}),
            ("isi_tempat_kosong", "Hasil darab 6 dan 9 ialah ______.", None, {"jawapan_diterima": ["54", "lima puluh empat"]}),
            ("betul_salah", "45 + 15 = 60.", None, {"nilai": True}),
            ("betul_salah", "100 - 30 = 80.", None, {"nilai": False}),
            ("padanan", "Padankan nombor dengan nilai tempat angkanya.", None, {"pasangan": [{"kiri": "Angka 4 dalam 245", "kanan": "puluh"}, {"kiri": "Angka 4 dalam 4 200", "kanan": "ribu"}]}),
            ("padanan", "Padankan operasi dengan jawapannya.", None, {"pasangan": [{"kiri": "3 x 5", "kanan": "15"}, {"kiri": "20 / 4", "kanan": "5"}]}),
        ],
        "sederhana": [
            ("aneka_pilihan", "456 + 278 = berapa?", {"A": "724", "B": "734", "C": "744", "D": "754"}, {"pilihan": "B"}),
            ("aneka_pilihan", "1 000 - 345 = berapa?", {"A": "645", "B": "655", "C": "665", "D": "675"}, {"pilihan": "B"}),
            ("aneka_pilihan", "45 x 12 = berapa?", {"A": "520", "B": "530", "C": "540", "D": "550"}, {"pilihan": "C"}),
            ("aneka_pilihan", "156 dibahagi dengan 4 ialah berapa?", {"A": "34", "B": "36", "C": "38", "D": "39"}, {"pilihan": "D"}),
            ("isi_tempat_kosong", "789 + 123 = ______.", None, {"jawapan_diterima": ["912", "sembilan ratus dua belas"]}),
            ("isi_tempat_kosong", "(5 + 3) x 4 = ______.", None, {"jawapan_diterima": ["32", "tiga puluh dua"]}),
            ("betul_salah", "0.5 lebih besar daripada 0.25.", None, {"nilai": True}),
            ("betul_salah", "1/2 lebih kecil daripada 1/3.", None, {"nilai": False}),
            ("padanan", "Padankan pecahan dengan perpuluhannya.", None, {"pasangan": [{"kiri": "1/2", "kanan": "0.5"}, {"kiri": "1/4", "kanan": "0.25"}]}),
            ("padanan", "Padankan nombor dengan faktor perdana pertamanya.", None, {"pasangan": [{"kiri": "Nombor 4", "kanan": "2"}, {"kiri": "Nombor 9", "kanan": "3"}]}),
        ],
        "sukar": [
            ("aneka_pilihan", "24 / (6 - 2) + 5 = berapa?", {"A": "11", "B": "12", "C": "13", "D": "14"}, {"pilihan": "A"}),
            ("aneka_pilihan", "25% daripada 80 ialah berapa?", {"A": "16", "B": "20", "C": "24", "D": "30"}, {"pilihan": "B"}),
            ("aneka_pilihan", "0.75 dalam bentuk pecahan termudah ialah apa?", {"A": "3/4", "B": "7/10", "C": "75/100", "D": "1/4"}, {"pilihan": "A"}),
            ("aneka_pilihan", "Faktor perdana bagi 36 ialah apa?", {"A": "1, 2, 3, 4, 6, 9, 12, 18, 36", "B": "2, 3", "C": "2, 2, 3, 3", "D": "4, 9"}, {"pilihan": "B"}),
            ("isi_tempat_kosong", "7 kuasa dua (7 x 7) = ______.", None, {"jawapan_diterima": ["49", "empat puluh sembilan"]}),
            ("isi_tempat_kosong", "8.5 + 2.75 = ______.", None, {"jawapan_diterima": ["11.25", "11.25"]}),
            ("betul_salah", "3 kuasa empat (3 x 3 x 3 x 3) = 81.", None, {"nilai": True}),
            ("betul_salah", "9 ialah faktor perdana bagi 27.", None, {"nilai": False}),
            ("padanan", "Padankan nombor dengan nilai tempat angkanya.", None, {"pasangan": [{"kiri": "Angka 3 dalam 1 305", "kanan": "ratus"}, {"kiri": "Angka 3 dalam 3 105", "kanan": "ribu"}]}),
            ("padanan", "Padankan perpuluhan dengan pecahan setaranya.", None, {"pasangan": [{"kiri": "0.5", "kanan": "1/2"}, {"kiri": "0.25", "kanan": "1/4"}]}),
        ],
    },
    2: {  # Ukuran dan Geometri
        "mudah": [
            ("aneka_pilihan", "1 kilometer bersamaan dengan berapa meter?", {"A": "10 m", "B": "100 m", "C": "1 000 m", "D": "10 000 m"}, {"pilihan": "C"}),
            ("aneka_pilihan", "Segi empat sama mempunyai berapa sisi?", {"A": "3", "B": "4", "C": "5", "D": "6"}, {"pilihan": "B"}),
            ("aneka_pilihan", "1 jam bersamaan dengan berapa minit?", {"A": "30", "B": "45", "C": "60", "D": "90"}, {"pilihan": "C"}),
            ("aneka_pilihan", "Unit yang paling sesuai untuk mengukur jisim sebuah buku ialah apa?", {"A": "gram", "B": "kilometer", "C": "liter", "D": "sentimeter"}, {"pilihan": "A"}),
            ("isi_tempat_kosong", "2 kilogram = ______ gram.", None, {"jawapan_diterima": ["2000", "2 000", "dua ribu"]}),
            ("isi_tempat_kosong", "Sebuah segi empat tepat mempunyai ______ sisi.", None, {"jawapan_diterima": ["4", "empat"]}),
            ("betul_salah", "Bentuk segi tiga mempunyai tiga sisi.", None, {"nilai": True}),
            ("betul_salah", "1 liter bersamaan dengan 100 mililiter.", None, {"nilai": False}),
            ("padanan", "Padankan bentuk dengan bilangan sisinya.", None, {"pasangan": [{"kiri": "Segi tiga", "kanan": "3 sisi"}, {"kiri": "Segi lima", "kanan": "5 sisi"}]}),
            ("padanan", "Padankan unit dengan ukuran yang sesuai.", None, {"pasangan": [{"kiri": "Masa", "kanan": "minit"}, {"kiri": "Panjang", "kanan": "sentimeter"}]}),
        ],
        "sederhana": [
            ("aneka_pilihan", "Perimeter segi empat tepat berukuran 5 cm x 3 cm ialah berapa?", {"A": "8 cm", "B": "15 cm", "C": "16 cm", "D": "30 cm"}, {"pilihan": "C"}),
            ("aneka_pilihan", "Luas segi empat sama dengan sisi 6 cm ialah berapa?", {"A": "12 cm persegi", "B": "24 cm persegi", "C": "36 cm persegi", "D": "48 cm persegi"}, {"pilihan": "C"}),
            ("aneka_pilihan", "Sudut tegak bersamaan dengan berapa darjah?", {"A": "45 darjah", "B": "90 darjah", "C": "120 darjah", "D": "180 darjah"}, {"pilihan": "B"}),
            ("aneka_pilihan", "3 kg 500 g bersamaan dengan berapa gram?", {"A": "3 050 g", "B": "3 500 g", "C": "3 505 g", "D": "5 300 g"}, {"pilihan": "B"}),
            ("isi_tempat_kosong", "Luas segi empat tepat berukuran 7 cm x 4 cm ialah ______ cm persegi.", None, {"jawapan_diterima": ["28", "dua puluh lapan"]}),
            ("isi_tempat_kosong", "1.5 kilometer = ______ meter.", None, {"jawapan_diterima": ["1500", "1 500", "seribu lima ratus"]}),
            ("betul_salah", "Semua sisi segi empat sama adalah sama panjang.", None, {"nilai": True}),
            ("betul_salah", "Perimeter ialah luas permukaan sesuatu bentuk.", None, {"nilai": False}),
            ("padanan", "Padankan bentuk dengan cirinya.", None, {"pasangan": [{"kiri": "Segi empat sama", "kanan": "4 sisi sama panjang"}, {"kiri": "Segi empat tepat", "kanan": "2 pasang sisi sama panjang"}]}),
            ("padanan", "Padankan ukuran dengan alat pengukurnya.", None, {"pasangan": [{"kiri": "Panjang meja", "kanan": "pembaris"}, {"kiri": "Jisim tepung", "kanan": "penimbang"}]}),
        ],
        "sukar": [
            ("aneka_pilihan", "Isipadu kuboid berukuran 5 cm x 4 cm x 3 cm ialah berapa?", {"A": "12 cm kubik", "B": "20 cm kubik", "C": "47 cm kubik", "D": "60 cm kubik"}, {"pilihan": "D"}),
            ("aneka_pilihan", "Luas segi empat tepat berukuran 12 cm x 8 cm ialah berapa?", {"A": "20 cm persegi", "B": "40 cm persegi", "C": "96 cm persegi", "D": "120 cm persegi"}, {"pilihan": "C"}),
            ("aneka_pilihan", "2.5 kg dalam gram ialah berapa?", {"A": "205 g", "B": "2 050 g", "C": "2 500 g", "D": "25 000 g"}, {"pilihan": "C"}),
            ("aneka_pilihan", "Sudut yang lebih besar daripada 90 darjah tetapi kurang daripada 180 darjah dipanggil apa?", {"A": "sudut tirus", "B": "sudut tegak", "C": "sudut cakah", "D": "sudut lurus"}, {"pilihan": "C"}),
            ("isi_tempat_kosong", "Isipadu kubus dengan sisi 5 cm ialah ______ cm kubik.", None, {"jawapan_diterima": ["125", "seratus dua puluh lima"]}),
            ("isi_tempat_kosong", "4 jam 30 minit = ______ minit.", None, {"jawapan_diterima": ["270", "dua ratus tujuh puluh"]}),
            ("betul_salah", "1 meter bersamaan dengan 100 sentimeter.", None, {"nilai": True}),
            ("betul_salah", "Luas diukur dalam unit kubik seperti cm kubik.", None, {"nilai": False}),
            ("padanan", "Padankan penukaran unit dengan jawapannya.", None, {"pasangan": [{"kiri": "2 m", "kanan": "200 cm"}, {"kiri": "3 kg", "kanan": "3 000 g"}]}),
            ("padanan", "Padankan sudut dengan namanya.", None, {"pasangan": [{"kiri": "Kurang daripada 90 darjah", "kanan": "sudut tirus"}, {"kiri": "180 darjah", "kanan": "sudut lurus"}]}),
        ],
    },
    3: {  # Pengurusan Data
        "mudah": [
            ("aneka_pilihan", "Carta menunjukkan 5 epal, 3 oren, dan 4 pisang. Buah yang paling banyak ialah apa?", {"A": "epal", "B": "oren", "C": "pisang", "D": "durian"}, {"pilihan": "A"}),
            ("aneka_pilihan", "Jadual menunjukkan 30 murid dalam 6A dan 28 murid dalam 6B. Jumlah murid ialah berapa?", {"A": "48", "B": "58", "C": "60", "D": "68"}, {"pilihan": "B"}),
            ("aneka_pilihan", "Dalam piktogram, 1 gambar mewakili 2 murid. 5 gambar mewakili berapa murid?", {"A": "5", "B": "7", "C": "10", "D": "15"}, {"pilihan": "C"}),
            ("aneka_pilihan", "Data: 2, 4, 6, 8. Nombor yang paling besar ialah apa?", {"A": "2", "B": "4", "C": "6", "D": "8"}, {"pilihan": "D"}),
            ("isi_tempat_kosong", "Data: 3, 5, 7, 9. Nilai yang paling kecil ialah ______.", None, {"jawapan_diterima": ["3", "tiga"]}),
            ("isi_tempat_kosong", "Dalam carta palang, palang yang paling tinggi menunjukkan nilai yang paling ______.", None, {"jawapan_diterima": ["banyak", "tinggi", "besar"]}),
            ("betul_salah", "Carta palang digunakan untuk membandingkan data.", None, {"nilai": True}),
            ("betul_salah", "Purata bagi 2 dan 4 ialah 4.", None, {"nilai": False}),
            ("padanan", "Padankan jenis carta dengan cara ia mewakili data.", None, {"pasangan": [{"kiri": "Piktogram", "kanan": "gambar mewakili data"}, {"kiri": "Carta palang", "kanan": "palang mewakili nilai"}]}),
            ("padanan", "Padankan istilah dengan nilainya dalam data 2, 4, 4, 6.", None, {"pasangan": [{"kiri": "Nilai paling kerap", "kanan": "4"}, {"kiri": "Nilai paling kecil", "kanan": "2"}]}),
        ],
        "sederhana": [
            ("aneka_pilihan", "Purata bagi 4, 6, dan 8 ialah berapa?", {"A": "5", "B": "6", "C": "7", "D": "9"}, {"pilihan": "B"}),
            ("aneka_pilihan", "Carta menunjukkan bintang: Ali 3, Mei 5, Chan 4, Dev 2. Siapa yang mendapat paling sedikit?", {"A": "Ali", "B": "Mei", "C": "Chan", "D": "Dev"}, {"pilihan": "D"}),
            ("aneka_pilihan", "Jadual jualan: Isnin 10, Selasa 15, Rabu 20. Jualan bertambah sebanyak berapa setiap hari?", {"A": "5", "B": "10", "C": "15", "D": "tidak tetap"}, {"pilihan": "A"}),
            ("aneka_pilihan", "Data markah: 60, 70, 80, 90, 100. Purata ialah berapa?", {"A": "70", "B": "75", "C": "80", "D": "85"}, {"pilihan": "C"}),
            ("isi_tempat_kosong", "Purata bagi 10, 20, dan 30 ialah ______.", None, {"jawapan_diterima": ["20", "dua puluh"]}),
            ("isi_tempat_kosong", "Data: 3, 7, 3, 9, 3. Nilai yang paling kerap muncul ialah ______.", None, {"jawapan_diterima": ["3", "tiga"]}),
            ("betul_salah", "Median ialah nilai di tengah-tengah data yang telah disusun.", None, {"nilai": True}),
            ("betul_salah", "Jadual hanya boleh menunjukkan dua nilai sahaja.", None, {"nilai": False}),
            ("padanan", "Padankan istilah dengan maksudnya.", None, {"pasangan": [{"kiri": "Purata", "kanan": "jumlah dibahagi bilangan"}, {"kiri": "Median", "kanan": "nilai tengah"}]}),
            ("padanan", "Dalam carta, 1 gambar mewakili 4 murid. Padankan gambar dengan bilangan murid.", None, {"pasangan": [{"kiri": "2 gambar", "kanan": "8 murid"}, {"kiri": "3 gambar", "kanan": "12 murid"}]}),
        ],
        "sukar": [
            ("aneka_pilihan", "Data: 2, 5, 5, 8, 10. Median ialah berapa?", {"A": "2", "B": "5", "C": "8", "D": "10"}, {"pilihan": "B"}),
            ("aneka_pilihan", "Data: 3, 3, 6, 8. Min (purata) ialah berapa?", {"A": "3", "B": "4", "C": "5", "D": "6"}, {"pilihan": "C"}),
            ("aneka_pilihan", "Kebarangkalian mendapat nombor genap apabila dadu 1 hingga 6 dilambung ialah berapa?", {"A": "1/6", "B": "1/3", "C": "1/2", "D": "2/3"}, {"pilihan": "C"}),
            ("aneka_pilihan", "Carta menunjukkan jualan 20, 25, 30, 35. Jumlah jualan ialah berapa?", {"A": "100", "B": "105", "C": "110", "D": "115"}, {"pilihan": "C"}),
            ("isi_tempat_kosong", "Data: 4, 8, 12, 16, 20. Purata ialah ______.", None, {"jawapan_diterima": ["12", "dua belas"]}),
            ("isi_tempat_kosong", "Data: 1, 2, 2, 3, 5. Mod ialah ______.", None, {"jawapan_diterima": ["2", "dua"]}),
            ("betul_salah", "Mod ialah nilai yang paling kerap muncul dalam data.", None, {"nilai": True}),
            ("betul_salah", "Kebarangkalian mendapat angka 7 pada dadu biasa ialah 1/6.", None, {"nilai": False}),
            ("padanan", "Padankan ukuran kecenderungan memusat dengan definisinya.", None, {"pasangan": [{"kiri": "Min", "kanan": "purata semua nilai"}, {"kiri": "Mod", "kanan": "nilai paling kerap"}]}),
            ("padanan", "Padankan kebarangkalian dengan peristiwa yang sesuai.", None, {"pasangan": [{"kiri": "Mustahil", "kanan": "hujan pada hari cerah"}, {"kiri": "Pasti", "kanan": "matahari terbit di timur"}]}),
        ],
    },
}


def main() -> None:
    db = SessionLocal()
    try:
        total_baru = 0
        for topic_id, tahap_map in SOALAN.items():
            for tahap, soalan_list in tahap_map.items():
                existing = (
                    db.query(Question)
                    .filter_by(topic_id=topic_id, tahap_kesukaran=tahap)
                    .count()
                )
                if existing:
                    print(
                        f"skip topik {topic_id} tahap {tahap}: "
                        f"{existing} soalan sudah wujud"
                    )
                    continue
                for jenis, teks, pilihan, jawapan_betul in soalan_list:
                    db.add(
                        Question(
                            topic_id=topic_id,
                            jenis_soalan=jenis,
                            tahap_kesukaran=tahap,
                            status="aktif",
                            teks_soalan=teks,
                            pilihan=pilihan,
                            jawapan_betul=jawapan_betul,
                        )
                    )
                db.commit()
                total_baru += len(soalan_list)
                print(f"seed topik {topic_id} tahap {tahap}: {len(soalan_list)} soalan")
        print(f"Selesai. {total_baru} soalan baru dimasukkan.")
    finally:
        db.close()


if __name__ == "__main__":
    main()