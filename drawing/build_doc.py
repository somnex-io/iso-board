#!/usr/bin/env python3
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
                                Image, NextPageTemplate, PageBreak, KeepTogether)
from reportlab.graphics.shapes import Drawing, Rect, Circle, String, Line

OUT = "outputs/FOH-iso-board_bench-sheet.pdf"

# ---------- styles ----------
H1 = ParagraphStyle("H1", fontName="Helvetica-Bold", fontSize=16, leading=20, spaceAfter=4)
H2 = ParagraphStyle("H2", fontName="Helvetica-Bold", fontSize=11.5, leading=14, spaceBefore=6, spaceAfter=2)
B = ParagraphStyle("B", fontName="Helvetica", fontSize=9.6, leading=12.4)
SM = ParagraphStyle("SM", fontName="Helvetica", fontSize=8.4, leading=10.6, textColor=colors.HexColor("#444"))
CK = ParagraphStyle("CK", fontName="Helvetica", fontSize=8.8, leading=10.8, leftIndent=14, firstLineIndent=-14, spaceAfter=1.0)
# checklist page only: slightly tighter headings and table so the build order fits on page 4
H2C = ParagraphStyle("H2C", parent=H2, spaceBefore=3, spaceAfter=1)
CELLC = ParagraphStyle("CELLC", fontName="Helvetica", fontSize=8.0, leading=9.4)
CELL = ParagraphStyle("CELL", fontName="Helvetica", fontSize=8.6, leading=10.6)
CELLB = ParagraphStyle("CELLB", fontName="Helvetica-Bold", fontSize=8.6, leading=10.6)

import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import palette as PAL                  # same wire colours as routing.py
IN_C, OUT_C, SH_C, BR_C = (colors.HexColor(c) for c in (PAL.IN_C, PAL.OUT_C, PAL.SH_C, PAL.BR_C))

