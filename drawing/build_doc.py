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
CK = ParagraphStyle("CK", fontName="Helvetica", fontSize=9.3, leading=11.8, leftIndent=14, firstLineIndent=-14, spaceAfter=1.5)
CELL = ParagraphStyle("CELL", fontName="Helvetica", fontSize=8.6, leading=10.6)
CELLB = ParagraphStyle("CELLB", fontName="Helvetica-Bold", fontSize=8.6, leading=10.6)

IN_C, OUT_C, SH_C, BR_C = colors.HexColor("#1F6FB2"), colors.HexColor("#D9541E"), colors.HexColor("#2E8B57"), colors.HexColor("#7A7A7A")

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

# ===== PAGE 1: reference =====
story.append(P("FOH isolation board: bench sheet, v2 (measured headers)", H1))
story.append(P("Two Lundahl LL1517 transformers on a 48 x 17 hole perfboard (122 x 43 mm), sitting in the ribbon between the "
               "WMD's rear balanced-out header and the Stereo Out Jacks 1U tile. 1:1, passive, galvanically isolated. "
               "Four signals cross through iron; no ground ever crosses.", B))

story.append(P("1. LL1517 pin key", H2))
pin_tbl = Table([
    [P("<b>Pin</b>", CELL), P("<b>What it is</b>", CELL), P("<b>T1 (LEFT)</b>", CELL), P("<b>T2 (RIGHT), mirrored</b>", CELL)],
    [P("1", CELLB), P("primary A start (+)", CELL), P("IN L+ (hot)", CELL), P("IN R- (cold)", CELL)],
    [P("3", CELLB), P("primary A end", CELL), P("bridge to 6", CELL), P("bridge to 6", CELL)],
    [P("6", CELLB), P("primary B start (+)", CELL), P("bridge from 3", CELL), P("bridge from 3", CELL)],
    [P("4", CELLB), P("primary B end", CELL), P("IN L- (cold)", CELL), P("IN R+ (hot)", CELL)],
    [P("2, 5", CELLB), P("centre taps", CELL), P("nothing", CELL), P("nothing", CELL)],
    [P("7", CELLB), P("secondary A start (+)", CELL), P("OUT L+ (tip)", CELL), P("OUT R- (ring)", CELL)],
    [P("8", CELLB), P("secondary A end", CELL), P("bridge to 12", CELL), P("bridge to 12", CELL)],
    [P("12", CELLB), P("secondary B start (+)", CELL), P("bridge from 8", CELL), P("bridge from 8", CELL)],
    [P("11", CELLB), P("secondary B end", CELL), P("OUT L- (ring)", CELL), P("OUT R+ (tip)", CELL)],
    [P("9", CELLB), P("core + housing", CELL), P("OUT GND (45,7)", CELL), P("joins T1's shield wire via the jumper", CELL)],
], colWidths=[11 * mm, 34 * mm, 30 * mm, 38 * mm])
pin_tbl.setStyle(grid_style())
side = Table([[pin_drawing(), pin_tbl]], colWidths=[62 * mm, 116 * mm])
side.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
story.append(side)
story.append(P("<b>T2 is wired mirrored on purpose:</b> both its primary and its secondary are reversed. Reversing one side alone would "
               "flip the right channel; reversing both cancels out, so L and R stay in phase. It is what lets the right-channel wires "
               "reach the header without crossing. Bridges are the same on both: 3-6 and 8-12, never 3-4.", SM))

story.append(P("2. Header pin maps (measured 13 Sept)", H2))
story.append(P("Both headers came out the same, viewed from the component side: top row GND, GND; middle row L+, L-; bottom row R+, R-. "
               "Rows and columns below are perfboard holes: column 0 is the IN end, row 0 the top edge. IN header = columns 1-2, "
               "OUT header = columns 45-46, both in rows 7-9.", B))
hdr = Table([
    [P("<b>IN (WMD)</b>", CELL), P("<b>col 1</b>", CELL), P("<b>col 2</b>", CELL), "", P("<b>OUT (tile)</b>", CELL), P("<b>col 45</b>", CELL), P("<b>col 46</b>", CELL)],
    [P("row 7", CELL), P("GND, no wire", CELL), P("GND, no wire", CELL), "", P("row 7", CELL), P("GND (T1 shield)", CELL), P("GND, no wire", CELL)],
    [P("row 8", CELL), P("L+", CELL), P("L-", CELL), "", P("row 8", CELL), P("L+", CELL), P("L-", CELL)],
    [P("row 9", CELL), P("R+", CELL), P("R-", CELL), "", P("row 9", CELL), P("R+", CELL), P("R-", CELL)],
], colWidths=[22 * mm, 31 * mm, 31 * mm, 6 * mm, 22 * mm, 31 * mm, 31 * mm])
hdr.setStyle(TableStyle([("FONT", (0, 0), (-1, -1), "Helvetica", 8.6), ("GRID", (0, 0), (2, -1), 0.4, colors.HexColor("#999")),
                         ("GRID", (4, 0), (6, -1), 0.4, colors.HexColor("#999")), ("BACKGROUND", (0, 0), (2, 0), colors.HexColor("#DCE7F5")),
                         ("BACKGROUND", (4, 0), (6, 0), colors.HexColor("#F8E3D8")), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                         ("LEFTPADDING", (3, 0), (3, -1), 0), ("RIGHTPADDING", (3, 0), (3, -1), 0)]))
