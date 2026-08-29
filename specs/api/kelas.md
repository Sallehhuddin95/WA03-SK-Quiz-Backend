# Kelas API

## Status

Accepted

## Purpose

Define the class management and sharing contract: list, create, update, share, and the guru directory for the share picker. Enforced through the kelas scoping model in ADR 0007.

## Ownership and Sharing Model

- `guru_kelas` records which guru owns which class. Own classes form the `own` scope.
- `kelas_share` records read-only grants. Shared classes form the `shared` scope.
- `admin` sees own plus shared classes. `super_admin` sees all classes.
- Shared classes are read-only for the receiving guru. No write operation applies to shared-class data.

## Error Envelope

All errors use the shared envelope:

```json
{
  "detail": {
    "mesej": "Sumber tidak dijumpai.",
    "kod": "SUMBER_TIDAK_DIJUMPAI"
  }
}
```

---

## GET /kelas

### Purpose

List classes visible to the caller.

### Authentication

`require_permission("kelas:read")`.

### Request

No params.

### Response

Success `200`:

```json
{
  "data": [
    {
      "id": 3,
      "nama": "6 Bijak",
      "darjah": 6,
      "guru_owners": [
        {
          "id": 5,
          "nama_first": "Siti",
          "nama_last": "Aminah"
        }
      ],
      "shared_with": [
        {
          "id": 7,
          "nama_first": "Raj",
          "nama_last": "Kumar"
        }
      ]
    }
  ]
}
```

### Error Shapes

- `401 SESI_TAMAT`.
- `403 AKAUN_TIDAK_AKTIF`.
- `403 TIADA_KEBENARAN`: permission missing.

### Validation Rules

- `admin` sees own plus shared classes only.
- `super_admin` sees all classes.
- Items include owner gurus (`guru_kelas`) and receiving gurus (`kelas_share`) as minimal projections (`id`, `nama_first`, `nama_last`).
- Class counts are small; no pagination is used.

---

## POST /kelas

### Purpose

Create a class.

### Authentication

`require_permission("kelas:create")`. `super_admin` only.

### Request

Body:

```json
{
  "nama": "6 Bijak",
  "darjah": 6
}
```

### Response

Success `201`. Same item shape as `GET /kelas`.

### Error Shapes

- `401 SESI_TAMAT`.
- `403 AKAUN_TIDAK_AKTIF`.
- `403 TIADA_KEBENARAN`: caller is not `super_admin`.
- `409 KONFLIK_SUMBER`: a class with the same `darjah` and `nama` already exists.
- `400`: validation failure.

### Validation Rules

- `nama`: required, non-blank.
- `darjah`: required, integer 1 to 6.
- A `(darjah, nama)` pair must be unique.

---

## PATCH /kelas/{id}

### Purpose

Rename a class or change its darjah.

### Authentication

`require_permission("kelas:update")`. `super_admin` only.

### Request

Body, all fields optional:

```json
{
  "nama": "6 Cerdas",
  "darjah": 6
}
```

### Response

Success `200`. Same item shape as `GET /kelas`.

### Error Shapes

- `401 SESI_TAMAT`.
- `403 AKAUN_TIDAK_AKTIF`.
- `403 TIADA_KEBENARAN`: caller is not `super_admin`.
- `404 SUMBER_TIDAK_DIJUMPAI`: class does not exist.
- `409 KONFLIK_SUMBER`: the new `(darjah, nama)` pair collides with another class.
- `400`: validation failure.

### Validation Rules

- `nama` and `darjah` follow the same rules as `POST /kelas`.
- Ownership records (`guru_kelas`) and shares (`kelas_share`) survive renames; they reference the class id.

---

## PUT /kelas/{id}/share

### Purpose

Replace the read-only share list of a class.

### Authentication

`require_permission("kelas:share")`. The owning guru or `super_admin`.

### Request

Body:

```json
{
  "guru_ids": [7, 8]
}
```

### Response

Success `200`. Same item shape as `GET /kelas`, with the updated `shared_with` list.

### Error Shapes

- `401 SESI_TAMAT`.
- `403 AKAUN_TIDAK_AKTIF`.
- `403 TIADA_KEBENARAN`: caller is not `super_admin` and is not an owner of this class.
- `404 SUMBER_TIDAK_DIJUMPAI`: class does not exist.
- `409 KONFLIK_SUMBER`: `guru_ids` includes a guru who already owns the class.
- `400`: `guru_ids` includes an id that does not reference an active `admin` account.

### Validation Rules

- `guru_ids` replaces the whole share list. An empty list clears all shares.
- Owners of the class cannot be share targets; they already have full access as owners.
- Receivers are always `admin` accounts. Share grants are read-only: roster and attempts/results visibility, no writes.
- A guru who shares a class still sees it in `shared_with` of the owning guru's view; the receiving guru sees it as part of the own-plus-shared scope in `GET /kelas`.

---

## GET /gurus

### Purpose

List gurus for the share picker.

### Authentication

`require_permission("guru:directory")`. `super_admin` and `admin`.

### Request

No params.

### Response

Success `200`:

```json
{
  "data": [
    {
      "id": 5,
      "nama_first": "Siti",
      "nama_last": "Aminah"
    }
  ]
}
```

### Error Shapes

- `401 SESI_TAMAT`.
- `403 AKAUN_TIDAK_AKTIF`.
- `403 TIADA_KEBENARAN`: permission missing.

### Validation Rules

- Returns active `admin` accounts only.
- Minimal projection: `id`, `nama_first`, `nama_last`. No usernames or role fields.
- Non-paginated; guru counts are small.