def grid_style(header=True):
    st = [("FONT", (0, 0), (-1, -1), "Helvetica", 8.6),
          ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#999")),
          ("VALIGN", (0, 0), (-1, -1), "TOP"),
          ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
    if header:
        st += [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8ECF5")), ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 8.6)]
    return TableStyle(st)

def P(t, s=B): return Paragraph(t, s)
def ck(t): return Paragraph("[&nbsp;&nbsp;]&nbsp; " + t, CK)

# ---------- LL1517 top-view pin drawing (own drawing, from datasheet numbers) ----------
def pin_drawing():
    d = Drawing(230, 150)
    d.scale(0.7, 0.7)
    d.width, d.height = 161, 105
    d.add(Rect(45, 15, 140, 120, strokeColor=colors.black, fillColor=colors.HexColor("#F7F5EE"), strokeWidth=1))
    d.add(String(115, 78, "LL1517", fontName="Helvetica-Bold", fontSize=9, textAnchor="middle"))
    d.add(String(115, 66, "top view (component side)", fontName="Helvetica", fontSize=7, textAnchor="middle", fillColor=colors.HexColor("#555")))
    left = {6: 125, 5: 105, 4: 85, 3: 65, 2: 45, 1: 25}
    right = {12: 125, 11: 105, 9: 65, 8: 45, 7: 25}
    for pin, y in left.items():
        d.add(Circle(60, y, 5, strokeColor=colors.black, fillColor=colors.white))
        d.add(String(60, y - 2.6, str(pin), fontName="Helvetica-Bold", fontSize=6.5, textAnchor="middle"))
    for pin, y in right.items():
        d.add(Circle(170, y, 5, strokeColor=colors.black, fillColor=colors.white))
        d.add(String(170, y - 2.6, str(pin), fontName="Helvetica-Bold", fontSize=6.5, textAnchor="middle"))
    d.add(String(60, 4, "PRIMARY (WMD)", fontName="Helvetica-Bold", fontSize=6.5, textAnchor="middle", fillColor=IN_C))
    d.add(String(170, 4, "SECONDARY (tile)", fontName="Helvetica-Bold", fontSize=6.5, textAnchor="middle", fillColor=OUT_C))
    d.add(String(115, 140, "rows 35.56 mm apart = 14 holes;  pins 5.08 mm = 2 holes", fontName="Helvetica", fontSize=6.5, textAnchor="middle", fillColor=colors.HexColor("#555")))
    d.add(String(10, 127, "+", fontName="Helvetica-Bold", fontSize=8))
    d.add(String(10, 27, "+", fontName="Helvetica-Bold", fontSize=8))
    d.add(String(206, 127, "+", fontName="Helvetica-Bold", fontSize=8))
    d.add(String(206, 27, "+", fontName="Helvetica-Bold", fontSize=8))
    return d

# ---------- document ----------
doc = BaseDocTemplate(OUT, pagesize=A4, leftMargin=16 * mm, rightMargin=16 * mm, topMargin=14 * mm, bottomMargin=14 * mm,
                      title="FOH isolation board - bench sheet", author="Somnex")
W, H = A4
LW, LH = landscape(A4)

def footer(canv, docu):
    canv.saveState()
    canv.setFont("Helvetica", 7.5)
    canv.setFillColor(colors.HexColor("#666"))
    pw = canv._pagesize[0]
    canv.drawString(16 * mm, 8 * mm, "Somnex  |  WMD PM MKII -> 2x Lundahl LL1517 -> Intellijel Stereo Out Jacks 1U  |  bench sheet, Sept 2026")
    canv.drawRightString(pw - 16 * mm, 8 * mm, "page %d" % docu.page)
    canv.restoreState()

portrait = PageTemplate("portrait", frames=[Frame(16 * mm, 14 * mm, W - 32 * mm, H - 28 * mm, id="p")], onPage=footer)
land = PageTemplate("land", frames=[Frame(12 * mm, 12 * mm, LW - 24 * mm, LH - 24 * mm, id="l")], pagesize=landscape(A4), onPage=footer)
doc.addPageTemplates([portrait, land])

story = []

# ---------- layout data: everything layout-specific below comes from the routes file ----------
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROUTES = sys.argv[sys.argv.index("--routes") + 1] if "--routes" in sys.argv else os.path.join(HERE, "..", "solver", "routes_v3.py")
RF = {}; exec(open(ROUTES).read(), RF)
CFG = dict(dict(in_rot=0, out_rot=0, m1=0, m2=1, cols=48, rows=17, t1=6, t2=27, trow=0, in_col=1, out_col=45, hrow=7), **RF.get("CONFIG", {}))
ROUTES_L = RF["routes"]
assert not any(r[3] for r in ROUTES_L), "this sheet covers jumper-free layouts; the 1-jumper v2 sheet is in outputs/v2-1-jumper/"
COLS, ROWS, TR, HR = CFG["cols"], CFG["rows"], CFG["trow"], CFG["hrow"]
SIZE = f"{COLS} x {ROWS} holes ({COLS * 2.54:.0f} x {ROWS * 2.54:.0f} mm)"
PRIM = {6: 3, 5: 5, 4: 7, 3: 9, 2: 11, 1: 13}; SEC = {12: 3, 11: 5, 9: 9, 8: 11, 7: 13}
TPOS = {"T1": CFG["t1"], "T2": CFG["t2"]}
MIR = {"T1": CFG["m1"], "T2": CFG["m2"]}
CH = {"T1": "L", "T2": "R"}
def pin(t, n): return (TPOS[t], PRIM[n] + TR) if n in PRIM else (TPOS[t] + 14, SEC[n] + TR)
NAMES = {pin(t, n): f"{t} pin {n}" for t in TPOS for n in [*PRIM, *SEC]}
for (c, r), lab in RF["IN_MAP"].items(): NAMES[(c, r)] = "IN " + lab.split("\n")[0]
for (c, r), lab in RF["OUT_MAP"].items(): NAMES[(c, r)] = "OUT " + lab.split("\n")[0]
def xy(c): return f"({c[0]},{c[1]})"
def name(c): return f"{NAMES[c]} {xy(c)}" if c in NAMES else xy(c)
def describe(pts):
    """Corner holes in order; the wire runs straight between them."""
    via = ", ".join(xy(c) for c in pts[1:-1])
    return f"from {name(pts[0])}" + (f" via {via}" if via else "") + f" to {name(pts[-1])}."
def longest(pts):
    (a, b), (c, d) = max(zip(pts, pts[1:]), key=lambda s: abs(s[0][0] - s[1][0]) + abs(s[0][1] - s[1][1]))
    return f"row {b}" if b == d else f"col {a}"
IN_W = [r for r in ROUTES_L if ": IN" in r[0]]
OUT_W = [r for r in ROUTES_L if "-> OUT" in r[0] and not r[0].startswith("shield")]
SH_W = [r for r in ROUTES_L if r[0].startswith("shield")]
BR_W = [r for r in ROUTES_L if "bridge" in r[0]]
def bridge_col(pts): return max(zip(pts, pts[1:]), key=lambda s: abs(s[0][1] - s[1][1]))[0][0]
BRIDGES = ", ".join(f"{r[0].replace(' bridge', '')} on col {bridge_col(r[2])}" for r in BR_W)
GND_USED = sorted({r[2][-1] for r in SH_W if r[2][-1] in NAMES and NAMES[r[2][-1]] == "OUT GND"})
GND_FREE = sorted(c for c, lab in RF["OUT_MAP"].items() if lab.startswith("GND") and c not in GND_USED)
def role(t, n):
    ch, m = CH[t], MIR[t]
    return {1: f"IN {ch}{'-' if m else '+'} ({'cold' if m else 'hot'})", 4: f"IN {ch}{'+' if m else '-'} ({'hot' if m else 'cold'})",
            7: f"OUT {ch}{'-' if m else '+'} ({'ring' if m else 'tip'})", 11: f"OUT {ch}{'+' if m else '-'} ({'tip' if m else 'ring'})",
            3: "bridge to 6", 6: "bridge from 3", 8: "bridge to 12", 12: "bridge from 8", 2: "nothing", 5: "nothing"}[n]
def shield_end(t):
    r = next(r for r in SH_W if r[2][0] == pin(t, 9))
    end = r[2][-1]
    return f"OUT GND {xy(end)}" if NAMES.get(end) == "OUT GND" else f"joins the other shield wire at {xy(end)}"
MIRRORED = [t for t in TPOS if MIR[t]]
ROT = lambda r: "GND pins toward the BOTTOM edge (row %d), i.e. turned 180°" % (HR + 2) if r else "GND pins toward the top edge (row %d)" % HR

# ===== PAGE 1: reference =====
story.append(P("FOH isolation board: bench sheet, v3 (measured headers, no jumpers)", H1))
story.append(P(f"Two Lundahl LL1517 transformers on a {COLS} x {ROWS} hole perfboard ({COLS * 2.54:.0f} x {ROWS * 2.54:.0f} mm), sitting in the ribbon between the "
               "WMD's rear balanced-out header and the Stereo Out Jacks 1U tile. 1:1, passive, galvanically isolated. "
               "Four signals cross through iron; no ground ever crosses. No insulated jumpers: every wire is bare and nothing crosses.", B))

story.append(P("1. LL1517 pin key", H2))
hdr_t = lambda t: f"<b>{t} ({'LEFT' if t == 'T1' else 'RIGHT'}){', mirrored' if MIR[t] else ''}</b>"
rows = [[P("<b>Pin</b>", CELL), P("<b>What it is</b>", CELL), P(hdr_t("T1"), CELL), P(hdr_t("T2"), CELL)]]
for n, what in [(1, "primary A start (+)"), (3, "primary A end"), (6, "primary B start (+)"), (4, "primary B end")]:
    rows.append([P(str(n), CELLB), P(what, CELL), P(role("T1", n), CELL), P(role("T2", n), CELL)])
rows.append([P("2, 5", CELLB), P("centre taps", CELL), P("nothing", CELL), P("nothing", CELL)])
for n, what in [(7, "secondary A start (+)"), (8, "secondary A end"), (12, "secondary B start (+)"), (11, "secondary B end")]:
    rows.append([P(str(n), CELLB), P(what, CELL), P(role("T1", n), CELL), P(role("T2", n), CELL)])
rows.append([P("9", CELLB), P("core + housing", CELL), P(shield_end("T1"), CELL), P(shield_end("T2"), CELL)])
pin_tbl = Table(rows, colWidths=[11 * mm, 34 * mm, 34 * mm, 34 * mm])
pin_tbl.setStyle(grid_style())
side = Table([[pin_drawing(), pin_tbl]], colWidths=[62 * mm, 116 * mm])
side.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
story.append(side)
if MIRRORED:
    t = MIRRORED[0] if len(MIRRORED) == 1 else "T1 and T2"
    story.append(P(f"<b>{t} {'is' if len(MIRRORED) == 1 else 'are'} wired mirrored on purpose:</b> both primary and secondary are reversed. "
                   "Reversing one side alone would flip that channel; reversing both cancels out, so L and R stay in phase. "
                   f"It is what lets the wires reach the headers without crossing. (In v2 it was T2; in v3 it is {t}.) "
                   "Bridges are the same on both: 3-6 and 8-12, never 3-4.", SM))

story.append(P("2. Header pin maps (measured 13 Sept)", H2))
story.append(P("Both headers measured the same, viewed from the component side: top row GND, GND; middle row L+, L-; bottom row R+, R-. "
               f"On this board the IN header is fitted with its {ROT(CFG['in_rot'])} and the OUT header with its {ROT(CFG['out_rot'])}, "
               f"so the holes read as below. Column 0 is the IN end, row 0 the top edge. IN header = columns {CFG['in_col']}-{CFG['in_col'] + 1}, "
               f"OUT header = columns {CFG['out_col']}-{CFG['out_col'] + 1}, both in rows {HR}-{HR + 2}.", B))
def hcell(c, mp, side_in):
    lab = mp[c].split("\n")[0]
    if lab.startswith("GND"):
        if side_in or c in GND_FREE: return "GND, no wire"
        ends = [f"T{r[2][0] == pin('T2', 9) and 2 or 1}" for r in SH_W if r[2][-1] == c]
        return "GND (both shields)" if len(ends) == 2 else f"GND ({ends[0]} shield)"
    return lab
hrows = [[P("<b>IN (WMD)</b>", CELL), P(f"<b>col {CFG['in_col']}</b>", CELL), P(f"<b>col {CFG['in_col'] + 1}</b>", CELL), "",
          P("<b>OUT (tile)</b>", CELL), P(f"<b>col {CFG['out_col']}</b>", CELL), P(f"<b>col {CFG['out_col'] + 1}</b>", CELL)]]
for r in (HR, HR + 1, HR + 2):
    ic, oc = CFG["in_col"], CFG["out_col"]
    hrows.append([P(f"row {r}", CELL), P(hcell((ic, r), RF["IN_MAP"], True), CELL), P(hcell((ic + 1, r), RF["IN_MAP"], True), CELL), "",
                  P(f"row {r}", CELL), P(hcell((oc, r), RF["OUT_MAP"], False), CELL), P(hcell((oc + 1, r), RF["OUT_MAP"], False), CELL)])
hdr = Table(hrows, colWidths=[22 * mm, 31 * mm, 31 * mm, 6 * mm, 22 * mm, 31 * mm, 31 * mm])
hdr.setStyle(TableStyle([("FONT", (0, 0), (-1, -1), "Helvetica", 8.6), ("GRID", (0, 0), (2, -1), 0.4, colors.HexColor("#999")),
                         ("GRID", (4, 0), (6, -1), 0.4, colors.HexColor("#999")), ("BACKGROUND", (0, 0), (2, 0), colors.HexColor("#DCE7F5")),
                         ("BACKGROUND", (4, 0), (6, 0), colors.HexColor("#F8E3D8")), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                         ("LEFTPADDING", (3, 0), (3, -1), 0), ("RIGHTPADDING", (3, 0), (3, -1), 0)]))
story.append(hdr)
def orient(label, rot, dev):
    if rot:
        return (f"fit the {label} header TURNED 180°: its two GND pins toward the bottom edge (row {HR + 2}), and its notch facing the same way "
                f"as the notch on the {dev} does when you hold the {dev} with its GND pins DOWN")
    return (f"fit the {label} header with its two GND pins toward the top edge (row {HR}), and its notch facing the same way as the notch "
            f"on the {dev} does when you hold the {dev} with its GND pins up")
story.append(P(f"<b>Orientation:</b> {orient('IN', CFG['in_rot'], 'WMD')}. Then {orient('OUT', CFG['out_rot'], 'tile')}. "
               + ("The OUT header is turned round compared with v2 and with the IN header; the ribbon plug turns with it, so every signal "
                  "still lands where the drawing expects it. Step B4 checks this with the meter before any wiring. " if CFG["out_rot"] or CFG["in_rot"] else "")
               + "Both ribbons pin 1 to pin 1, stripe on the same side at both ends; make them different lengths.", SM))
story.append(P("3. Sharpie key for the underside", H2))
runs = lambda ws: ", ".join(f"{r[0].split(' :')[0]} {longest(r[2])}" for r in ws)
pick = lambda ws, ch: [r for r in ws if r[0][0] == ch]
# key labels wear the wire colour, except grey: the bridge grey is too light for text
key = Table([
    [P(f"<font color='{PAL.IN_L}'><b>BLUE</b></font>", CELL), P(f"WMD side, LEFT channel (IN L+, L-). Long runs: {runs(pick(IN_W, 'L'))}.", CELL)],
    [P(f"<font color='{PAL.IN_R}'><b>PURPLE</b></font>", CELL), P(f"WMD side, RIGHT channel (IN R+, R-). Long runs: {runs(pick(IN_W, 'R'))}.", CELL)],
    [P(f"<font color='{PAL.OUT_L}'><b>RED</b></font>", CELL), P(f"Tile side, LEFT channel (OUT L+, L-). Long runs: {runs(pick(OUT_W, 'L'))}.", CELL)],
    [P(f"<font color='{PAL.OUT_R}'><b>ORANGE</b></font>", CELL), P(f"Tile side, RIGHT channel (OUT R+, R-). Long runs: {runs(pick(OUT_W, 'R'))}.", CELL)],
    [P(f"<font color='{PAL.SH_C}'><b>GREEN</b></font>", CELL), P("Shields: pin 9 of each transformer to OUT GND "
       + " and ".join(xy(c) for c in GND_USED) + ". Longest runs: " + ", ".join(f"T{1 if r[2][0] == pin('T1', 9) else 2} {longest(r[2])}" for r in SH_W) + ".", CELL)],
    [P("<font color='#666666'><b>GREY</b></font>", CELL), P(f"Bridges 3-6 and 8-12: {BRIDGES}. No jumpers anywhere.", CELL)],
], colWidths=[34 * mm, 140 * mm])
key.setStyle(grid_style(header=False))
story.append(key)
story.append(P("Left and right channels have their own colours: blue and purple on the WMD side, red and orange on the tile side. "
               "Draw the lines in the gaps beside the holes, not through the pad rings. Ink under a joint still solders; it just looks scruffy. "
               "A WMD-side wire (blue or purple) touching a tile-side one (red or orange) anywhere is a failed board.", SM))

# ===== PAGES 2-3: drawings =====
story.append(NextPageTemplate("land"))
story.append(PageBreak())
story.append(P("Routing, TOP view (component side). Column 0 is the IN end, row 0 is the top edge.", H2))
story.append(Image("outputs/iso-board-routing.png", width=LW - 24 * mm, height=(LW - 24 * mm) * 0.4))
story.append(P("v3 for the measured headers. Bodies on top, every wire underneath. Machine-checked (solver/check_routes.py): no wire crosses another "
               "and no two wires share a hole, except the two shield wires that end on the same GND pin.", SM))
story.append(PageBreak())
story.append(P("Routing, UNDERSIDE view (mirrored). This is what you see with the board flipped, wires facing you.", H2))
story.append(Image("outputs/iso-board-routing-underside.png", width=LW - 24 * mm, height=(LW - 24 * mm) * 0.4))
story.append(P("Use this page at the iron. The IN end is now on the RIGHT. Lay silver wire flat from pad to pad along the drawn path; solder each pad it lands on; do not let bare wire cross another bare wire.", SM))

# ===== PAGE 4: build order =====
story.append(NextPageTemplate("portrait"))
story.append(PageBreak())
story.append(P("4. Build order", H1))
story.append(P("A. Prepare", H2C))
for t in [
    f"Cut the board to {SIZE}. Score both faces along a hole row with a knife against a rule, snap over a table edge, tidy with P120 on the block. Backup: junior hacksaw (32 TPI). Wipe the glass dust off.",
    f"Mark the two transformer footprints on TOP: primary column at col {CFG['t1']} (T1) and col {CFG['t2']} (T2), secondary column 14 holes on, at col {CFG['t1'] + 14} and col {CFG['t2'] + 14}. Pins at rows {', '.join(str(r + TR) for r in PRIM.values())} (primary) and {', '.join(str(r + TR) for r in SEC.values())} (secondary). Check a transformer physically against the marks before drilling.",
    "Drill the 22 footprint holes to 1.5 mm with the HOTO at 600 rpm, light pressure. The existing hole centres the bit. All other holes stay 1.0 mm.",
    "Sharpie the routing on the UNDERSIDE using page 3 and the colour key.",
]: story.append(ck(t))
story.append(P("B. Headers and ribbons", H2C))
for t in [
    f"Fit both 2x3 box headers from the top: IN at cols {CFG['in_col']}-{CFG['in_col'] + 1} rows {HR}-{HR + 2}, OUT at cols {CFG['out_col']}-{CFG['out_col'] + 1} rows {HR}-{HR + 2}, "
    f"oriented as in section 2 ({'OUT header turned 180°, GND pins toward the bottom' if CFG['out_rot'] else 'GND pins toward the top'}). Tack one pin, check it sits flat, solder the rest.",
    "Peel 6 conductors off the 10-way ribbon. Cut square. Crimp a PFL 6 on each end in the vice: stripe over pin 1, cap pressed home parallel with scrap card either side, strain relief folded over. Two short ribbons (different lengths) plus one longer bypass ribbon.",
    "Test each ribbon: all six conductors continuous end to end; no continuity between neighbouring pins.",
    "Orientation check, before any wiring: plug the tile's ribbon into the OUT header. Meter from a tile jack sleeve to the OUT header holes: expect 0 ohm at "
    + " and ".join(xy(c) for c, lab in sorted(RF["OUT_MAP"].items()) if lab.startswith("GND")) + ". If the 0 ohm readings are at "
    + " and ".join(xy(c) for c in sorted((c[0], 2 * HR + 2 - c[1]) for c, lab in RF["OUT_MAP"].items() if lab.startswith("GND")))
    + " instead, the header is the wrong way round: stop and refit it.",
]: story.append(ck(t))
story.append(P("C. Transformers and wiring <font size=8.4 name=Helvetica>(each wire: corner holes (col,row) in order, straight runs between them)</font>", H2C))
def wire_name(r):
    lab = r[0]
    if lab.startswith("shield"): return f"T{1 if r[2][0] == pin('T1', 9) else 2} shield"
    return ("IN " if ": IN" in lab else "OUT ") + lab.split(" :")[0]
mirror_note = " ".join(f"{t} is mirrored: IN {CH[t]}+ goes to pin 4 and IN {CH[t]}- to pin 1; OUT {CH[t]}+ comes from pin 11 and OUT {CH[t]}- from pin 7." for t in MIRRORED)
for t in [
    "Seat T1 and T2 from the top with the primary pins toward the IN end. Every pin drops in without force. Solder all 11 pins on each; short passes.",
    f"Bridges first (grey): {BRIDGES}.",
    *([f"<b>{mirror_note}</b>"] if mirror_note else []),
    *[f"<font color='{PAL.wire_colour(r[0])}'><b>{wire_name(r)}</b></font> "
      + describe(r[2]) + (f" Solder it together with the T1 shield on {xy(GND_USED[0])}." if r is SH_W[-1] and len(GND_USED) == 1 and len(SH_W) == 2 else "")
      for r in IN_W + OUT_W + SH_W],
    f"No wire on: IN GND pins " + " and ".join(xy(c) for c, lab in sorted(RF["IN_MAP"].items()) if lab.startswith("GND"))
    + ("; OUT GND " + " and ".join(xy(c) for c in GND_FREE) if GND_FREE else "") + "; pins 2 and 5 of each transformer.",
]: story.append(ck(t))
story.append(P("D. Bench tests, before it goes anywhere near the case", H2C))
sig_out = ", ".join(xy(c) for c, lab in sorted(RF["OUT_MAP"].items()) if not lab.startswith("GND"))
tests = Table([
    [P("<b>Meter between</b>", CELLC), P("<b>Expect</b>", CELLC), P("<b>Means</b>", CELLC)],
    [P("T pin 1 and pin 4 (each transformer)", CELLC), P("about 18 ohm", CELLC), P("primaries in series, bridge good", CELLC)],
    [P("T pin 7 and pin 11 (each transformer)", CELLC), P("about 19 ohm", CELLC), P("secondaries in series, bridge good", CELLC)],
    [P("T pin 1 and pin 7", CELLC), P("OPEN", CELLC), P("no copper between the sides", CELLC)],
    [P("T pin 9 and pin 1; pin 9 and pin 7", CELLC), P("OPEN", CELLC), P("housing touches no coil", CELLC)],
    [P("IN header GND and OUT header GND", CELLC), P("OPEN", CELLC), P("the isolation itself", CELLC)],
    [P("every IN signal pin and every OUT pin", CELLC), P("OPEN", CELLC), P("no stray bridge across domains", CELLC)],
    [P("IN L+ and IN L-; IN R+ and IN R-", CELLC), P("about 18 ohm", CELLC), P("header to primary correct" + (f" ({', '.join(MIRRORED)} mirrored)" if MIRRORED else ""), CELLC)],
    [P("OUT L+ and OUT L-; OUT R+ and OUT R-", CELLC), P("about 19 ohm", CELLC), P("secondary to header correct", CELLC)],
    [P(f"OUT GND {' / '.join(xy(c) for c in GND_USED)} and T1 pin 9; and T2 pin 9", CELLC), P("0 ohm", CELLC), P("both shields landed", CELLC)],
    [P("OUT GND and each OUT signal pin", CELLC), P("OPEN", CELLC), P("no shield wire touching a signal wire", CELLC)],
], colWidths=[66 * mm, 28 * mm, 82 * mm])
tests.setStyle(grid_style()); tests.setStyle(TableStyle([("TOPPADDING", (0, 0), (-1, -1), 1.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5), ("FONT", (0, 0), (-1, -1), "Helvetica", 8.0)]))
story.append(tests)
story.append(P("E. Sleeve, mount, install", H2C))
for t in [
    "Cut about 150 mm of the 70 mm ISOLATECH tube. Slide on with both ribbons plugged, shrink from the centre out with the gun moving. Ends stay open.",
    "Mark IN and OUT on the sleeve with a paint pen.",
    "Two EPDM runners (about 120 mm, 15 x 3 mm) stuck to the case where the board sits, about 30 mm apart. Two tie bases on isopropyl-wiped aluminium either side, pressed 30 s, left 24 h. Zip tie through each base; ONE-WRAP strap through the zip ties and over the board.",
    "Installed, strap tight, NO FOH cable: tile jack sleeve to any WMD jack sleeve = OPEN, and tile jack sleeve to bare case metal = OPEN. Press and wiggle the board while watching the meter.",
    "Ribbon in, tone playing: turn MSTR, level at the tile follows. Heaviest track, full MSTR, into a desk: bottom end clean, L and R equal and in phase.",
    "Straight bypass ribbon into the flight case. Label the tile ISO OUT L/R, LINE LEVEL.",
]: story.append(ck(t))

doc.build(story)
print("saved", OUT)
