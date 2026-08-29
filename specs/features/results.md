# Results

## Status

Accepted

## Goal

Show quiz results to the right people: murid see their own history, staff see performance scoped to visible classes.

## Scope

- Murid history: own attempts only, no name input
- Guru prestasi: attempts from own plus shared classes
- Super admin prestasi: all attempts
- Staff preview mode for the student experience

## Out of Scope

- Exporting results
- Answer-level review by staff (covered by the attempt result contract)
- Class management

## Actors

- Murid: sees own attempt history
- Guru: sees performance for own and shared classes
- Super admin: sees performance for all classes

## Preconditions

- The user has a valid session
- The account is active
- The role matches the route group: `murid` for history, `admin` or `super_admin` for prestasi

## Main Flow

### Murid History

1. Murid opens the history page.
2. The app lists the murid's own attempts via `GET /quiz-attempts`, scoped to `user_id`.
3. The murid opens an attempt detail and sees the result per question.

### Staff Prestasi

1. Guru opens the prestasi page.
2. The app lists attempts for visible classes via `GET /quiz-attempts` with staff scope: own plus shared classes for a guru, all classes for a super admin.
3. The guru can search by participant name within the visible scope.
4. The guru opens an attempt detail to review answers.

### Staff Preview

1. Staff open the student view preview.
2. `GET /kuiz/pratonton` shows questions without answers.
3. The preview is clearly marked as a preview and cannot submit anything.

## Alternate Flows

### Empty History

A murid with no attempts sees an empty state with a call to start a first quiz.

### No Visible Classes

A guru who owns no classes and has no shares sees an empty prestasi state. This is not an error.

### Session Expiry

A `401 SESI_TAMAT` response redirects to `/login`.

## Error and Empty States

- `401 SESI_TAMAT`: session invalid. Redirect to `/login`.
- `403 TIADA_KEBENARAN`: the caller tries to read attempts outside their scope.
- `403 AKAUN_TIDAK_AKTIF`: deactivated account.
- Empty states exist for history, prestasi, and search results.

## Acceptance Criteria

- Murid history shows only own attempts; there is no name input on the murid history page.
- Guru prestasi shows attempts from own and shared classes only; murid from other classes are invisible.
- Super admin prestasi shows all attempts.
- Shared-class visibility is read-only: a guru can view rosters and results but cannot mutate anything through the results surface.
- Staff preview shows questions without answers and cannot be submitted.

## Related Specs

- API: `specs/api/auth.md`, `specs/api/quiz-attempts.md`
- Database: `specs/database/auth.md`
- Feature: `specs/features/quiz-taking.md`