# Validations Domain

## Purpose
Validations components render recent validation events and provide drill-down details for operator decision support.

## Components
- `RecentValidations.tsx`: Domain entry with refresh loop.
- `ValidationTable.tsx`: Tabular list and modal orchestration.
- `ValidationRow.tsx`: Row-level signal/action summary.
- `ValidationDetailModal.tsx`: Full validation evidence view.

## Data and Dependencies
- Uses `ValidationMetrics` from `@/types`.
- Data collection belongs in hooks/services; UI components receive typed data.
- Error/loading handling must remain explicit and visible.

## Usage
```tsx
import { RecentValidations } from '@components/Validations';

<RecentValidations />
```

## Extension Rules
- Keep table row rendering lightweight; expensive formatting belongs in `lib/utils`.
- Maintain stable keys in row rendering to avoid modal/selection glitches.
- Any new backend fields must be added to `src/types` before UI usage.
