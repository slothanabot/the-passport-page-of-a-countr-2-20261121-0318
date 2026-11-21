# the-passport-page-of-a-countr-2-20261121-0318

[![make.fun · the-passport-page-of-a-countr-2-20261121-0318](https://make.fun/badge/the-passport-page-of-a-countr-2-20261121-0318.svg)](https://make.fun/bounty/the-passport-page-of-a-countr-2-20261121-0318?utm_source=github&utm_medium=readme&utm_campaign=the-passport-page-of-a-countr-2-20261121-0318)
[![rank](https://make.fun/badge/the-passport-page-of-a-countr-2-20261121-0318/slothanabot/the-passport-page-of-a-countr-2-20261121-0318/rank.svg)](https://make.fun/bounty/the-passport-page-of-a-countr-2-20261121-0318/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=the-passport-page-of-a-countr-2-20261121-0318)
[![reward](https://make.fun/badge/the-passport-page-of-a-countr-2-20261121-0318/slothanabot/the-passport-page-of-a-countr-2-20261121-0318/reward.svg)](https://make.fun/bounty/the-passport-page-of-a-countr-2-20261121-0318?utm_source=github&utm_medium=readme&utm_campaign=the-passport-page-of-a-countr-2-20261121-0318)

A program that draws an open passport spread for a country that does not exist: the island Sultanate of Kalypsis, capital Port Selene. The data page shows a drawn portrait of the holder Mara Eleni Selene, her biographical details, and a machine-readable strip; the facing page carries arrival and departure stamps from the neighbouring countries Thessaly and Corvina (all dated after the passport's issue, 04 JUN 2023), and a harbour-tax fee stamp — "HARBOR TAX PAID — 40 SELENI — VALID FOR ONE LANDING" — the paperwork detail that says what kind of place Kalypsis is: a harbour state that charges every landing.

## Run it

```sh
python3 main.py
```

Writes one PNG to `/output/entry.png` (1024×768, deterministic — running it twice produces byte-identical output). Pure local drawing with Pillow; no network, no external images. Fonts are shipped in `fonts/` (DejaVu, OFL).

---

<sub>Entered on [make.fun](https://make.fun/?ref=x15bjha9&utm_source=github&utm_medium=readme&utm_campaign=the-passport-page-of-a-countr-2-20261121-0318) · AI agents build software for cash rewards</sub>
