# Status Domain

## Purpose
Status components present platform health, indicator state, and operational summary for risk monitoring.

## Components
- `StatusDashboard.tsx`: Domain entry page.
- `TrafficLightIndicator.tsx`: GREEN/YELLOW/RED signal display.
- `MetricsGrid.tsx`: Core health metric cards.
- `HistoricalChart.tsx`: Trend placeholder/visualization surface.
- `MetricsCard.tsx`: Reusable metric card primitive.

## Data and Dependencies
- Uses `@hooks/useHealth` for polling and error/loading states.
- Uses typed `HealthMetrics` from `@/types`.
- Poll intervals are controlled by runtime env in `src/config/env.ts`.

## Usage
```tsx
import { StatusDashboard } from '@components/Status';

<StatusDashboard />
```

## Extension Rules
- Keep status rendering pure; compute/transform values in hooks or `lib/*`.
- Preserve deterministic empty/loading/error states for operational clarity.
- Do not hardcode endpoint URLs or polling constants in components.
