# Dashboard Organization Blueprint

## Current State Assessment

**Strengths:**
- Domain-driven component structure (Auth, Audit, Onboarding, etc.)
- Clean separation: components, hooks, services, store, types
- TypeScript strict mode enforced
- Modern stack: React 18, Vite, Zustand

**Gaps:**
- Duplicate styles (src/App.css, src/index.css vs src/styles/)
- No lib/utils layer for shared business logic
- Missing error boundary infrastructure
- No centralized config/constants
- Test structure incomplete (e2e exists, unit tests absent)
- Component barrel exports missing

## Canonical Structure (Production-Grade)

```
client-dashboard/
├── public/                    # Static assets only
├── src/
│   ├── main.tsx              # App entry point
│   ├── App.tsx               # Root component with providers
│   ├── components/           # UI components by domain
│   │   ├── Auth/
│   │   ├── Audit/
│   │   ├── Common/           # Shared UI primitives
│   │   ├── Dashboard/
│   │   ├── Incidents/
│   │   ├── Integration/
│   │   ├── Onboarding/
│   │   ├── Status/
│   │   ├── Validations/
│   │   └── ErrorBoundary/    # NEW: Error handling UI
│   ├── hooks/                # React hooks (useAPI, useAuth, etc.)
│   ├── services/             # API client layer (thin wrappers)
│   │   ├── api.ts            # Base axios instance + interceptors
│   │   ├── auth.ts
│   │   ├── audit.ts
│   │   └── [domain].ts
│   ├── lib/                  # NEW: Business logic, utilities, helpers
│   │   ├── validation/       # Input validators
│   │   ├── formatters/       # Date, number, currency formatters
│   │   ├── constants/        # App-wide constants
│   │   └── utils/            # Pure functions
│   ├── config/               # NEW: Environment and feature flags
│   │   ├── env.ts            # Runtime env validation (zod)
│   │   └── features.ts       # Feature toggles
│   ├── store/                # Zustand state management
│   ├── types/                # TypeScript interfaces/types
│   ├── styles/               # Global styles only
│   │   └── globals.css       # Tailwind directives + base styles
│   └── assets/               # Images, fonts, icons
├── tests/
│   ├── unit/                 # NEW: Component + hook unit tests (Vitest)
│   ├── integration/          # NEW: Multi-component integration tests
│   ├── e2e/                  # Playwright/Cypress end-to-end tests
│   └── fixtures/             # Test data and mocks
├── .env.example              # Template with all vars documented
├── .env.local                # Local overrides (gitignored)
├── vite.config.ts
├── tsconfig.json
└── package.json
```

## Placement Rules (Enforced)

### 1. Styles
- **Single source:** Only `src/styles/globals.css` for global styles
- **Component styles:** Use Tailwind utility classes inline
- **Complex components:** CSS modules if absolutely required (`*.module.css`)
- **FORBIDDEN:** Loose `.css` files at `src/` root

### 2. Business Logic
- **Never in components:** Components are UI-only, delegate logic to lib/ or hooks/
- **lib/:** Pure functions, validators, formatters (no React)
- **hooks/:** React-specific stateful logic
- **services/:** API calls only, no business logic

### 3. Configuration
- **Environment vars:** Validate at runtime in `config/env.ts` (use zod)
- **Feature flags:** Centralize in `config/features.ts`
- **Constants:** Domain constants in `lib/constants/[domain].ts`
- **FORBIDDEN:** Magic strings/numbers in components

### 4. Components
- **Index exports:** Each domain folder MUST have `index.ts` barrel export
- **Max complexity:** 200 lines per component; split if exceeded
- **Props types:** Inline for single-use, `types/` for shared
- **Error boundaries:** Wrap async boundaries (data fetching, modals)

### 5. Tests
- **Unit tests:** Co-located with source (`.test.ts` suffix) OR `tests/unit/`
- **Integration:** `tests/integration/` for multi-component workflows
- **E2E:** `tests/e2e/` for critical user paths only
- **Coverage target:** 80% for lib/, 60% for components

### 6. Types
- **API types:** Auto-generate from OpenAPI spec if available
- **Domain types:** One file per domain (`types/auth.ts`, `types/validation.ts`)
- **Avoid `any`:** Strict TypeScript mode enforced

## Migration Waves

### Wave 1: Hygiene Cleanup (30 min)
1. Consolidate styles:
   - Move content from `src/App.css` and `src/index.css` to `src/styles/globals.css`
   - Delete `src/App.css` and `src/index.css`
   - Update imports in App.tsx and main.tsx
2. Add barrel exports:
   - Create `index.ts` in each component domain folder
   - Export all components from their domain
3. Update gitignore:
   - Ensure `dist/`, `node_modules/`, `.env.local` ignored
   - Add `coverage/` for test reports

