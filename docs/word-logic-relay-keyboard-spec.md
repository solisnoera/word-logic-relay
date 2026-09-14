# WORD LOGIC RELAY v2 — On-screen Keyboard Binding Specification

This document is a binding addendum to `docs/word-logic-relay-implementation.md`.

## Goal

The on-screen keyboard should visually and spatially resemble a real QWERTY keyboard more closely than the current Wordle-style layout.

The current source places controls around the bottom letter row (`ENTER` on the left of Z and `DEL` on the right of M). Replace that arrangement.

## Required layout

Use a staggered three-row QWERTY layout with the editing/action keys on the right-hand side where users expect them from a physical keyboard:

```text
Q  W  E  R  T  Y  U  I  O  P   [ DEL ]
   A  S  D  F  G  H  J  K  L    [ ENTER ]
      Z  X  C  V  B  N  M
```

Interpretation:

- `DEL` / Backspace sits at the far right of the top letter row, analogous to Backspace on a physical keyboard.
- `ENTER` sits at the far right of the home row, analogous to Enter/Return on a physical keyboard.
- the A-row is visually indented relative to Q-row
- the Z-row is visually indented further relative to A-row
- no SHIFT key is needed because the game always displays/accepts uppercase A-Z

## Labels

Preferred visible labels:

- Backspace: `DEL` or `⌫`; if using the symbol, provide `aria-label="Delete"`
- Enter: `ENTER`

The exact glyph may be adjusted for readability, but control meaning must be immediately obvious.

## Sizing

- letter keys should remain approximately uniform squares/rounded rectangles
- `DEL` and `ENTER` may be wider than letter keys
- do not shrink all letter keys merely to fit long control labels
- on small iPhones, shorten the visible delete label to `⌫` if needed
- maintain comfortable touch targets; target roughly 40–44 CSS px where viewport permits
- gaps may reduce slightly on narrow screens before key sizes become too small

## Responsive behavior

The keyboard must remain usable in:

- small iPhone portrait
- modern iPhone portrait
- 11-inch iPad portrait/landscape
- Mac browser

Preferred implementation approach:

- CSS grid or flex rows with explicit stagger/indent values
- avoid hardcoded pixel offsets that only work at one viewport width
- use CSS custom properties for key width, gap, and row indent
- allow `DEL` / `ENTER` widths to scale independently

Example conceptual CSS variables:

```css
--key-w: clamp(28px, 8.7vw, 46px);
--key-gap: clamp(3px, 1vw, 6px);
--row2-indent: calc(var(--key-w) * .45);
--row3-indent: calc(var(--key-w) * .95);
```

These values are illustrative; tune by actual device testing.

## Interaction

Both on-screen and physical keyboard input must map to the same game handlers:

- A-Z -> letter input
- Backspace / Delete UI -> remove last entered letter
- Enter / Return UI -> submit current five-letter guess

Do not duplicate game logic between physical and virtual keyboard handlers.

## Keyboard state colors

Retain the existing correct/present/absent color feedback for letter keys.

Action keys (`DEL`, `ENTER`) should not inherit letter-state colors.

BOSS-mode banned-letter feedback should remain visually obvious on the corresponding letter key without disturbing the action keys.

## Acceptance checks

- `DEL` is no longer beside M on the bottom row
- `ENTER` is no longer left of Z
- rows visually resemble staggered QWERTY
- controls are reachable and obvious on touch devices
- no essential key is clipped at 320px-class viewport widths
- physical keyboard behavior is unchanged
- Safari portrait and landscape resizing does not break row alignment

