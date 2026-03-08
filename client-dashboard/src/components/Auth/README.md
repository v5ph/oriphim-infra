# Auth Domain

## Purpose
Auth components define the dashboard access boundary: login, guarded rendering, and top-level auth provider composition.

## Components
- `LoginForm.tsx`: API key based login form.
- `ProtectedRoute.tsx`: Renders children only when authenticated.
- `AuthProvider.tsx`: Provider shell used from `main.tsx`.

## Data and Dependencies
- Reads auth state from `@hooks/useAuth`.
- Uses token storage keys configured in `src/config/env.ts`.
- Must not call backend endpoints directly; use `useAuth` / `services/api.ts` only.

## Usage
```tsx
import { LoginForm, ProtectedRoute } from '@components/Auth';

<ProtectedRoute>
  <Dashboard />
</ProtectedRoute>
```

## Extension Rules
- Keep auth UI concerns in this domain; move reusable primitives to `components/Common`.
- Keep business logic in hooks/services, not JSX event handlers.
- Preserve error-state rendering for invalid credentials and network failures.