### Wave 2: Infrastructure Additions (1-2 hours)
1. Create `src/config/`:
   ```typescript
   // config/env.ts
   import { z } from 'zod';
   
   const envSchema = z.object({
     VITE_API_BASE_URL: z.string().url(),
     VITE_API_TIMEOUT: z.coerce.number().default(30000),
   });
   
   export const env = envSchema.parse({
     VITE_API_BASE_URL: import.meta.env.VITE_API_BASE_URL,
     VITE_API_TIMEOUT: import.meta.env.VITE_API_TIMEOUT,
   });
   ```
2. Create `src/lib/` structure:
   - `lib/constants/endpoints.ts`
   - `lib/utils/format.ts`
   - `lib/validation/schemas.ts`
3. Add error boundary:
   ```typescript
   // components/ErrorBoundary/AppErrorBoundary.tsx
   // Catch-all for uncaught errors
   ```
4. Create test structure:
   - `tests/unit/` with sample test
   - `tests/integration/` with README
   - Configure Vitest in vite.config.ts

### Wave 3: Quality Gates (30 min)
1. Add NPM scripts:
   ```json
   {
     "test": "vitest",
     "test:unit": "vitest run tests/unit",
     "test:e2e": "playwright test",
     "type-check": "tsc --noEmit",
     "lint:strict": "eslint . --max-warnings 0"
   }
   ```
2. Pre-commit hook (Husky):
   - Run `type-check` + `lint:strict` before commit
3. CI pipeline check:
   - Block merge if: type errors, lint warnings, or test failures

### Wave 4: Documentation (30 min)
1. Component README per domain (optional but recommended):
   - `components/Auth/README.md` - Usage examples
2. Update root README.md:
   - Architecture diagram
   - Dev setup instructions
   - Environment variables reference
3. API integration guide:
   - How to add new endpoints
   - Error handling patterns

## Acceptance Criteria

- [ ] Zero loose CSS files at `src/` root
- [ ] All component domains have barrel exports (`index.ts`)
- [ ] Runtime environment validation exists and throws on missing vars
- [ ] `lib/` folder contains all non-React business logic
- [ ] Error boundary wraps App.tsx
- [ ] `npm run type-check` passes with zero errors
- [ ] `npm run lint:strict` passes with zero warnings
- [ ] Unit test structure exists (even if empty tests initially)
- [ ] Every `.env.example` variable is documented
- [ ] New contributors can run `npm install && npm run dev` in under 2 minutes

## Anti-Patterns to Avoid

**FORBIDDEN:**
- Fetching data directly in components (use hooks + services)
- Business logic in event handlers (extract to lib/)
- Relative imports beyond 2 levels (`../../../` → use path aliases)
- Mutating Zustand state outside actions
- Hardcoded API URLs (use config/env.ts)
- Ignoring TypeScript errors with `@ts-ignore`
- Mixing UI and API logic in same file

**Path Aliases (tsconfig):**
```json
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./src/*"],
      "@components/*": ["./src/components/*"],
      "@hooks/*": ["./src/hooks/*"],
      "@services/*": ["./src/services/*"],
      "@lib/*": ["./src/lib/*"],
      "@types/*": ["./src/types/*"]
    }
  }
}
```

## Ownership Model

| Domain | Owner | Responsibilities |
|--------|-------|------------------|
| `components/` | Frontend team | UI implementation, accessibility |
| `services/` | Integration team | API contracts, error handling |
| `lib/` | Platform team | Shared utilities, validators |
| `config/` | DevOps | Environment management |
| `tests/` | QA + Developers | Coverage, quality gates |
| Root config | Tech lead | Build tooling, dependencies |

## Performance Budget

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| First Contentful Paint | < 1.5s | 2s |
| Time to Interactive | < 3s | 4s |
| Bundle size (gzipped) | < 200KB | 300KB |
| Lighthouse score | > 90 | < 85 |

**Monitoring:**
- Bundle analyzer: `npm run build -- --analyze`
- Lighthouse CI in GitHub Actions

## Security Checklist

- [ ] CSP headers configured in production
- [ ] No secrets in environment variables exposed to browser
- [ ] API keys never logged or exposed in errors
- [ ] XSS protection: Sanitize user input before render
- [ ] CSRF tokens for state-changing operations
- [ ] Dependencies scanned weekly (`npm audit`)
- [ ] HTTPS-only in production
- [ ] Secure cookie flags: httpOnly, secure, sameSite

## Next Steps (Choose One)

**Option A: Quick Win (30 min)**
Execute Wave 1 only - immediate hygiene improvement, zero risk.

**Option B: Full Production Hardening (4 hours)**
Execute all 4 waves - production-grade structure, ready for scaling.

**Option C: Gradual (2 weeks)**
One wave per sprint, validate with stakeholders between waves.

**Recommendation:** Start with Wave 1, measure impact, then commit to Wave 2-4 in next sprint.
