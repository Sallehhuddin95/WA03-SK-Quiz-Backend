# 0006 Use DB-Backed Sessions with BFF Cookie Relay

## Status

Accepted

## Context

ADR 0003 established server-managed sessions as the default authentication model for web applications. It did not settle the concrete mechanism: how sessions are stored, how the cookie is shaped, how the Next.js BFF participates, or how passwords are hashed.

Without this decision, each contributor could pick a different implementation. JWT with a client refresh loop, signed cookies without revocation, or client-side token handling would each be defensible in isolation and mutually incompatible in practice.

The system also has a BFF in front of FastAPI. Its role in session handling must be explicit, otherwise the BFF becomes a second security authority by accident.

## Decision

### DB-Backed Revocable Sessions

DB-backed revocable sessions are the session mechanism under ADR 0003.

- On login, the server generates a session token of 32 random bytes.
- Only the SHA-256 hash of the token is stored in the `sessions` table. The raw token is never stored in the database.
- The raw token is carried by the `sk_quiz_sesi` cookie: `HttpOnly`, `SameSite=Lax`, `Secure` in production.
- Idle timeout is 24 hours, tracked by `last_seen_at`. Absolute lifetime is 30 days, tracked by `expires_at`. Authenticated activity renews `last_seen_at` (sliding renewal). Expired sessions are rejected.
- Logout revokes the session by setting `revoked_at`. Password change and password reset revoke sessions. Revoked sessions are rejected.

FastAPI is the sole session owner. It creates, validates, renews, and revokes sessions. No other component decides whether a session is valid.

### BFF Cookie Relay

The Next.js BFF is a transport relay, not a security authority.

- BFF route handlers forward only the `sk_quiz_sesi` cookie upstream. No other client cookies are forwarded.
- Upstream `set-cookie` headers are relayed downstream unchanged.
- The BFF never reads, interprets, or validates session contents. It does not decide whether a request is authenticated.

### Password Hashing

Passwords are hashed with Argon2 via `pwdlib`. Plain-text passwords are never stored or logged.

## Consequences

Benefits:

- sessions are revocable: logout, password change, password reset, and account deactivation take effect immediately
- no client-side token storage, refresh logic, or token lifecycle code
- one trust boundary: only FastAPI validates sessions
- opaque tokens keep the BFF simple and free of auth logic

Costs and tradeoffs:

- every authenticated request performs a session lookup against the database
- the BFF must preserve cookie relay discipline (forward only the session cookie, relay `set-cookie`)
- sessions are stateful server state, so any future horizontal scaling must share the database

## Alternatives Considered

### Stateless JWT Sessions

Rejected because revocation requires a blocklist or short expiry plus refresh logic, adding complexity without a benefit for this system. ADR 0003 already rejects client-side token handling as the default.

### Signed Cookies Without Database State

Rejected because sessions could not be revoked before their expiry date, which breaks logout, password change, and account deactivation behavior.

### Redis-Backed Sessions

Rejected as an extra infrastructure dependency. PostgreSQL is already the system of record, and the session table does not need a separate cache tier at this scale.