# Routing v3: measured header maps, ZERO jumpers, planned 48 x 17 board, default component positions.
# IN header rot 0 (GND row toward row 0, as v2). OUT header rot 1 (mounted 180 degrees: GND row toward
# the bottom, reads R- R+ / L- L+ / GND GND top to bottom). T1 MIRRORED (hot 4 / cold 1, out hot 11 /
# cold 7). T2 normal (hot 1 / cold 4, out hot 7 / cold 11). v2 had T2 mirrored instead.
# Found by solver/negotiate.py (r01_m10 seed 7), tidied by solver/cpsat_route.py --opt.
# Check: python3 solver/check_routes.py solver/routes_v3.py
CONFIG = {'in_rot': 0, 'out_rot': 1, 'm1': 1, 'm2': 0, 'cols': 48, 't1': 6, 't2': 27, 'trow': 0, 'in_col': 1, 'out_col': 45, 'hrow': 7}
IN_C, OUT_C, BR_C, SH_C = "#1F6FB2", "#D9541E", "#7A7A7A", "#2E8B57"
IN_MAP  = {(1, 7): 'GND\nn.c.', (2, 7): 'GND\nn.c.', (1, 8): 'L+', (2, 8): 'L-', (1, 9): 'R+', (2, 9): 'R-'}
OUT_MAP = {(45, 9): 'GND', (46, 9): 'GND', (45, 8): 'L-', (46, 8): 'L+', (45, 7): 'R-', (46, 7): 'R+'}
# (label, colour, points, is_jumper)
routes = [
 ('L+ : IN -> T1 pin 4 (mirrored)', IN_C, [(1, 8), (0, 8), (0, 6), (3, 6), (3, 7), (6, 7)], False),
 ('L- : IN -> T1 pin 1 (mirrored)', IN_C, [(2, 8), (4, 8), (4, 13), (6, 13)], False),
 ('R+ : IN -> T2 pin 1', IN_C, [(1, 9), (1, 16), (25, 16), (25, 13), (27, 13)], False),
 ('R- : IN -> T2 pin 4', IN_C, [(2, 9), (2, 15), (24, 15), (24, 12), (28, 12), (28, 7), (27, 7)], False),
 ('T1 bridge 3-6', BR_C, [(6, 9), (7, 9), (7, 3), (6, 3)], False),
 ('T1 bridge 8-12', BR_C, [(20, 11), (18, 11), (18, 3), (20, 3)], False),
 ('T2 bridge 3-6', BR_C, [(27, 9), (26, 9), (26, 3), (27, 3)], False),
 ('T2 bridge 8-12', BR_C, [(41, 11), (39, 11), (39, 3), (41, 3)], False),
 ('L+ : T1 pin 11 -> OUT (mirrored)', OUT_C, [(20, 5), (21, 5), (21, 0), (37, 0), (37, 1), (44, 1), (44, 3), (47, 3), (47, 8), (46, 8)], False),
 ('L- : T1 pin 7 -> OUT (mirrored)', OUT_C, [(20, 13), (21, 13), (21, 10), (19, 10), (19, 6), (22, 6), (22, 1), (36, 1), (36, 2), (37, 2), (37, 14), (42, 14), (42, 10), (40, 10), (40, 8), (45, 8)], False),
 ('R+ : T2 pin 7 -> OUT', OUT_C, [(41, 13), (41, 12), (38, 12), (38, 2), (42, 2), (42, 4), (46, 4), (46, 7)], False),
 ('R- : T2 pin 11 -> OUT', OUT_C, [(41, 5), (45, 5), (45, 7)], False),
 ('shield T1 pin 9 -> OUT GND', SH_C, [(20, 9), (23, 9), (23, 2), (35, 2), (35, 16), (45, 16), (45, 9)], False),
 ('shield T2 pin 9 -> OUT GND', SH_C, [(41, 9), (45, 9)], False),
]
