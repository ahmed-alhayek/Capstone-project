
# Mindful — Premium Mental Wellness UX

A high-fidelity, front-end-only build of an emotionally intelligent mental health companion. No real backend — mocked data throughout so we can focus on design system quality, motion, and flow.

## Design system foundation

**Palette (light & dark, OKLCH, WCAG AA)**
- Sage (primary) — calm, trust
- Slate (neutrals / text)
- Muted lavender (accent / moments of warmth)
- Soft cream + deep charcoal surfaces
- Semantic tokens: `surface`, `surface-elevated`, `surface-glass`, `support` (for crisis — muted amber/clay, never alarm red)

**Typography**
- Inter via Google Fonts, tight tracking on display, generous line-height on body
- Scale: 12 / 14 / 16 / 18 / 22 / 28 / 36 / 48

**Spacing & elevation**
- 4pt grid; radii 12 / 20 / 28
- Three elevation layers with soft, long-tail shadows
- Glass surfaces use low-opacity tint + backdrop blur — applied sparingly (modals, telemetry chips, floating nav)

**Motion**
- Global easing: cubic-bezier(0.22, 1, 0.36, 1), 280–420ms
- Respects `prefers-reduced-motion`
- Reusable: breathing pulse, gentle rise-in, soft scale

**Theme toggle**
- System default, persisted in localStorage, animated sun/moon in header

## Routes

- `/` — Welcome / landing with privacy-forward hero
- `/login`, `/register` — Frictionless auth (UI only, no backend)
- `/chat` — Primary hub (text + voice modes)
- `/summary` — Post-session recap
- `/history` — Longitudinal analytics
- `/crisis` — Triggered automatically when mocked score drops <40

## Screens

**1. Auth**
Two-column on desktop (form + reassuring privacy pillars: "End-to-end private", "Never sold", "You own your data"). Single column on mobile. Social + email, no dark patterns, no marketing fluff.

**2. Chat hub**
- Left rail (desktop): session list, mode toggle, settings
- Center: message stream — AI messages on soft sage surface, user messages on lavender-tinted; whisper-light timestamps; no avatars shouting
- Top-right telemetry pill: current mood word + small score ring, updates gently every few turns (mocked drift). Tap to expand into a detail sheet.
- **Voice mode**: full-screen takeover with a central orb that breathes (idle), ripples (recording), and shimmers (processing). States announced via aria-live.
- Composer: textarea with soft focus ring, mic toggle, send

**3. Post-session summary**
- Hero line: empathetic narrative ("You worked through a lot today.")
- Below: three soft cards — mood shift, topics, suggested reflection
- Quantitative data presented as quiet rings + sparklines, never bar-chart-heavy
- Primary CTA: "Save to journal" · secondary: "Share with therapist"

**4. History dashboard**
- Time range selector (week / month / 90d)
- Mood trend line chart (recharts) with smoothed curve, AA-contrast tooltips
- Calendar heatmap of session intensity
- Session list with mood glyphs, not numbers first
- Insight cards — narrative-led ("Evenings are consistently lighter for you")

**5. Crisis state (<40 score)**
- Soft interstitial, not a modal slam
- Warm amber/clay tones, never red
- Copy: "We noticed things feel heavy. You don't have to be alone with this."
- Three clear actions: Talk to a human now (988/Samaritans links), Grounding exercise (60-sec breathing), Keep chatting with gentler pacing
- Dismissible but re-surfaces if score stays low

## Component library (shadcn-based, restyled)
Buttons, inputs, cards, dialogs, sheets, toast, tabs, slider, switch, tooltip, avatar, badge, separator — all re-tokenized. New: `GlassPanel`, `BreathingOrb`, `MoodRing`, `TelemetryPill`, `InsightCard`, `CrisisBanner`.

All states (hover / active / disabled / focus-visible) explicitly designed, with visible focus rings meeting AA.

## Mock data layer
`src/lib/mock.ts` — seeded sessions, mood timeline, canned AI replies with slight delay, drifting score generator with a "crisis demo" toggle in settings so the crisis flow is reviewable on demand.

## Out of scope (per change-control rule)
No real auth, AI, STT/TTS, persistence, or analytics. If any of those are wanted later, I'll propose them separately with impact notes before implementing.
