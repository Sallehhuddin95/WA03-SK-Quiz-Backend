# Quiz Attempts API

## Status

Accepted

## Purpose

Define the quiz attempt contract: start, list, result, submit, and staff preview. This spec covers existing behavior plus the authentication delta: attempts are linked to the logged-in murid, and `nama_peserta` is derived server-side.

## Permission and Scope Model

- `murid`: `attempt:create`, `attempt:submit`, `attempt:read_own`. Self-scoped to own attempts.
- `admin`: `attempt:read_all`, `attempt:preview`. Scoped to own plus shared classes.
- `super_admin`: `attempt:read_all`, `attempt:preview`. Unbounded.

## Error Envelope

All errors use the shared envelope:

```json
{
  "detail": {
    "mesej": "Kuiz ini telah dihantar.",
    "kod": "KUIZ_TELAH_SELESAI"
  }
}
```

---

## POST /quiz-attempts

### Purpose

Start a quiz attempt for the logged-in murid.

### Authentication

`require_permission("attempt:create")`. Murid only.

### Request

Body:

```json
{
  "topic_id": 3,
  "tahap_kesukaran": "sederhana"
}
```

### Response

Success `201`:

```json
{
  "data": {
    "id": 42,
    "topic_id": 3,
    "topic_nama": "Pecahan",
    "tahap_kesukaran": "sederhana",
    "nama_peserta": "Ahmad bin Ali",
    "status": "dalam_progres",
    "skor": null,
    "jumlah_soalan": 10,
    "masa_mula": "2026-08-25T09:00:00Z",
    "masa_hantar": null,
    "soalan": [
      {
        "id": 101,
        "jenis_soalan": "aneka_pilihan",
        "teks_soalan": "Berapakah 1/2 + 1/4?",
        "pilihan": {
          "A": "1/4",
          "B": "3/4",
          "C": "1/8",
          "D": "2/6"
        }
      }
    ]
  }
}
```

### Error Shapes

- `401 SESI_TAMAT`.
- `403 AKAUN_TIDAK_AKTIF`.
- `403 TIADA_KEBENARAN`: caller is not `murid`.
- `400 SOALAN_TIDAK_MENCUKUPI`: not enough active questions for the topic and difficulty.
- `400`: validation failure.

### Validation Rules

- `topic_id`: required, positive integer.
- `tahap_kesukaran`: required, one of `mudah`, `sederhana`, `sukar`.
- `nama_peserta` is not accepted in the input. It is derived server-side from the murid's `nama_first` and `nama_last`.
- The attempt is linked to the murid's `user_id`.
- The response question shape excludes answer fields, matching the existing `QuestionSummaryResponse`.

### Contract Change

`nama_peserta` was removed from the request body and `user_id` linkage was added. This is a breaking contract change. It is accepted because the frontend and backend ship together; see `docs/shared/versioning.md` Section 4 for the coordinated-deployment rule.

---

## GET /quiz-attempts

### Purpose

List quiz attempts.

### Authentication

`require_permission("attempt:read_own")` for murid, `require_permission("attempt:read_all")` for staff.

### Request

Query params:

- `topic_id`: optional filter.
- `difficulty`: optional filter, one of `mudah`, `sederhana`, `sukar`.
- `participant_name`: optional search on `nama_peserta`. Staff only; ignored for murid.
- `status`: optional filter (`dalam_progres`, `selesai`).
- `page`, `page_size`: pagination.

### Response

Success `200`:

```json
{
  "data": [
    {
      "id": 42,
      "topic_id": 3,
      "topic_nama": "Pecahan",
      "tahap_kesukaran": "sederhana",
      "nama_peserta": "Ahmad bin Ali",
      "status": "selesai",
      "skor": 8,
      "jumlah_soalan": 10,
      "masa_mula": "2026-08-25T09:00:00Z",
      "masa_hantar": "2026-08-25T09:12:00Z",
      "created_at": "2026-08-25T09:00:00Z",
      "updated_at": "2026-08-25T09:12:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total_items": 1,
    "total_pages": 1
  }
}
```

### Error Shapes

- `401 SESI_TAMAT`.
- `403 AKAUN_TIDAK_AKTIF`.
- `403 TIADA_KEBENARAN`: permission missing.

### Validation Rules

