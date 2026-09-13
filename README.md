# somnex-iso-board

Perfboard routing for a two-transformer (Lundahl LL1517) FOH isolation board that sits between a
WMD Performance Mixer MKII rear balanced-out header and an Intellijel Stereo Out Jacks 1U tile.

Start with `CLAUDE.md` (the task), then `docs/DESIGN-SPEC.md` (all constraints) and
`docs/STATE-OF-PLAY.md` (where things stand). Current drawings and bench sheet (v3, no jumpers) are in
`outputs/current/`; the 1-jumper v2 set is in `outputs/v2-1-jumper/`.

```
pip install -r requirements.txt
python3 solver/check_routes.py solver/routes_v3.py
python3 solver/cpsat_route.py 0 0 0 0 120
python3 drawing/routing.py && python3 drawing/routing.py --mirror
python3 drawing/build_doc.py
```
