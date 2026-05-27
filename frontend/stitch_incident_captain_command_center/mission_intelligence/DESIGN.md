---
name: Mission Intelligence
colors:
  surface: '#f8f9fa'
  surface-dim: '#d9dadb'
  surface-bright: '#f8f9fa'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f3f4f5'
  surface-container: '#edeeef'
  surface-container-high: '#e7e8e9'
  surface-container-highest: '#e1e3e4'
  on-surface: '#191c1d'
  on-surface-variant: '#434933'
  inverse-surface: '#2e3132'
  inverse-on-surface: '#f0f1f2'
  outline: '#737a61'
  outline-variant: '#c3caac'
  surface-tint: '#4c6700'
  primary: '#4c6700'
  on-primary: '#ffffff'
  primary-container: '#c1ff00'
  on-primary-container: '#567300'
  inverse-primary: '#a3d800'
  secondary: '#5b5f63'
  on-secondary: '#ffffff'
  secondary-container: '#dde0e5'
  on-secondary-container: '#5f6368'
  tertiary: '#0062a1'
  on-tertiary: '#ffffff'
  tertiary-container: '#dfecff'
  on-tertiary-container: '#006db4'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#baf600'
  primary-fixed-dim: '#a3d800'
  on-primary-fixed: '#151f00'
  on-primary-fixed-variant: '#394e00'
  secondary-fixed: '#e0e3e8'
  secondary-fixed-dim: '#c3c7cc'
  on-secondary-fixed: '#181c20'
  on-secondary-fixed-variant: '#43474c'
  tertiary-fixed: '#d1e4ff'
  tertiary-fixed-dim: '#9dcaff'
  on-tertiary-fixed: '#001d35'
  on-tertiary-fixed-variant: '#00497b'
  background: '#f8f9fa'
  on-background: '#191c1d'
  surface-variant: '#e1e3e4'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-md-mobile:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 15px
    fontWeight: '400'
    lineHeight: 22px
  label-caps:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '700'
    lineHeight: 16px
    letterSpacing: 0.05em
  metadata:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 18px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 8px
  gutter: 24px
  margin-page: 32px
  card-padding: 24px
  stack-sm: 12px
  stack-md: 20px
---

## Brand & Style

The design system is engineered for high-stakes enterprise environments where clarity and rapid response are paramount. It adopts a **Mission Control** aesthetic—blending the clinical precision of modern healthcare interfaces with the authoritative density of a command center. 

The brand personality is **composed, vigilant, and surgical**. It avoids unnecessary decoration, opting instead for a "functional futuristic" look. The interface should feel like an extension of the user’s intelligence, providing a calm "eye of the storm" during critical system incidents. Visual interest is generated through asymmetrical modularity and high-contrast status indicators rather than illustrative flourishes.

## Colors

This design system utilizes a high-utility palette rooted in grayscale foundations with "electric" functional accents.

- **Primary Neon:** Use `#C1FF00` sparingly for success states, active AI insights, and primary "Resolve" actions. It is a beacon of health.
- **Surface Strategy:** The UI uses a tri-tier grayscale system. The base application background is `#F8F9FA`, while modular containers (cards) use pure `#FFFFFF` to pop forward. A deeper `#F1F3F5` is reserved for inset areas or well-defined sidebar gutters.
- **Typography & Borders:** Text uses a deep charcoal `#212529` for maximum legibility. Borders must remain whisper-thin and subtle (`rgba(0,0,0,0.05)`) to maintain the "clean enterprise" feel.
- **Telemetry Palette:** Standard status colors are used for data visualization: Amber for pending warnings, Red for active breaches/errors, and Blue for informational telemetry or cold data.

## Typography

The typography system relies exclusively on **Inter** to deliver a neutral, systematic feel that handles dense data without losing legibility.

- **Hierarchical Contrast:** Large, bold headlines are used for incident titles and dashboard sections to ground the user.
- **Compact Metadata:** Much of the interface relies on `metadata` and `label-caps` for logs, timestamps, and system metrics. These are tightly tracked to ensure high-density information density without visual clutter.
- **Numerical Data:** For telemetry and countdowns, ensure `font-variant-numeric: tabular-nums` is applied to prevent horizontal "jumping" as values update in real-time.

## Layout & Spacing

This design system employs an **Asymmetrical Modular Grid**. Unlike rigid symmetrical dashboards, content is grouped into cards of varying widths (e.g., a 7-column primary investigation feed next to a 5-column telemetry sidebar).

- **Grid:** A 12-column fluid system with wide 24px gutters. 
- **Density:** While the outer margins are generous (32px), internal card spacing is kept tight (8px-12px between elements) to allow "mission-critical" data to remain visible above the fold.
- **Mobile Reflow:** On mobile, columns stack vertically. Asymmetrical sidebars move to the bottom of the scroll or are hidden behind a "Global Intel" drawer.

## Elevation & Depth

Hierarchy is established through **Tonal Layering** and **Ultra-Soft Shadows** rather than heavy dark gradients.

- **Level 0 (Canvas):** The base background (`#F8F9FA`).
- **Level 1 (Modules):** Pure white cards (`#FFFFFF`) with a subtle 1px border (`rgba(0,0,0,0.05)`) and a large-spread, low-opacity shadow (Color: `#000000`, Alpha: 0.03, Blur: 40px). This makes cards feel like they are floating slightly above the command surface.
- **Level 2 (Interaction):** Hover states for cards increase the shadow density slightly and may introduce a primary-neon left-border accent (4px width).
- **Insets:** Search bars and code blocks use an "inset" style with a slightly darker background (`#F1F3F5`) to appear recessed into the UI.

## Shapes

The shape language is defined by **pronounced, friendly radii** that soften the technical nature of the content.

- **Container Radius:** All primary dashboard cards and modular units must use a 24px (`1.5rem`) corner radius. This is the hallmark of the system’s visual identity.
- **Component Radius:** Smaller elements like buttons, input fields, and chips use a 12px or 16px radius to maintain the "pill-adjacent" aesthetic without going fully circular.
- **Internal Nesting:** When an element is nested inside a 24px container, the inner element should use a smaller radius (typically 12px) to maintain concentric visual harmony.

## Components

### Buttons
- **Primary:** Neon-lime background with black text. High visibility for "Execute" or "Resolve."
- **Secondary:** White background with a subtle border and charcoal text.
- **Ghost:** Text only, used for secondary metadata actions.

### Cards (The Modular Unit)
- Every "Incident Detail" or "Metric Trend" is housed in a Level 1 card.
- Cards should feature a top-right "Action Overflow" (three dots) and a bold title in the top-left.

### Status Chips
- Pill-shaped with a small leading dot. 
- "Investigating" = Blue, "Critical" = Red, "Resolved" = Neon Lime.

### Input Fields
- Subtle gray backgrounds (`#F1F3F5`) with no border until focused.
- On focus, the border becomes the primary neon or a neutral dark charcoal.

### Progress & Telemetry
- Use thin, high-contrast sparklines. 
- Avoid heavy gauges; use horizontal "percentage bars" that leverage the 24px roundedness for the outer container.

### AI Captain Insights
- Special component: A card with a subtle Neon Lime glow (inner shadow) to denote that the content was generated by the platform's AI.