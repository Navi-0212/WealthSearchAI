---
name: Premium Fintech System
colors:
  surface: '#10131a'
  surface-dim: '#10131a'
  surface-bright: '#353941'
  surface-container-lowest: '#0a0e15'
  surface-container-low: '#181c23'
  surface-container: '#1c2027'
  surface-container-high: '#262a32'
  surface-container-highest: '#31353d'
  on-surface: '#e0e2ec'
  on-surface-variant: '#c0c6d6'
  inverse-surface: '#e0e2ec'
  inverse-on-surface: '#2d3038'
  outline: '#8a919f'
  outline-variant: '#404754'
  surface-tint: '#a8c8ff'
  primary: '#a8c8ff'
  on-primary: '#003061'
  primary-container: '#3491ff'
  on-primary-container: '#002955'
  inverse-primary: '#005eb3'
  secondary: '#bdf4ff'
  on-secondary: '#00363d'
  secondary-container: '#00e3fd'
  on-secondary-container: '#00616d'
  tertiary: '#ffb68f'
  on-tertiary: '#542100'
  tertiary-container: '#ea6c10'
  on-tertiary-container: '#4a1c00'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#d5e3ff'
  primary-fixed-dim: '#a8c8ff'
  on-primary-fixed: '#001b3c'
  on-primary-fixed-variant: '#004689'
  secondary-fixed: '#9cf0ff'
  secondary-fixed-dim: '#00daf3'
  on-secondary-fixed: '#001f24'
  on-secondary-fixed-variant: '#004f58'
  tertiary-fixed: '#ffdbca'
  tertiary-fixed-dim: '#ffb68f'
  on-tertiary-fixed: '#331100'
  on-tertiary-fixed-variant: '#773200'
  background: '#10131a'
  on-background: '#e0e2ec'
  surface-variant: '#31353d'
typography:
  display-lg:
    fontFamily: Outfit
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Outfit
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Outfit
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
  headline-md:
    fontFamily: Outfit
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 8px
  xs: 4px
  sm: 12px
  md: 24px
  lg: 48px
  xl: 80px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 40px
---

## Brand & Style

The design system is engineered for a high-stakes financial environment where precision meets futuristic innovation. The brand personality is **authoritative yet visionary**, balancing the strict requirements of compliance with the fluid, high-tech nature of artificial intelligence. It targets high-net-worth individuals and sophisticated investors who demand a "command center" aesthetic that feels both secure and cutting-edge.

The visual style is a refined **Glassmorphism**, characterized by deep spatial layers and luminous accents. It utilizes a structural dark-mode foundation to reduce eye strain during prolonged data analysis, while using vibrant neon-leaning primaries to highlight key financial insights. The overall emotional response should be one of "calm control" and "technological superiority."

## Colors

The palette is anchored by a sophisticated **True Dark** base. The primary and secondary colors are high-energy blues designed to stand out against the deep background, signifying growth and digital intelligence.

- **Primary (#0088ff):** Used for main actions, active states, and branding elements.
- **Secondary (#00e5ff):** Reserved for data visualization highlights and success indicators.
- **Accent (#feb019):** A strategic gold used for high-value alerts, premium features, and warning states to ensure compliance-related information is never missed.
- **Background:** A vertical gradient from `#0a0b10` to `#06070a`. Large, organic "blobs" of primary/secondary colors should be placed in the background with a 120px Gaussian blur at 15% opacity to provide a sense of depth and movement.

## Typography

This design system uses a dual-typeface approach to distinguish between editorial impact and functional clarity. 

**Outfit** is used for headlines to provide a modern, geometric structure that feels tech-forward. Use tighter letter-spacing on larger displays to maintain a premium "locked-in" look. 

**Plus Jakarta Sans** is the workhorse for body copy and UI labels. Its slightly wider apertures ensure high legibility on dark backgrounds, even at smaller sizes or in data-dense tables. Text should maintain a high contrast ratio (typically 90% white for primary text, 60% for secondary metadata) to meet accessibility standards within the dark theme.

## Layout & Spacing

The layout utilizes a **12-column fluid grid** for desktop and a **4-column grid** for mobile. A strict 8px base-unit system ensures vertical rhythm and consistent density across complex financial dashboards.

- **Desktop:** 40px outer margins with 24px gutters. Use large `xl` (80px) vertical spacing to separate major content sections, creating a sense of luxury and breathing room.
- **Mobile:** 16px outer margins. Content should stack vertically, with card components spanning the full width of the grid minus margins.
- **Alignment:** Financial data in tables should be right-aligned for numerical comparison, while text labels remain left-aligned.

## Elevation & Depth

Hierarchy is established through **translucent glass layers** rather than traditional shadows. This mimics a physical stack of semi-transparent acrylic panels.

1.  **Base Layer:** The background gradient with blurred color blobs.
2.  **Mid Layer (Cards/Containers):** `backdrop-filter: blur(20px)` with a background of `rgba(255, 255, 255, 0.03)`. A crucial 1px solid border at `rgba(255, 255, 255, 0.06)` must be applied to define the edges against the dark background.
3.  **Top Layer (Modals/Popovers):** `backdrop-filter: blur(40px)` with a slightly higher background opacity (`rgba(255, 255, 255, 0.08)`).

All transitions between states (e.g., hovering over a card) must use a `cubic-bezier(0.4, 0, 0.2, 1)` timing function for a smooth, high-fidelity feel.

## Shapes

The shape language is **Rounded (Level 2)**. This strikes a balance between the precision of sharp corners and the approachability of fully rounded forms.

- **Standard Elements:** 0.5rem (8px) radius for buttons and input fields.
- **Containers:** 1rem (16px) radius for primary cards and dashboard widgets.
- **Large Sections:** 1.5rem (24px) radius for global containers or bottom sheets on mobile.
- **Compliance Badges:** Should use a "Pill" shape (100px radius) to distinguish them from interactive UI buttons.

## Components

### Buttons
- **Primary:** Solid background using the Primary Blue. Use a subtle inner glow (top-down white overlay at 10%) to create a "glass-press" effect.
- **Secondary:** Transparent background with a 1px solid Primary Blue border.
- **Compliance/Alert:** Solid Accent Gold with black text for maximum visibility.

### Glass Cards
All cards must implement the `backdrop-filter: blur(20px)` and the 1px subtle border. Content inside cards should have a consistent 24px internal padding.

### Inputs
Input fields use a dark, semi-transparent fill (`rgba(0,0,0,0.2)`). The border should transition from the standard `rgba(255,255,255,0.06)` to a vivid `Primary Blue` on focus, accompanied by a soft outer glow.

### Data Visualization
Charts should use the Secondary Aqua and Primary Blue for growth/positive data. Use the Accent Gold specifically for "Warning" or "Action Required" zones in compliance-related monitoring.

### Lists & Tables
Rows should be separated by 1px lines at `rgba(255,255,255,0.04)`. Alternate row stripping is discouraged; instead, use hover states that slightly increase the card's background opacity to highlight the active row.