# Auth and RBAC Schema

## Status

Accepted

## Purpose

Define the persistence structures behind ADR 0006 (DB-backed sessions) and ADR 0007 (RBAC with kelas scoping): users, sessions, kelas, ownership, sharing, and the quiz attempt linkage.

## Entities or Tables

- `users`
- `sessions`
- `kelas`
- `guru_kelas`
- `kelas_share`
- `quiz_attempts` (delta: add `user_id`)

## Key Fields

### users

- `id`: primary key.
- `username`: unique, non-null. Free-form typed identifier used at login.
- `nama_first`: non-null.
- `nama_last`: non-null.
- `password_hash`: non-null. Argon2 hash via `pwdlib`.
- `role`: non-null, check constraint in (`super_admin`, `admin`, `murid`).
- `aktif`: non-null boolean, default `true`. Soft delete flag.
- `mesti_tukar_kata_laluan`: non-null boolean, default `false`. Set `true` for bootstrap, admin-created accounts, and password resets.
- `kelas_id`: nullable FK to `kelas`. Set only for `murid`.
- `created_by`: nullable FK to `users`. Set for accounts created by another user; null for the bootstrap super admin.
- `created_at`, `updated_at`: timestamps.

### sessions

- `id`: primary key.
- `token_hash`: SHA-256 hash of the session token, unique, non-null. The raw token is never stored.
- `user_id`: FK to `users`, non-null, cascade delete.
- `expires_at`: absolute session lifetime (30 days), non-null.
- `last_seen_at`: idle tracking (24 hour timeout), non-null. Updated on activity.
- `revoked_at`: nullable. Set on logout, password change, and password reset.
- `created_at`: timestamp.

### kelas

- `id`: primary key.
- `nama`: non-null.
- `darjah`: non-null integer, check constraint 1 to 6.
- `created_at`, `updated_at`: timestamps.
- A `(darjah, nama)` pair must be unique so a class is unambiguous in UI and API references.

### guru_kelas

- `guru_id`: FK to `users`, cascade delete.
- `kelas_id`: FK to `kelas`, cascade delete.
- Primary key: `(guru_id, kelas_id)`.
- Records which guru owns which class. This is the `own` scope.

### kelas_share

- `kelas_id`: FK to `kelas`, cascade delete.
- `shared_with_guru_id`: FK to `users`, cascade delete.
- Primary key: `(kelas_id, shared_with_guru_id)`.
- Records read-only grants. This is the `shared` scope.

### quiz_attempts

- Existing fields unchanged, including `nama_peserta` as a snapshot.
- New `user_id`: nullable FK to `users`, `ON DELETE SET NULL`, indexed. Links the attempt to the murid account.
- `nama_peserta` is kept so history display survives account renames and soft deletes.

## Relationships

- `users.kelas_id` to `kelas`: many murid to one class. Null for staff and super admin.
- `guru_kelas`: many-to-many between guru users and classes.
- `kelas_share`: many-to-many between classes and receiving gurus.
- `sessions.user_id` to `users`: one user to many sessions.
- `quiz_attempts.user_id` to `users`: one murid to many attempts.

## Constraints

- `username` unique. `sessions.token_hash` unique. `kelas` `(darjah, nama)` unique.
- `role` restricted by check constraint.
- `darjah` restricted to 1 to 6.
- `kelas_id` is set only for `murid`; staff and super admin rows keep it null.
- No hard deletes. User deactivation is `aktif=false`.
- Session revocation is `revoked_at` set, never row deletion during normal operation.

## Query or Access Notes

- Session lookup is by `token_hash`; the raw cookie value is hashed before querying.
- Visible class set for a guru: `guru_kelas` rows (own) union `kelas_share` rows where `shared_with_guru_id` is the guru (shared).
- Murid scope: `users.kelas_id`.
- Attempt scope for staff: `quiz_attempts.user_id` to `users.kelas_id` within the visible class set.
- Attempt scope for murid: `quiz_attempts.user_id = current user`.
- The `user_id` index on `quiz_attempts` serves both the murid history query and the staff scope join.

## Migration Notes

- New tables: `users`, `sessions`, `kelas`, `guru_kelas`, `kelas_share`.
- `quiz_attempts` gains a nullable `user_id` column with `ON DELETE SET NULL` and an index. Existing rows keep `nama_peserta` and get `user_id = null`.
- The bootstrap super admin must be created after `users` exists, via the CLI script, never via an API endpoint.
- No destructive migration: existing quiz attempt rows are preserved.