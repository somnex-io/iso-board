# Routing v3: measured header maps, ZERO jumpers, planned 50 x 19 board, default component positions.
# 50 x 19 is the 48 x 17 layout moved +1 column and +1 row, leaving the outer ring of holes empty as a
# sacrificial border. Same topology and wire shapes as the 48 x 17 version (commit 0a305c9).
# IN header rot 0 (GND row toward row 0, as v2). OUT header rot 1 (mounted 180 degrees: GND row toward
# the bottom, reads R- R+ / L- L+ / GND GND top to bottom). T1 MIRRORED (hot 4 / cold 1, out hot 11 /
# cold 7). T2 normal (hot 1 / cold 4, out hot 7 / cold 11). v2 had T2 mirrored instead.
# Found by solver/negotiate.py (r01_m10 seed 7), tidied by solver/cpsat_route.py --opt.
# Check: python3 solver/check_routes.py solver/routes_v3.py
CONFIG = {'in_rot': 0, 'out_rot': 1, 'm1': 1, 'm2': 0, 'cols': 50, 'rows': 19, 't1': 7, 't2': 28, 'trow': 1, 'in_col': 2, 'out_col': 46, 'hrow': 8}
IN_C, OUT_C, BR_C, SH_C = "#1F6FB2", "#D9541E", "#7A7A7A", "#2E8B57"
IN_MAP  = {(2, 8): 'GND\nn.c.', (3, 8): 'GND\nn.c.', (2, 9): 'L+', (3, 9): 'L-', (2, 10): 'R+', (3, 10): 'R-'}
OUT_MAP = {(46, 10): 'GND', (47, 10): 'GND', (46, 9): 'L-', (47, 9): 'L+', (46, 8): 'R-', (47, 8): 'R+'}
# (label, colour, points, is_jumper)
routes = [
 ('L+ : IN -> T1 pin 4 (mirrored)', IN_C, [(2, 9), (1, 9), (1, 7), (4, 7), (4, 8), (7, 8)], False),
 ('L- : IN -> T1 pin 1 (mirrored)', IN_C, [(3, 9), (5, 9), (5, 14), (7, 14)], False),
 ('R+ : IN -> T2 pin 1', IN_C, [(2, 10), (2, 17), (26, 17), (26, 14), (28, 14)], False),
 ('R- : IN -> T2 pin 4', IN_C, [(3, 10), (3, 16), (25, 16), (25, 13), (29, 13), (29, 8), (28, 8)], False),
 ('T1 bridge 3-6', BR_C, [(7, 10), (8, 10), (8, 4), (7, 4)], False),
 ('T1 bridge 8-12', BR_C, [(21, 12), (19, 12), (19, 4), (21, 4)], False),
 ('T2 bridge 3-6', BR_C, [(28, 10), (27, 10), (27, 4), (28, 4)], False),
 ('T2 bridge 8-12', BR_C, [(42, 12), (40, 12), (40, 4), (42, 4)], False),
 ('L+ : T1 pin 11 -> OUT (mirrored)', OUT_C, [(21, 6), (22, 6), (22, 1), (38, 1), (38, 2), (45, 2), (45, 4), (48, 4), (48, 9), (47, 9)], False),
 ('L- : T1 pin 7 -> OUT (mirrored)', OUT_C, [(21, 14), (22, 14), (22, 11), (20, 11), (20, 7), (23, 7), (23, 2), (37, 2), (37, 3), (38, 3), (38, 15), (43, 15), (43, 11), (41, 11), (41, 9), (46, 9)], False),
 ('R+ : T2 pin 7 -> OUT', OUT_C, [(42, 14), (42, 13), (39, 13), (39, 3), (43, 3), (43, 5), (47, 5), (47, 8)], False),
 ('R- : T2 pin 11 -> OUT', OUT_C, [(42, 6), (46, 6), (46, 8)], False),
 ('shield T1 pin 9 -> OUT GND', SH_C, [(21, 10), (24, 10), (24, 3), (36, 3), (36, 17), (46, 17), (46, 10)], False),
 ('shield T2 pin 9 -> OUT GND', SH_C, [(42, 10), (46, 10)], False),
]
