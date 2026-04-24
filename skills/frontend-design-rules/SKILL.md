---
name: frontend-design-rules
description: Hard rules for frontend design tasks — hero-first layout, brand hierarchy, typography, cards, motion, and React patterns
triggers:
  - frontend
  - design
  - ui
  - ux
  - hero
  - landing page
  - layout
  - brand
  - typography
  - cards
  - motion
argument-hint: ""
---

# Frontend Design Rules

## Purpose

Enforce opinionated, high-quality frontend design decisions. Avoid generic, overbuilt layouts. These are hard rules, not suggestions.

## When to Activate

When doing any frontend design task — building pages, components, layouts, or reviewing UI code.

## Hard Rules

### Composition & Layout
- **One composition**: The first viewport must read as one composition, not a dashboard (unless it's a dashboard).
- **Hero budget**: The first viewport should usually contain only the brand, one headline, one short supporting sentence, one CTA group, and one dominant image. Do not place stats, schedules, event listings, address blocks, promos, "this week" callouts, metadata rows, or secondary marketing content in the first viewport.
- **Full-bleed hero only**: On landing pages and promotional surfaces, the hero image should be a dominant edge-to-edge visual plane or background by default. Do not use inset hero images, side-panel hero images, rounded media cards, tiled collages, or floating image blocks unless the existing design system clearly requires it.
- **No hero overlays**: Do not place detached labels, floating badges, promo stickers, info chips, or callout boxes on top of hero media.
- **One job per section**: Each section should have one purpose, one headline, and usually one short supporting sentence.

### Brand
- **Brand first**: On branded pages, the brand or product name must be a hero-level signal, not just nav text or an eyebrow. No headline should overpower the brand.
- **Brand test**: If the first viewport could belong to another brand after removing the nav, the branding is too weak.

### Typography & Visual
- **Typography**: Use expressive, purposeful fonts and avoid default stacks (Inter, Roboto, Arial, system).
- **Background**: Don't rely on flat, single-color backgrounds; use gradients, images, or subtle patterns to build atmosphere.
- **Real visual anchor**: Imagery should show the product, place, atmosphere, or context. Decorative gradients and abstract backgrounds do not count as the main visual idea.
- **Color & Look**: Choose a clear visual direction; define CSS variables; avoid purple-on-white defaults. No purple bias or dark mode bias.

### Cards & Clutter
- **Cards**: Default: no cards. Never use cards in the hero. Cards are allowed only when they are the container for a user interaction. If removing a border, shadow, background, or radius does not hurt interaction or understanding, it should not be a card.
- **Reduce clutter**: Avoid pill clusters, stat strips, icon rows, boxed promos, schedule snippets, and multiple competing text blocks.

### Motion
- Use motion to create presence and hierarchy, not noise. Ship at least 2-3 intentional motions for visually led work.

### Responsiveness
- Ensure the page loads properly on both desktop and mobile.

### React Patterns
- For React code, prefer modern patterns including `useEffectEvent`, `startTransition`, and `useDeferredValue` when appropriate if used by the team.
- Do not add `useMemo`/`useCallback` by default unless already used; follow the repo's React Compiler guidance.

### Exception
If working within an existing website or design system, preserve the established patterns, structure, and visual language.

## Checklist

Before finalizing any frontend design work, verify:

1. First viewport = one composition with clear brand signal
2. Hero is full-bleed, edge-to-edge (no inset/floating)
3. No cards in the hero; cards only for interactive containers
4. Typography is expressive, not default stacks
5. Background has depth (gradient, image, pattern)
6. Each section has one job, one headline
7. At least 2-3 intentional motion effects
8. Works on both desktop and mobile
9. CSS variables defined for color direction
10. No purple-on-white or dark mode bias defaults
