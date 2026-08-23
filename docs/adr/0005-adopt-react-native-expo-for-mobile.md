# 0005 Adopt React Native (Expo) for Mobile

## Status

Accepted

## Context

The project is expanding beyond web frontend and backend to include a mobile client. Without an explicit decision, mobile work risks being bolted onto the existing web frontend structure, introducing a second competing pattern for rendering, navigation, and state management, or adopting an unrelated mobile stack that does not share conventions with the rest of the system.

## Decision

Mobile will be built with React Native using Expo (managed workflow), as a dedicated stack alongside web frontend and backend:

- Navigation: Expo Router (file-based), mirroring the route-first structure already used by the Next.js App Router on web.
- Server state: TanStack Query, the same library already used on web.
- Global/local state: Zustand, the same library already used on web.
- Validation: Zod, the same library already used on web.
- Styling: NativeWind with Tamagui or gluestack-ui as the component primitive layer.
- Testing: Jest, React Native Testing Library, and MSW for unit/integration; Maestro for end-to-end flows.
- Build and distribution: EAS Build, EAS Submit, and EAS Update.

Mobile-specific documentation lives under `docs/mobile/`, following the same structure as `docs/frontend/` and `docs/backend/`. Mobile code must not be mixed into web frontend folders, and web frontend conventions must not be assumed to apply to mobile without being explicitly restated in `docs/mobile/`.

## Consequences

Benefits:

- shared data-fetching, state, and validation conventions across web and mobile reduce the number of competing patterns for the same concern
- Expo Router's file-based routing keeps the mental model consistent with the Next.js App Router
- dedicated mobile documentation prevents mobile-specific rules (secure token storage, navigation boundaries, platform-specific files) from being lost inside web-focused docs
- EAS tooling gives a maintained build/release pipeline without requiring native Xcode/Android Studio project management for common cases

Costs and tradeoffs:

- Expo's managed workflow constrains some native module choices unless the project ejects or uses config plugins
- mobile authentication cannot reuse the web's cookie-based session default and requires its own secure-storage and token-refresh handling
- three stack-specific guideline sets (frontend, backend, mobile) must now be kept in sync for any genuinely shared concern

## Alternatives Considered

### Bare React Native (No Expo)

Rejected as the default because it requires managing native iOS/Android project configuration directly, increasing setup and maintenance cost without a clear benefit for the current project needs. Teams may still eject from Expo later if a specific native requirement demands it.

### Flutter or Native (Swift/Kotlin) Mobile Stack

Rejected because it would introduce an entirely separate language and ecosystem, duplicating data-fetching, validation, and state-management concerns that are already solved with TanStack Query, Zod, and Zustand on web. React Native allows reuse of TypeScript and, where reasonable, business logic conventions across web and mobile.

### Mixing Mobile Code into the Web Frontend Folder Structure

Rejected because it would blur module boundaries between two different runtime environments (browser vs. native), violating the module boundary rules in `docs/architecture/module-boundaries.md`.
