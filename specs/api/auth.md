# Auth API

## Status

Accepted

## Purpose

Define the authentication contract: login, logout, current session, and password change. Sessions follow ADR 0006: DB-backed revocable sessions with a BFF cookie relay.

All endpoints are reached through the Next.js BFF, which forwards only the `sk_quiz_sesi` cookie upstream and relays `set-cookie` downstream.

## Authentication Model

- Session token: 32 random bytes generated at login. The raw token is carried by the `sk_quiz_sesi` cookie. Only its SHA-256 hash is stored in the `sessions` table.
- Cookie attributes: `HttpOnly`, `SameSite=Lax`, `Secure` in production.
- Lifecycle: 24 hour idle timeout, 30 day absolute lifetime, sliding renewal on activity.
- Error distinction: `401 SESI_TAMAT` for missing, expired, or revoked sessions; `403 AKAUN_TIDAK_AKTIF` for deactivated accounts; `403 TIADA_KEBENARAN` for valid sessions without permission.

## Error Envelope

All errors use the shared envelope:

```json
{
  "detail": {
    "mesej": "Kelayakan tidak sah.",
    "kod": "KELAYAKAN_TIDAK_SAH"
  }
}
```

---

## POST /auth/login

### Purpose

Authenticate a user and create a session.

### Authentication

Public.

### Request

Body:

```json
{
  "username": "ahmad.ali",
  "kata_laluan": "rahasia123"
}
```

### Response

Success `200`. Sets the `sk_quiz_sesi` cookie. Returns the session user:

```json
{
  "data": {
    "id": 12,
    "username": "ahmad.ali",
    "nama_first": "Ahmad",
    "nama_last": "bin Ali",
    "role": "murid",
    "mesti_tukar_kata_laluan": true,
    "kelas": {
      "id": 3,
      "nama": "6 Bijak",
      "darjah": 6
    }
  }
}
```

`kelas` is present only when `role` is `murid`.

### Error Shapes

- `401 KELAYAKAN_TIDAK_SAH`: wrong username or password. The response is identical for both cases. No user enumeration.
- `403 AKAUN_TIDAK_AKTIF`: the account exists but `aktif` is false.

### Validation Rules

- `username`: required, non-blank, trimmed.
- `kata_laluan`: required, non-blank.

### Notes

- Login never distinguishes between unknown username and wrong password.
- `mesti_tukar_kata_laluan` tells the client whether the user must change the password before using the app.

---

## POST /auth/logout

### Purpose

Revoke the current session and clear the session cookie.

### Authentication

Session required. Any role.

### Request

No body.

### Response

Success `204 No Content`. The session is marked `revoked_at` and the `sk_quiz_sesi` cookie is cleared.

### Error Shapes

- `401 SESI_TAMAT`: session missing, expired, or revoked.

### Notes

- Logout revokes only the current session. Other sessions of the same user stay valid.

---

## GET /auth/me

### Purpose

Return the current session user.

### Authentication

Session required. Any role.

### Request

No params, no body.

### Response

Success `200`:

```json
{
  "data": {
    "id": 12,
    "username": "ahmad.ali",
    "nama_first": "Ahmad",
    "nama_last": "bin Ali",
    "role": "murid",
    "mesti_tukar_kata_laluan": false,
    "kelas": {
      "id": 3,
      "nama": "6 Bijak",
      "darjah": 6
    }
  }
}
```

`kelas` is present only when `role` is `murid`.

### Error Shapes

- `401 SESI_TAMAT`: session missing, expired, or revoked.
- `403 AKAUN_TIDAK_AKTIF`: account deactivated after session creation.

### Notes

- Successful access renews `last_seen_at` (sliding renewal).
- The frontend uses this endpoint to hydrate session state after page load.

---

## POST /auth/change-password

### Purpose

Change the password for the current user.

### Authentication

Session required. Any role.

### Request

Body:

```json
{
  "kata_laluan_semasa": "rahasia123",
  "kata_laluan_baru": "rahasia456"
}
```

### Response

Success `200`. The password hash is updated with Argon2 via `pwdlib`, `mesti_tukar_kata_laluan` is cleared, and all other sessions of the user are revoked. The current session stays valid.

### Error Shapes

- `401 SESI_TAMAT`: session missing, expired, or revoked.
- `403 AKAUN_TIDAK_AKTIF`: account deactivated.
- `401 KELAYAKAN_TIDAK_SAH`: `kata_laluan_semasa` does not match.
- `400`: validation failure on `kata_laluan_baru` (blank or below the server password policy).

### Validation Rules

- `kata_laluan_semasa`: required, non-blank.
- `kata_laluan_baru`: required, non-blank, constrained by the server password policy.

### Notes

- Revoking other sessions forces devices using the old password out.
- This endpoint is the required path for users with `mesti_tukar_kata_laluan=true`.