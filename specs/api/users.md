# Users API

## Status

Accepted

## Purpose

Define user management: create, list, read, update, reset password, and soft delete. Enforced through the RBAC and kelas scoping model in ADR 0007.

## Permission and Scope Model

- `super_admin` may manage `admin` and `murid` users, unbounded by class scope.
- `admin` may manage `murid` users only, bounded by kelas scope.
- Target-role whitelist on create: `super_admin` may create `admin` or `murid`; `admin` may create `murid` only.
- Scope on create, update, reset password, and delete: own classes only.
- Scope on read: own plus shared classes.
- Shared classes are read-only. No write operation applies to murid in shared classes.
- Scope or role violations return `403 TIADA_KEBENARAN`.

## Error Envelope

All errors use the shared envelope:

```json
{
  "detail": {
    "mesej": "Nama pengguna sudah wujud.",
    "kod": "NAMA_PENGGUNA_WUJUD"
  }
}
```

---

## POST /users

### Purpose

Create a user.

### Authentication

`require_permission("user:create")`.

### Request

Body:

```json
{
  "nama_first": "Ahmad",
  "nama_last": "bin Ali",
  "username": "ahmad.ali",
  "role": "murid",
  "kata_laluan_awal": "rahasia123",
  "kelas_id": 3
}
```

### Response

Success `201`:

```json
{
  "data": {
    "id": 12,
    "username": "ahmad.ali",
    "nama_first": "Ahmad",
    "nama_last": "bin Ali",
    "role": "murid",
    "aktif": true,
    "mesti_tukar_kata_laluan": true,
    "kelas_id": 3
  }
}
```

Accounts created by an admin start with `mesti_tukar_kata_laluan=true` because the password was assigned, not chosen.

### Error Shapes

- `401 SESI_TAMAT`: session missing, expired, or revoked.
- `403 AKAUN_TIDAK_AKTIF`: creator account deactivated.
- `403 TIADA_KEBENARAN`: role not in the creator's target whitelist, or `kelas_id` outside the creator's own scope.
- `409 NAMA_PENGGUNA_WUJUD`: username already exists.
- `400`: validation failure.

### Validation Rules

- `nama_first`: required, non-blank.
- `nama_last`: required, non-blank.
- `username`: required, free-form typed, unique. Trimmed.
- `role`: one of `admin`, `murid` for this endpoint. `super_admin` is never accepted; it is provisioned only by the bootstrap CLI.
- `kata_laluan_awal`: required, constrained by the server password policy.
- `kelas_id`: required for `murid`. Must be absent for `admin`.
- `kelas_id` for `admin` creators must be inside the creator's own scope. Tampering to another scope returns `403 TIADA_KEBENARAN`.

---

## GET /users

### Purpose

List users.

### Authentication

`require_permission("user:read")`.

### Request

Query params:

- `role`: optional filter, one of `super_admin`, `admin`, `murid`.
- `carian`: optional search on `nama_first`, `nama_last`, or `username`.
- `page`, `page_size`: pagination, same envelope as the existing paginated endpoints.

### Response

Success `200`:

```json
{
  "data": [
    {
      "id": 12,
      "username": "ahmad.ali",
      "nama_first": "Ahmad",
      "nama_last": "bin Ali",
      "role": "murid",
      "aktif": true,
      "mesti_tukar_kata_laluan": false,
      "kelas_id": 3
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

- `401 SESI_TAMAT`: session missing, expired, or revoked.
- `403 AKAUN_TIDAK_AKTIF`: account deactivated.
- `403 TIADA_KEBENARAN`: permission missing.

### Validation Rules

- `admin` callers see `murid` users in own plus shared classes only. Results are scoped server-side; the caller cannot widen the scope with filters.
- `super_admin` callers see all users.
- `carian` matches within the caller's visible scope.

---

## GET /users/{id}

### Purpose

Read one user.

### Authentication

`require_permission("user:read")`.

### Request

Path: `id` (user id).

### Response

Success `200`. Same user shape as `GET /users` items.

### Error Shapes

- `401 SESI_TAMAT`.
- `403 AKAUN_TIDAK_AKTIF`.
- `403 TIADA_KEBENARAN`: the user is outside the caller's scope.
- `404 SUMBER_TIDAK_DIJUMPAI`: user does not exist.

### Validation Rules

- `admin` callers may read `murid` users in own plus shared classes only. Reading an `admin` user or an out-of-scope `murid` returns `403 TIADA_KEBENARAN`.

---

## PATCH /users/{id}

### Purpose

Update a user.

### Authentication

`require_permission("user:update")`.

### Request

Body, all fields optional:

```json
{
  "nama_first": "Ahmad",
  "nama_last": "bin Ali",
  "aktif": false,
  "kelas_id": 4
}
```

### Response

Success `200`. Same user shape as `GET /users` items.

### Error Shapes

- `401 SESI_TAMAT`.
- `403 AKAUN_TIDAK_AKTIF`.
- `403 TIADA_KEBENARAN`: target outside the caller's own scope, or `kelas_id` outside the caller's own scope.
- `404 SUMBER_TIDAK_DIJUMPAI`: user does not exist.
- `409 NAMA_PENGGUNA_WUJUD`: not applicable here; username is not mutable via this endpoint.
- `400`: validation failure.

### Validation Rules

- `role` is not mutable via this endpoint.
- `username` is not mutable via this endpoint.
- `admin` callers may update `murid` users in own classes only. Shared-class murid are read-only; updating them returns `403 TIADA_KEBENARAN`.
- `kelas_id` changes must stay inside the caller's own scope.
- `aktif=false` is the soft-deactivate path and keeps history intact.

---

## POST /users/{id}/reset-password

### Purpose

Force a password change for a user.

### Authentication

`require_permission("user:reset_password")`.

### Request

Body:

```json
{
  "kata_laluan_baru": "rahasia123"
}
```

### Response

Success `200`. The password hash is updated, `mesti_tukar_kata_laluan` is set to `true`, and all sessions of the target user are revoked. The target user must log in again with the new password and change it before normal use.

### Error Shapes

- `401 SESI_TAMAT`.
- `403 AKAUN_TIDAK_AKTIF`.
- `403 TIADA_KEBENARAN`: target outside the caller's own scope.
- `404 SUMBER_TIDAK_DIJUMPAI`: user does not exist.
- `400`: validation failure on `kata_laluan_baru`.

### Validation Rules

- `admin` callers may reset passwords for `murid` users in own classes only.
- `super_admin` may reset for any `admin` or `murid` user.

---

## DELETE /users/{id}

### Purpose

Soft delete a user.

### Authentication

`require_permission("user:delete")`.

### Request

No body.

### Response

Success `204 No Content`. The user's `aktif` is set to `false`. No rows are removed.

### Error Shapes

- `401 SESI_TAMAT`.
- `403 AKAUN_TIDAK_AKTIF`.
- `403 TIADA_KEBENARAN`: target outside the caller's own scope.
- `404 SUMBER_TIDAK_DIJUMPAI`: user does not exist.

### Validation Rules

- `admin` callers may delete `murid` users in own classes only.
- Soft delete preserves history: quiz attempts keep `nama_peserta` snapshots and the `user_id` reference stays intact.
- There is no hard delete endpoint.

---

## POST /users/bulk-deactivate

### Purpose

Soft-delete multiple users in one call. The table's multi-select "nyahaktif" action calls this endpoint.

### Authentication

`require_permission("user:delete")`.

### Request

Body:

```json
{
  "ids": [12, 14, 17]
}
```

`ids` must contain at least 1 and at most 500 positive integers. No other fields are accepted.

### Response

Success `200`:

```json
{
  "data": {
    "mesej": "2 pengguna berjaya dinyahaktifkan.",
    "dinyahaktifkan": 2
  }
}
```

Each target user has `aktif` set to `false` and all of the target's sessions revoked, exactly like `DELETE /users/{id}`.

### Error Shapes

- `401 SESI_TAMAT`.
- `403 AKAUN_TIDAK_AKTIF`.
- `403 TIADA_KEBENARAN`: any target is outside the caller's own scope, or any target role is not `murid` for an `admin` caller.
- `404 SUMBER_TIDAK_DIJUMPAI`: any target id does not exist.
- `400`: validation failure.

### Validation Rules

- The call is atomic. If any target is out of scope or missing, the whole batch is rejected and nothing is changed.
- `admin` callers may deactivate `murid` users in own classes only. Shared-class murid are read-only.
- `super_admin` may deactivate any `admin` or `murid` user.
- Soft delete preserves history. There is no hard delete endpoint.