story.append(hdr)
story.append(P("<b>Orientation:</b> fit each header so its two GND pins are toward the top edge of the board (row 7) and its notch faces the same "
               "way as the notch on the WMD or tile does when you hold that device with its GND pins up. Then a straight ribbon lands every "
               "signal where the drawing expects it. Both ribbons pin 1 to pin 1, stripe on the same side at both ends; make them different lengths.", SM))
story.append(P("3. Sharpie key for the underside", H2))
key = Table([
    [P("<font color='#1F6FB2'><b>BLUE</b></font>", CELL), P("WMD side: L+, L-, R+, R-. Bottom lanes: row 15 = R+, row 14 = R-.", CELL)],
    [P("<font color='#D9541E'><b>ORANGE / RED</b></font>", CELL), P("Tile side: L+, L-, R+, R-. Top lanes rows 0 and 2 for the long L runs.", CELL)],
    [P("<font color='#2E8B57'><b>GREEN</b></font>", CELL), P("Shields: pin 9 of each transformer to an OUT-side GND pin. Top lane row 1.", CELL)],
    [P("<font color='#7A7A7A'><b>GREY / BLACK</b></font>", CELL), P("Bridges 3-6 and 8-12, inside each footprint on columns 7, 19, 26, 40. Dashed green = the one insulated jumper.", CELL)],
], colWidths=[34 * mm, 140 * mm])
key.setStyle(grid_style(header=False))
story.append(key)
story.append(P("Draw the lines in the gaps beside the holes, not through the pad rings. Ink under a joint still solders; it just looks scruffy. "
               "A blue wire touching an orange one anywhere is a failed board.", SM))

# ===== PAGES 2-3: drawings =====
story.append(NextPageTemplate("land"))
story.append(PageBreak())
story.append(P("Routing, TOP view (component side). Column 0 is the IN end, row 0 is the top edge.", H2))
story.append(Image("outputs/iso-board-routing.png", width=LW - 24 * mm, height=(LW - 24 * mm) * 0.4))
story.append(P("v2 for the measured headers. Bodies on top, every wire underneath. Machine-checked: no two wires share a hole; the only crossing is the dashed insulated jumper near the OUT header.", SM))
story.append(PageBreak())
story.append(P("Routing, UNDERSIDE view (mirrored). This is what you see with the board flipped, wires facing you.", H2))
story.append(Image("outputs/iso-board-routing-underside.png", width=LW - 24 * mm, height=(LW - 24 * mm) * 0.4))
story.append(P("Use this page at the iron. The IN end is now on the RIGHT. Lay silver wire flat from pad to pad along the drawn path; solder each pad it lands on; do not let bare wire cross another bare wire.", SM))

