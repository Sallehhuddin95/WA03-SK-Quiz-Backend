# 0007 Adopt RBAC with Kelas Scoping

## Status

Accepted

## Context

The system has three user groups: school administrators, teachers, and students. Access rules were previously undefined on the backend. The frontend used a client-side role picker and localStorage role storage, which is UX state, not access control.

The backend needs one authorization model that covers:

- user management (who can create, read, update, deactivate users)
- class ownership (which guru teaches which kelas)
- class sharing (read-only visibility across gurus)
- quiz attempt visibility (murid history, guru prestasi)

Staff also need a way to see the student experience without impersonating students, because murid routes and murid identity must stay exclusive to murid accounts.

## Decision

### Roles and Permissions

Three-role RBAC with a static, code-defined role to permission matrix.

Roles:

- `super_admin`: school administrator. Unbounded class scope.
- `admin`: guru (teacher). Class scope is bounded by ownership and sharing.
- `murid`: student. Self-scoped to own attempts.

Permissions are enforced through a permission-named dependency factory in FastAPI: `require_permission("user:read")`. Route handlers declare the permission they need; the dependency resolves role to permissions and rejects the request when the permission is missing.

Permission matrix:

| Permission          | super_admin | admin | murid |
| ------------------- | ----------- | ----- | ----- |
| `user:create`       | yes         | yes   | no    |
| `user:read`         | yes         | yes   | no    |
| `user:update`       | yes         | yes   | no    |
| `user:reset_password` | yes       | yes   | no    |
| `user:delete`       | yes         | yes   | no    |
| `kelas:create`      | yes         | no    | no    |
| `kelas:read`        | yes         | yes   | no    |
| `kelas:update`      | yes         | no    | no    |
| `kelas:share`       | yes         | yes   | no    |
| `guru:directory`    | yes         | yes   | no    |
| `attempt:create`    | no          | no    | yes   |
| `attempt:submit`    | no          | no    | yes   |
| `attempt:read_own`  | no          | no    | yes   |
| `attempt:read_all`  | yes         | yes   | no    |
| `attempt:preview`   | yes         | yes   | no    |

The matrix is additive: adding a permission later grants it to the roles listed, nothing more.

### Error Distinction

- `401 SESI_TAMAT`: session missing, expired, or revoked.
- `403 TIADA_KEBENARAN`: valid session, but the caller lacks the permission or the scope.
- `403 AKAUN_TIDAK_AKTIF`: account is deactivated (`aktif=false`).

Ownership and scope checks live in the service layer, not in route handlers. Routes declare permissions; services enforce who may touch which record.

### Kelas Scoping

- `kelas` is an entity with `darjah` (1-6) and `nama`.
- `guru_kelas` is a many-to-many ownership table: a guru teaches multiple classes.
- A murid has exactly one `kelas_id`.
- `super_admin` is unbounded; no scope filter applies.

Scope resolution uses a `KelasScope` resolver with two levels:

- `own`: classes where the guru is an owner via `guru_kelas`.
- `shared`: classes granted via `kelas_share`.

Permission to scope mapping:

- `user:create`, `user:update`, `user:reset_password`, `user:delete`: own only.
- `user:read`, `kelas:read`, `attempt:read_all`: own plus shared.

### Class Sharing

- `kelas_share` is a join table of `kelas_id` and `shared_with_guru_id`.
- The owning guru or `super_admin` shares a class read-only with other gurus.
- The receiving guru sees the roster and attempts/results for the shared class. No writes are allowed on shared classes.
- Sharing is managed with `PUT /kelas/{id}/share` taking a `guru_ids` list. An empty list removes all shares.

### Student View

Student view is an in-app mode, not impersonation.

- On the frontend, a sessionStorage-persisted Zustand UI state switches staff into the murid-style interface.
- Staff preview questions through `GET /kuiz/pratonton`, which returns up to 10 questions without answers.
- Murid routes stay murid-only. The backend never switches identity, and no staff session ever acts as a murid.

### Share Picker Permission

`guru:directory` is an additive permission granted to `super_admin` and `admin`. It exposes a minimal guru projection (`id`, `nama_first`, `nama_last`) for the share picker.

### Bootstrap

A CLI script creates the initial `super_admin` account with `mesti_tukar_kata_laluan=true`. No API endpoint creates `super_admin` accounts.

## Consequences

Benefits:

- one authorization model across all endpoints
- permission and scope rules are testable and reviewable in one place
- sharing is explicit, read-only, and revocable via the share list
- student view cannot become a privilege escalation path because sessions never change identity

Costs and tradeoffs:

- every staff-facing endpoint must declare its permission and scope
- share state needs UI management and clear read-only indicators on shared classes
- contributors must learn two concepts: permission names and kelas scope levels

## Alternatives Considered

### Client-Side Role Selection (Status Quo)

Rejected because a role stored in localStorage is UX state, not access control. It provides no server enforcement and cannot protect any endpoint.

### Per-Role Branching Inside Route Handlers

Rejected because it duplicates authorization rules across handlers and drifts over time. A centralized permission matrix keeps the rules in one place.

### Staff Impersonation of Murid Accounts

Rejected because it mixes identities, muddies audit trails, and turns a preview feature into a security-sensitive flow. The in-app student view with answer-free preview questions delivers the same value without touching identity.

### Per-User Hardcoded Class Lists

Rejected because it duplicates the two-level model that `guru_kelas` (ownership) and `kelas_share` (read-only grants) already express in one place.