- Murid callers see own attempts only. `participant_name` is ignored; the query is scoped to the murid's `user_id`.
- Staff callers see attempts whose murid belongs to a visible class: own plus shared for `admin`, all for `super_admin`.
- `participant_name` search is available to staff for finding attempts across visible classes.

---

## GET /quiz-attempts/{id}/result

### Purpose

Return the result of one attempt, or the in-progress state with questions.

### Authentication

`require_permission("attempt:read_own")` for murid, `require_permission("attempt:read_all")` for staff.

### Request

Path: `id` (attempt id).

Query params:

- `include_questions`: `true` returns the resume shape with questions for in-progress attempts.

### Response

Success `200`. `AttemptResultResponse` for submitted attempts, `AttemptResumeResponse` for in-progress attempts when `include_questions` is true.

### Error Shapes

- `401 SESI_TAMAT`.
- `403 AKAUN_TIDAK_AKTIF`.
- `403 TIADA_KEBENARAN`: the attempt belongs to another murid or falls outside the staff caller's visible scope.
- `404 SUMBER_TIDAK_DIJUMPAI`: attempt does not exist.
- `409 KUIZ_BELUM_SELESAI`: result requested for an in-progress attempt without `include_questions`.

### Validation Rules

- Murid callers can read own attempts only.
- Staff callers can read attempts whose murid belongs to a visible class.

---

## POST /quiz-attempts/{id}/submit

### Purpose

Submit answers for an attempt.

### Authentication

`require_permission("attempt:submit")`. Murid only.

### Request

Path: `id` (attempt id).

Body:

```json
{
  "jawapan": [
    {
      "question_id": 101,
      "data_jawapan": {
        "pilihan": "B"
      }
    }
  ]
}
```

`jawapan` contains exactly 10 items with unique `question_id` values, matching the existing `SubmitAttemptRequest`.

### Response

Success `200`. Same shape as the existing `AttemptResultResponse`.

### Error Shapes

- `401 SESI_TAMAT`.
- `403 AKAUN_TIDAK_AKTIF`.
- `403 TIADA_KEBENARAN`: caller is not `murid`, or the attempt belongs to another murid.
- `404 SUMBER_TIDAK_DIJUMPAI`: attempt does not exist.
- `409 KUIZ_TELAH_SELESAI`: attempt already submitted.
- `400 SOALAN_TIDAK_SAH`: a `question_id` does not belong to this attempt.
- `400`: validation failure.

### Validation Rules

- Murid callers can submit own attempts only.
- Submission is idempotent-safe: submitting a submitted attempt returns `KUIZ_TELAH_SELESAI`.

---

## GET /kuiz/pratonton

### Purpose

Staff preview of quiz questions without answers.

### Authentication

`require_permission("attempt:preview")`. `super_admin` and `admin`.

### Request

Query params:

- `topic_id`: required. A single topic is always selected; there is no "semua topik" option.
- `tahap_kesukaran`: optional, one of `mudah`, `sederhana`, `sukar`. When omitted, the query spans all difficulty levels for the topic. This is the "semua" (all) case.

### Response

Success `200`:

```json
{
  "data": [
    {
      "id": 101,
      "jenis_soalan": "aneka_pilihan",
      "teks_soalan": "Berapakah 1/2 + 1/4?",
      "pilihan": {
        "A": "1/4",
        "B": "3/4",
        "C": "1/8",
        "D": "2/6"
      }
    }
  ]
}
```

Up to 10 questions. When `tahap_kesukaran` is set, selection rules match a real attempt for that difficulty. When it is omitted, questions are drawn across every difficulty level for the topic. Answer fields are never included.

### Error Shapes

- `401 SESI_TAMAT`.
- `403 AKAUN_TIDAK_AKTIF`.
- `403 TIADA_KEBENARAN`: permission missing.
- `400 SOALAN_TIDAK_MENCUKUPI`: fewer than 10 active questions for the topic within the selected scope. When `tahap_kesukaran` is omitted, the count spans all difficulty levels.

### Validation Rules

- This endpoint backs the staff student-view preview. It never creates an attempt and never records answers.
- Preview is not impersonation: no session identity changes, and no attempt rows are created.
- An omitted `tahap_kesukaran` is the "semua" case. It selects questions across all difficulty levels for the given topic, not questions with a NULL difficulty.