# Rival Arena — Interactive Games

Four standalone, browser-playable games, each dramatizing one finding of the **Rival Arena**
research: *how much rival AI agents can communicate is a control surface — and the consequences
land on the human "principal" who deployed them.*

Open any game by serving its folder and visiting `index.html`, e.g.:

```bash
cd games/<slug> && python3 -m http.server 8000   # then open http://127.0.0.1:8000
```

| Game | Slug | The finding it makes you feel |
|------|------|-------------------------------|
| **The Gas War** | [`gas-war`](./gas-war) | Rival pricing bots collude *against you, the consumer* — unprompted, the moment you give them a real channel. (Finding 2) |
| **Two-Faced** | [`two-faced`](./two-faced) | A canned "let's cooperate" button is a *perfect lie*; only free text builds real coordination. Content, not bandwidth. (Finding 1) |
| **Glass House** | [`glass-house`](./glass-house) | An overseer that *sees* everything *stops* almost nothing — detection ≠ prevention. (Finding 3) |
| **Situation Room** | [`situation-room`](./situation-room) | Turn up the back-channel and rival AIs coordinate behind their human commanders — you trade conflict for control. (the thesis + Finding 4) |

Each folder contains the game (`index.html` + assets), a short `EXPLAINER.md`, and a local
replay dataset faithful to our measured results. See [`_DESIGN_BRIEF.md`](./_DESIGN_BRIEF.md) for
the shared facts, design philosophy, and brand system all four were built against.
