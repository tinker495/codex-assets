---
name: frontend-design
description: Design or implement branded landing pages, marketing sites, homepage heroes, campaign pages, and other visually led frontend surfaces with strong brand presence, one-composition-above-the-fold structure, full-bleed hero media, intentional motion, and non-generic typography/color direction. Use when Codex needs to create or refresh promotional frontend work in HTML/CSS/React, strengthen a weak hero, review a page for generic card-heavy layout decisions, or translate brand direction into responsive frontend code. Do not use for dashboards, admin panels, or product-app UI; use $interface-design for those.
---

# Frontend Design

## Objective

Design and implement branded frontend surfaces that feel authored, not templated. Make the first viewport carry the brand, keep the composition focused, and turn the direction into responsive code.

## Route the task

- Use this skill for landing pages, marketing sites, branded homepages, launch pages, campaign surfaces, and visual refreshes of promotional pages.
- Use `$interface-design` for dashboards, admin panels, settings, internal tools, and product-app UI.
- Preserve the existing website or design system when it already defines the visual language. Adapt within it instead of replacing it.

## Define the direction before coding

- Name the brand or product that must dominate the first viewport.
- Name the single action the hero must drive.
- Name the real visual anchor: product, place, atmosphere, or context.
- Name the mood, type direction, and color direction in concrete terms.
- Reject structures that read like dashboards when the page is meant to sell, launch, or introduce.

## Build the first viewport as one composition

- Make the first viewport read as one composition, not a pile of modules.
- Make the brand or product name a hero-level signal. Do not hide it in navigation, a tiny eyebrow, or secondary copy.
- Keep the hero budget to: brand, one headline, one short supporting sentence, one CTA group, and one dominant image.
- Use a full-bleed hero image or full-bleed background image plane by default on landing pages and promotional surfaces.
- Use real imagery as the main idea. Decorative gradients and abstract backgrounds cannot be the primary visual anchor.
- Keep secondary marketing content below the fold unless it is the page's only job.

## Remove common failure modes

- Do not use inset hero images, side-panel hero images, rounded media cards, tiled collages, or floating image blocks unless the existing system requires them.
- Do not place detached badges, promo stickers, chips, info boxes, or callout overlays on top of hero media.
- Do not put stats, schedules, event listings, address blocks, promos, metadata rows, or "this week" callouts in the first viewport.
- Default to no cards. Never use cards in the hero.
- Use cards only when they contain an interaction. If removing border, shadow, background, or radius does not hurt comprehension or interaction, remove the card treatment.

## Shape each section around one job

- Give each section one purpose, one headline, and usually one short supporting sentence.
- Cut pill clusters, stat strips, icon rows, boxed promos, schedule snippets, and competing text blocks unless the section exists to present them.
- Keep section order simple: hero first, proof or support later, details last.

## Choose a deliberate visual system

- Choose expressive typography that fits the brand. Do not default to Inter, Roboto, Arial, or generic system stacks.
- Define CSS variables for color, typography, spacing, radius, and motion before scaling the page.
- Use gradients, photography, texture, or subtle patterns to build atmosphere instead of relying on flat single-color backgrounds.
- Choose a clear color direction. Do not default to purple-on-white. Do not drift into dark mode without a reason from the brand or context.
- Keep typography, color, spacing, and imagery aligned to the same intent.

## Use motion to create presence

- Ship at least 2-3 intentional motions on visually led work.
- Use motion to establish hierarchy, reveal sections, and give media presence.
- Keep motion quiet and purposeful. Avoid decorative loops and noisy choreography.

## Implement cleanly

- Make the page load and read correctly on desktop and mobile.
- Follow the repo's existing implementation patterns and design-system constraints when they exist.
- In React code, prefer modern patterns already accepted by the team.
- Use `useEffectEvent`, `startTransition`, and `useDeferredValue` when they fit the interaction and repo conventions.
- Do not add `useMemo` or `useCallback` by default.
- Keep implementation direct. Do not add abstractions that only serve one marketing page.

## Present the solution in this order

- State the intent: user, action, and feel.
- State the first-viewport composition.
- State the visual system: type, color, imagery, and atmosphere.
- State the motion plan.
- State the section order.
- Implement or describe the page.

## Review before presenting

- Remove the navigation in your head. If the first viewport could belong to another brand, strengthen the brand signal.
- Compare the headline and brand. If the headline visually wins, rebalance.
- Remove borders, shadows, backgrounds, and radii from any non-interactive container. If nothing breaks, keep them removed.
- Squint at the hero. If more than one thing competes for attention, cut content.
- Check that the dominant image is real context, not decorative abstraction.
- Check that each section still has one job on mobile and desktop.
