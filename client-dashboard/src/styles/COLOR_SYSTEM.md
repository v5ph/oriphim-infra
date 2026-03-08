# ORIPHIM Color System

## Overview
Modern, enterprise-grade color palette optimized for infrastructure monitoring dashboards. All colors meet WCAG AA accessibility standards.

## Core Palette

### Brand (Indigo)
Primary brand color for CTAs, active states, and key UI elements.
- `brand-600`: `#4F46E5` (Primary)
- `brand-700`: `#4338CA` (Hover)
- Full range: 50-900

### Neutrals (Slate)
Base grays for text, borders, backgrounds.
- `slate-50`: `#F8FAFC` (Background)
- `slate-200`: `#E2E8F0` (Borders)
- `slate-600`: `#475569` (Secondary text)
- `slate-900`: `#0F172A` (Primary text)

## Semantic Colors

### Success (Emerald)
Operational status, successful validations, healthy systems.
- `success-500`: `#10B981`
- `success-50`: `#ECFDF5` (Background)
- `success-700`: `#047857` (Text)

### Warning (Amber)
Degraded performance, attention needed, review required.
- `warning-500`: `#F59E0B`
- `warning-50`: `#FFFBEB` (Background)
- `warning-700`: `#B45309` (Text)

### Danger (Red)
Critical errors, blocked validations, system failures.
- `danger-500`: `#EF4444`
- `danger-600`: `#DC2626`
- `danger-50`: `#FEF2F2` (Background)
- `danger-700`: `#B91C1C` (Text)

### Info (Cyan)
Informational messages, metrics, neutral alerts.
- `info-500`: `#06B6D4`
- `info-50`: `#ECFEFF` (Background)
- `info-700`: `#0E7490` (Text)

## Legacy Compatibility
The following legacy variables are remapped to new values:
- `floral-white` → `slate-50`
- `carbon-black` → `slate-900`
- `blood-red` → `danger-600`
- `deep-crimson` → `danger-700`
- `space-indigo` → `brand-600`
- `charcoal-brown` → `slate-600`

## Usage Examples

### Status Indicators
```tsx
<div className="status-green">Operational</div>
<div className="status-yellow">Degraded</div>
<div className="status-red">Critical</div>
```

### Buttons
```tsx
<button className="btn-primary">Primary Action</button>
<button className="btn-secondary">Secondary Action</button>
```

### Badges
```tsx
<span className="badge-allow">ALLOW</span>
<span className="badge-review">REVIEW</span>
<span className="badge-block">BLOCK</span>
```

### Cards & Containers
```tsx
<div className="card">...</div>
<div className="metric-card-success">...</div>
```

## Contrast Ratios
All color combinations meet WCAG AA standards:
- Normal text: 4.5:1 minimum
- Large text: 3:1 minimum
- Interactive elements: 3:1 minimum

## CSS Variables
Available in `:root`:
- `--brand-primary`: Primary brand color
- `--gray-900`: Dark text
- `--success`, `--warning`, `--danger`, `--info`: Semantic colors
- `--*-bg`: Background variants for each semantic color
