# Quiz Taking

## Status

Accepted

## Goal

Let a logged-in murid take a quiz: choose a topic and difficulty, answer 10 questions, submit, and see the result. Staff can preview the same questions without answers.

## Scope

- Login as a prerequisite; murid role only
- Topic and difficulty selection
- Quiz flow: 10 questions, navigation, submit dialog
- Pending attempt detection and continuation
- Result display after submit
- Staff preview of questions without answers

## Out of Scope

- Question bank management (admin side)
- Class and user management
- Answer review by staff

## Actors

- Murid: takes quizzes
- Guru and super admin: preview questions via the student view

## Preconditions

- The user has a valid session (`sk_quiz_sesi` cookie)
- The account is active
- The role is `murid` for taking quizzes
- The topic has enough active questions for the chosen difficulty

## Main Flow

1. Murid logs in. The name shown comes from the session, not from a form field.
2. Murid lands on the quiz home and selects a topic and difficulty.
3. The murid starts the quiz. `POST /quiz-attempts` creates the attempt with `user_id` linked to the murid and `nama_peserta` derived server-side.
4. The murid answers the 10 questions and submits. `POST /quiz-attempts/{id}/submit`.
5. The result view shows the score and per-question feedback.

## Alternate Flows

### Pending Attempt

If the murid already has a `dalam_progres` attempt for the same topic and difficulty, the app offers a choice: continue the existing attempt or start a new one.

### Session Expiry Mid-Quiz

If the session expires while taking a quiz, the app redirects to `/login`. The in-progress attempt is not lost; the murid can continue it after logging in again.

### Staff Preview

Staff open the student view preview for a topic. `GET /kuiz/pratonton` returns up to 10 questions without answers. No attempt is created and no answers are recorded.

### Password Change Required

If `mesti_tukar_kata_laluan` is true after login, the murid must change the password before entering the quiz flow.

## Error and Empty States

- `401 SESI_TAMAT`: session invalid. Redirect to `/login`.
- `403 TIADA_KEBENARAN`: role is not murid. The murid route group rejects staff.
- `400 SOALAN_TIDAK_MENCUKUPI`: not enough questions. Show a message that the topic has insufficient questions.
- `409 KUIZ_TELAH_SELESAI`: the attempt was already submitted. Prevent double submission.
- No pending attempts: start directly without the continue dialog.

## Acceptance Criteria

- The quiz selector has no name input field; the participant name comes from the session.
- Starting a quiz requires a valid murid session; staff roles receive `403 TIADA_KEBENARAN`.
- Attempts are linked to the murid's `user_id`, and the murid sees only own attempts in history.
- The staff preview shows questions without answers and never creates an attempt.
- A pending in-progress attempt for the same topic and difficulty triggers the continue-or-restart dialog.
- Session expiry during a quiz redirects to `/login` and preserves the in-progress attempt.

## Related Specs

- API: `specs/api/auth.md`, `specs/api/quiz-attempts.md`
- Database: `specs/database/auth.md`
- Feature: `specs/features/results.md`