# ===== PAGE 4: build order =====
story.append(NextPageTemplate("portrait"))
story.append(PageBreak())
story.append(P("4. Build order", H1))
story.append(P("A. Prepare", H2))
for t in [
    "Cut the board to 48 x 17 holes (122 x 43 mm). Score both faces along a hole row with a knife against a rule, snap over a table edge, tidy with P120 on the block. Backup: junior hacksaw (32 TPI). Wipe the glass dust off.",
    "Mark the two transformer footprints on TOP: primary column at col 6 (T1) and col 27 (T2), secondary column 14 holes on, at col 20 and col 41. Pins at rows 3, 5, 7, 9, 11, 13 (primary) and 3, 5, 9, 11, 13 (secondary). Check a transformer physically against the marks before drilling.",
    "Drill the 22 footprint holes to 1.5 mm with the HOTO at 600 rpm, light pressure. The existing hole centres the bit. All other holes stay 1.0 mm.",
    "Sharpie the routing on the UNDERSIDE using page 3 and the colour key.",
]: story.append(ck(t))
story.append(P("B. Headers and ribbons", H2))
for t in [
    "Fit both 2x3 box headers from the top: IN at cols 1-2 rows 7-9, OUT at cols 45-46 rows 7-9, notch orientation matching the WMD's and the tile's own headers. Tack one pin, check it sits flat, solder the rest.",
    "Peel 6 conductors off the 10-way ribbon. Cut square. Crimp a PFL 6 on each end in the vice: stripe over pin 1, cap pressed home parallel with scrap card either side, strain relief folded over. Two short ribbons (different lengths) plus one longer bypass ribbon.",
    "Test each ribbon: all six conductors continuous end to end; no continuity between neighbouring pins.",
]: story.append(ck(t))
story.append(P("C. Transformers and wiring", H2))
for t in [
    "Seat T1 and T2 from the top with the primary pins toward the IN end. Every pin drops in without force. Solder all 11 pins on each; short passes.",
    "Bridges first (grey): T1 3-6 on col 7, T1 8-12 on col 19, T2 3-6 on col 26, T2 8-12 on col 40.",
    "IN wires (blue): L+ (1,8) out to col 0, down to row 14, along to col 5, up into T1 pin 1. L- (2,8) along row 8 to col 4, up to row 7, into T1 pin 4. "
    "R+ (1,9) down col 1 to row 12, along to col 7, down to row 15, along row 15 to col 28, up col 28 to row 7, into T2 pin 4 (mirrored). "
    "R- (2,9) down to row 10, along to col 8, down to row 14, along row 14 to col 27, up into T2 pin 1 (mirrored).",
    "OUT wires (orange): T1 pin 11 (L-) out to col 21, up to row 0, along to col 47, down to row 8, into OUT L- (46,8). "
    "T1 pin 7 (L+) along row 13 to col 23, up to row 2, along to col 44, down to row 8, into OUT L+ (45,8). "
    "T2 pin 11 (R+, mirrored) up to row 4, along to col 43, down to row 9, into OUT R+ (45,9). "
    "T2 pin 7 (R-, mirrored) along row 13 to col 46, up into OUT R- (46,9).",
    "T1 shield (green): pin 9 out to col 22, up to row 1, along to col 45, down to GND (45,7).",
    "T2 shield (green): pin 9 to (41,8), across to (42,8), up to (42,6). Then the ONE insulated jumper: a scrap of insulated hookup wire (or bare wire "
    "with a sleeve of 1 mm heat-shrink) soldered at (42,6) and at (45,6), lying over the bare wires at (43,6) and (44,6) without touching them. "
    "(45,6) already has T1's shield wire on it, so both housings end on the same GND pin.",
    "No wire on: IN GND pins (1,7) and (2,7); OUT GND (46,7); pins 2 and 5 of each transformer.",
]: story.append(ck(t))
story.append(P("D. Bench tests, before it goes anywhere near the case", H2))
tests = Table([
    [P("<b>Meter between</b>", CELL), P("<b>Expect</b>", CELL), P("<b>Means</b>", CELL)],
    [P("T pin 1 and pin 4 (each transformer)", CELL), P("about 18 ohm", CELL), P("primaries in series, bridge good", CELL)],
    [P("T pin 7 and pin 11 (each transformer)", CELL), P("about 19 ohm", CELL), P("secondaries in series, bridge good", CELL)],
    [P("T pin 1 and pin 7", CELL), P("OPEN", CELL), P("no copper between the sides", CELL)],
    [P("T pin 9 and pin 1; pin 9 and pin 7", CELL), P("OPEN", CELL), P("housing touches no coil", CELL)],
    [P("IN header GND and OUT header GND", CELL), P("OPEN", CELL), P("the isolation itself", CELL)],
    [P("every IN signal pin and every OUT pin", CELL), P("OPEN", CELL), P("no stray bridge across domains", CELL)],
    [P("IN L+ and IN L-; IN R+ and IN R-", CELL), P("about 18 ohm", CELL), P("header to primary correct (T2 mirrored)", CELL)],
    [P("OUT L+ and OUT L-; OUT R+ and OUT R-", CELL), P("about 19 ohm", CELL), P("secondary to header correct", CELL)],
    [P("OUT GND (45,7) and T1 pin 9; and T2 pin 9", CELL), P("0 ohm", CELL), P("both shields landed, jumper good", CELL)],
    [P("T2 pin 9 and OUT L+ (45,8); and OUT R+ (45,9)", CELL), P("OPEN", CELL), P("jumper insulation intact over the crossings", CELL)],
], colWidths=[66 * mm, 28 * mm, 82 * mm])
tests.setStyle(grid_style())
story.append(tests)
story.append(P("E. Sleeve, mount, install", H2))
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
