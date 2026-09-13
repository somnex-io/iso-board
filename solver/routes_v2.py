# Routing v2: measured header maps (both: top row GND GND / middle L+ L- / bottom R+ R-)
IN_C, OUT_C, BR_C, SH_C = "#1F6FB2", "#D9541E", "#7A7A7A", "#2E8B57"
IN_MAP  = {(1,7):"GND\nn.c.", (2,7):"GND\nn.c.", (1,8):"L+", (2,8):"L-", (1,9):"R+", (2,9):"R-"}
OUT_MAP = {(45,7):"GND", (46,7):"GND", (45,8):"L+", (46,8):"L-", (45,9):"R+", (46,9):"R-"}
# (label, colour, points, is_jumper)
routes = [
 # IN domain
 ("L- : IN -> T1 pin 4", IN_C, [(2,8),(4,8),(4,7),(6,7)], False),
 ("L+ : IN -> T1 pin 1", IN_C, [(1,8),(0,8),(0,14),(5,14),(5,13),(6,13)], False),
 ("R+ : IN -> T2 pin 4 (mirrored)", IN_C, [(1,9),(1,12),(7,12),(7,15),(28,15),(28,7),(27,7)], False),
 ("R- : IN -> T2 pin 1 (mirrored)", IN_C, [(2,9),(2,10),(8,10),(8,14),(27,14),(27,13)], False),
 # bridges
 ("T1 bridge 3-6", BR_C, [(6,9),(7,9),(7,3),(6,3)], False),
 ("T1 bridge 8-12", BR_C, [(20,11),(19,11),(19,3),(20,3)], False),
 ("T2 bridge 3-6", BR_C, [(27,9),(26,9),(26,3),(27,3)], False),
 ("T2 bridge 8-12", BR_C, [(41,11),(40,11),(40,3),(41,3)], False),
 # OUT domain
 ("L- : T1 pin 11 -> OUT", OUT_C, [(20,5),(21,5),(21,0),(47,0),(47,8),(46,8)], False),
 ("L+ : T1 pin 7 -> OUT", OUT_C, [(20,13),(23,13),(23,2),(44,2),(44,8),(45,8)], False),
 ("R+ : T2 pin 11 -> OUT (mirrored)", OUT_C, [(41,5),(41,4),(43,4),(43,9),(45,9)], False),
 ("R- : T2 pin 7 -> OUT (mirrored)", OUT_C, [(41,13),(46,13),(46,9)], False),
 # shields
 ("shield T1 pin 9 -> OUT GND", SH_C, [(20,9),(22,9),(22,1),(45,1),(45,7)], False),
 ("shield T2 pin 9 (bare part)", SH_C, [(41,9),(41,8),(42,8),(42,6)], False),
 ("shield T2 JUMPER (insulated) -> joins T1 shield", SH_C, [(42,6),(45,6)], True),
]
