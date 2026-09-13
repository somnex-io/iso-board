#!/usr/bin/env python3
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

AR = "Arial"
HDR_FILL = PatternFill("solid", fgColor="1F2A44")
SEC_FILL = PatternFill("solid", fgColor="E8ECF5")
YEL = PatternFill("solid", fgColor="FFFF00")
HDR_FONT = Font(name=AR, bold=True, color="FFFFFF", size=11)
SEC_FONT = Font(name=AR, bold=True, size=11)
BASE = Font(name=AR, size=11)
LINK = Font(name=AR, size=11, color="0000FF", underline="single")
NOTE_FONT = Font(name=AR, size=10, italic=True, color="555555")
WRAP = Alignment(wrap_text=True, vertical="top")
TOP = Alignment(vertical="top")
thin = Side(style="thin", color="C0C0C0")
BORD = Border(left=thin, right=thin, top=thin, bottom=thin)

wb = Workbook()
ws = wb.active
ws.title = "Buy list"

ws["A1"] = "Somnex FOH isolation build — buy list"
ws["A1"].font = Font(name=AR, bold=True, size=14)
ws["A2"] = ("Legend: item names are clickable product links. Prices marked INVOICED come from the actual order emails "
            "of 31 Aug 2026; Reichelt lines are ex-BTW business pricing, all others incl. BTW. Yellow = still to confirm. "
            "Status: To order / Ordered / Have.")
ws["A2"].font = NOTE_FONT
ws["A2"].alignment = WRAP
ws.merge_cells("A2:H2")
ws.row_dimensions[2].height = 30

headers = ["#", "Item (click = product page)", "Qty", "Vendor", "Unit EUR", "Line EUR", "Status", "Notes"]
HR = 4
for i, h in enumerate(headers, 1):
    c = ws.cell(row=HR, column=i, value=h)
    c.font = HDR_FONT
    c.fill = HDR_FILL
    c.border = BORD

# (item, url, qty, vendor, unit, status, notes, yellow_cols)
rows = [('Intellijel Stereo Out Jacks 1U (art. 469647)', 'https://www.thomannmusic.com/en-nl/intellijel_designs_stereo_out_jacks_1u.htm', 1, 'Thomann', 23.9, 'Ordered', 'Order ***, 31 Aug. Thomann had only acknowledged receipt when I checked - the itemised confirmation was still pending, so this price is your cart figure, not an invoice. Passive jacks tile (8 HP 1U, 39 mm). NOT art. 469646.', ['E']), ('Floatingpoint Instruments multiclock', 'https://www.thomannmusic.com/floatingpoint_instruments_multiclock.htm', 1, 'Thomann', 568.0, 'Ordered', "Same order ***. Cart price, confirm against Thomann's itemised confirmation when it arrives. 9 V PSU included. Count MIDI DIN cables against its 4 outputs.", ['E']), ('Intellijel Audio I/O (2023)', 'https://www.voltmusicstore.com/products/intellijel-audio-i-o', 1, 'Volt Music Store, Rotterdam', 289.0, 'To order', 'NOT ORDERED - no Volt order in the mailbox (latest is ***, Sept 2025). For the WMD master insert loop to the IMC. In stock; same-day dispatch before 15:00; free NL shipping over EUR 150.', ['G']), ('Lundahl LL1517 output transformer', 'https://www.soundimports.eu/nl/lundahl-ll1517.html', 2, 'SoundImports', 82.95, 'Ordered', 'INVOICED. Order ***, invoice ***, 31 Aug. EUR 165.90 incl 21% BTW, shipping and payment costs EUR 0.00, PostNL 1 day. Datasheet: lundahltransformers.com/wp-content/uploads/datasheets/1517.pdf', []), ('WSL 6G box header, 2x3, 2.54 mm, straight', 'https://www.reichelt.com/de/en/box-connector-6-pin-straight-wsl-6g-p85732.html', 4, 'Reichelt', 0.15, 'Ordered', 'INVOICED ex-BTW. Order ***, 31 Aug. Four ordered rather than two - two spares.', []), ('PFL 6 IDC socket with strain relief', 'https://www.reichelt.de/de/de/pfostenbuchse-6-polig-mit-zugentlastung-pfl-6-p53153.html', 8, 'Reichelt', 0.11, 'Ordered', 'INVOICED ex-BTW. Eight: 4 for the two short ribbons, 2 for the bypass, 2 spare. A botched crimp is the likeliest build error, so spares are the right call.', []), ('Rademacher UP 832EP matrix board, epoxy, 160 x 100 mm', 'https://www.reichelt.com/nl/en/shop/product/matrix_board_epoxy_160x100_mm-23950', 2, 'Reichelt', 6.18, 'Ordered', 'INVOICED ex-BTW (EUR 7.48 incl, matching the 7.47 shelf price). Two boards = a spare if a score-and-snap wanders. Epoxy 1.5 mm, 35 um Cu, pads both faces, 1.0 mm holes, 2.54 mm pitch. Cut to ~123 x 45 mm; open the ~25 LL1517 holes to 1.5 mm.', []), ('Flat ribbon AWG 28-10G, 10-way, grey, 3 m ring', 'https://www.reichelt.com/de/en/shop/product/flat_ribbon_cable_awg_28_10-pin_grey_3-m_ring-47637', 1, 'Reichelt', 3.02, 'Ordered', 'INVOICED ex-BTW. 10-way: peel 6 conductors off for each ribbon, which is what flat cable is designed for.', []), ('BKL silver wire (silver-plated copper), 0.6 mm, 10 m', 'https://www.reichelt.com/de/en/shop/product/silver_wire_diameter_0_6_mm_length_10_m-18069', 1, 'Reichelt', 4.54, 'Ordered', 'INVOICED ex-BTW. Underside pad-to-pad links.', []), ('HSS twist drill DIN 338RN, 1.5 mm, 3-piece set', 'https://www.reichelt.com/de/en/hss-steel-drill-bit-din-338rn-1-5-mm-three-piece-set-bohrer-s1-5mm-p44062.html', 1, 'Reichelt', 1.67, 'Ordered', "INVOICED ex-BTW. Three bits per pouch. Insurance in case the HOTO's 20 bits lack a 1.5.", []), ('Reichelt shipping', None, 1, 'Reichelt', 8.22, 'Ordered', 'INVOICED. Order *** total EUR 31.28.', []), ('HOTO SNAPBLOQ D-A03 Electric Mini Drill Set', 'https://www.amazon.nl/-/en/gp/product/B0DK53D6JF', 1, 'Amazon.nl', 111.65, 'Ordered', 'INVOICED. Amazon order ***, 31 Aug, sold by HOTO Tools, arriving Wednesday. EUR 16.65 over my estimate. Confirm a 1.5 mm bit is among the 20 on arrival; the Reichelt bit covers it either way.', []), ('KATSU SP10008008 mini drill-press vice', 'https://www.amazon.nl/-/en/gp/product/B01NCSSQQQ', 1, 'Amazon.nl', 16.06, 'Ordered', 'INVOICED. Same Amazon order, sold by AIM Tools. Presses the IDC caps and holds the board for drilling. Scrap card either side of the connector; wind down slowly.', []), ('ISOLATECH heat-shrink 2:1 black, O 70 mm (in-line board)', 'https://www.amazon.nl/ISOLATECH-Krimpkous-diverse-diameters-zonder/dp/B07W4PCZRZ', 1, 'Amazon.nl', 11.59, 'Ordered', 'INVOICED. Separate Amazon order ***, arriving tomorrow. Correct size for the IN-LINE board (45 x 22 mm section, 132 mm perimeter, snug at 80% of range). Cut ~150 mm.', []), ('ISOLATECH heat-shrink 2:1 black, O 100 mm (side-by-side fallback)', 'https://www.amazon.nl/ISOLATECH-Krimpkous-diverse-diameters-zonder/dp/B07W4PCZRZ', 1, 'Amazon.nl', 15.09, 'Ordered', 'INVOICED. In the main Amazon order. Covers the SIDE-BY-SIDE layout (80 mm wide, 203 mm perimeter, 71% of range) if in-line does not work out. Buying both sizes takes the layout decision off the critical path.', []), ('S&R sandpaper set + hand sanding block', 'https://www.amazon.nl/b?ie=UTF8&node=16419668031', 1, 'Amazon.nl', 17.49, 'Ordered', 'INVOICED. Sold by Werkzeugbar, arriving tomorrow. Only P120-P180 gets used on the board edge; the block keeps it square. Sand FR4 dry, wipe down after.', []), ('EPDM cell-rubber tape, self-adhesive, 15 x 3 mm, 10 m', 'https://www.amazon.nl/Celrubber-afdichtingsband-enkelzijdig-zelfklevend-schuimrubber/dp/B07YQVZFCN', 1, 'Amazon.nl', 15.0, 'Ordered', "INVOICED. Sold by kaman-equipments. Two runners of ~120 mm under the board's long edges, ~30 mm apart. Sticks to the CASE; nothing sticks to it.", []), ('Self-adhesive cable-tie mounting bases, 20 x 20 mm', 'https://www.amazon.nl/InLine-59965G-bevestigingssokkels-kabelbinders-zelfklevend/dp/B004OXV6WK', 1, 'Amazon.nl', 6.95, 'Ordered', 'INVOICED. Marketplace seller, not the InLine pack I linked - check the slot width on arrival. Slot is usually 4.5 mm and ONE-WRAP is 20 mm, so thread a zip tie through each base and run the strap through that. FITTING: isopropyl, press 30 s, leave 24 h before loading.', []), ('Junior hacksaw 150 mm (Wisent)', None, None, 'owned', None, 'Have', 'Owned. Verify the fitted blade: count tooth tips over 10 mm. 12-13 = 32 TPI (correct), 9-10 = 24 TPI. Photo estimate says 32. If 24: Bahco 228-32-10P or Rotec HSS 150 mm 32 TPI, ~EUR 8-10.', []), ('VELCRO ONE-WRAP strap', None, None, 'owned', None, 'Have', 'Owned - confirmed, so the EUR 20 line is gone. ~200 mm per strap.', []), ('FOH cables: 2x TRS-XLRm self-built + pro snake spare pair', None, None, 'owned', None, 'Have', 'Confirmed owned earlier.', []), ('Insert loop cables (Audio I/O to IMC) + 4x 3.5 mm patch', None, None, 'owned', None, 'Have', 'Confirmed owned earlier.', []), ('Solder: Kester 63/37 0.025 in (Mouser order ***, May 2025)', None, None, 'owned', None, 'Have', '1 lb spool on hand.', [])]

r = HR
for item, url, qty, vendor, unit, status, notes, yellow in rows:
    r += 1
    ws.cell(row=r, column=1, value=r - HR)
    ic = ws.cell(row=r, column=2, value=item)
    if url:
        ic.hyperlink = url
        ic.font = LINK
    ws.cell(row=r, column=3, value=qty)
    ws.cell(row=r, column=4, value=vendor)
    ws.cell(row=r, column=5, value=unit)
    ws.cell(row=r, column=6, value=f"=IF(OR(C{r}=\"\",E{r}=\"\"),\"\",C{r}*E{r})")
    ws.cell(row=r, column=7, value=status)
    ws.cell(row=r, column=8, value=notes)
    for col in range(1, 9):
        c = ws.cell(row=r, column=col)
        c.border = BORD
        if col == 2 and url:
            c.font = LINK
        else:
            c.font = BASE
        c.alignment = WRAP if col in (2, 4, 8) else TOP
    for ycol in yellow:
        ws[f"{ycol}{r}"].fill = YEL

last = r
r += 1
tc = ws.cell(row=r, column=5, value="Total (known)")
tc.font = Font(name=AR, bold=True)
f = ws.cell(row=r, column=6, value=f"=SUM(F{HR+1}:F{last})")
f.font = Font(name=AR, bold=True)
f.border = BORD

for row in range(HR + 1, last + 2):
    ws.cell(row=row, column=5).number_format = '"€"#,##0.00'
    ws.cell(row=row, column=6).number_format = '"€"#,##0.00'

widths = {"A": 4, "B": 48, "C": 5, "D": 26, "E": 10, "F": 10, "G": 11, "H": 62}
for col, w in widths.items():
    ws.column_dimensions[col].width = w
ws.freeze_panes = f"A{HR+1}"

# ---------------- Sheet 2: Build + tests ----------------
ws2 = wb.create_sheet("Build + tests")
ws2["A1"] = "Board: WMD 6-pin header  ->  2x LL1517 (series-series 1:1)  ->  Stereo Out Jacks 1U"
ws2["A1"].font = Font(name=AR, bold=True, size=13)
ws2["A2"] = ("Mark Done column as you go. LL1517 datasheet drawing is the wiring authority: "
             "lundahltransformers.com/wp-content/uploads/datasheets/1517.pdf")
ws2["A2"].font = NOTE_FONT
ws2["A2"].alignment = WRAP
ws2.merge_cells("A2:D2")

h2 = ["Phase", "Step", "Detail", "Done"]
HR2 = 4
for i, h in enumerate(h2, 1):
    c = ws2.cell(row=HR2, column=i, value=h)
    c.font = HDR_FONT
    c.fill = HDR_FILL
    c.border = BORD

steps = [
    ("A. Pre-build checks", [
        ("Tile isolation", "Tile out of case: meter jack sleeve to bare panel = OPEN. Photo shows plastic-bushing jacks; verify anyway."),
        ("WMD header map", "Manual: BALANCED OUT is a 6-pin header for Intellijel case outputs, described as part of MSTR OUT, and 'the MASTER pot will reduce the level here' - so the header is POST-MSTR. Confirm functionally: ribbon in, tone playing, turn MSTR and watch the level change. Manual also states all panel points AND rear headers are IN PHASE on the MKII, so the header polarity matches the front jacks. Still meter jack-to-pin (tip = +, ring = -, sleeve = gnd) and write the map down. NOTE: the VU meter reads the mixing bus BEFORE the MASTER pot, so it does not show what FOH receives - and gain reduction in the MASTER INSERT (the IMC) is not shown either."),
        ("DC offset check", "Eurorack is often DC-coupled, and DC through a transformer primary biases the core and eats headroom. With the rig running and MSTR up, meter DC VOLTS across the header's L+/L- and R+/R- pairs. A few mV is nothing; tens of mV or more, ask WMD before relying on it. The transformer will block DC from reaching FOH either way - the concern is headroom on our side."),
        ("Signal order (CONFIRMED)", "Mix bus -> MASTER INSERT (IMC) -> MSTR pot -> DRV135 balanced driver -> rear header -> transformer board -> tile -> FOH. Steven confirmed the insert is PRE-MSTR. Consequences: (1) MSTR is genuinely the FOH gain and it attenuates AHEAD of the transformer, so the board can never see more than the WMD can pass; (2) MSTR is a post-compression trim, so changing FOH level does not disturb IMC gain staging; (3) ceiling at the transformer is the WMD insert return clipping, roughly +19 dBu worst case, still ~5 dB under the LL1517's +24 dBu at 30 Hz. Line-check order: set IMC drive and compression first, then use MSTR for level only. The VU helps with none of this - it reads the mix bus before both the insert and the pot."),
        ("Connector check", "Confirm WMD header and tile connector are both 2.54 mm 2x3 shrouded. If one differs, only that header on the board changes."),
        ("Grid fit", "LL1517: pin pitch 5.08 mm, row spacing 35.56 mm = exactly 2 and 14 holes on a 2.54 mm grid. Every pin lands in a hole."),
        ("Cut board to size", "Two straight cuts, 160x100 down to ~123x45. Best method, no new tools: score-and-snap along a ROW OF HOLES. Mark the line, run a sharp utility knife along a steel rule 5-6 firm passes on the top face, repeat on the underside, then snap over a table edge with the board supported close to the line. The hole row acts as a perforation so FR4 breaks cleanly along it. Tidy the edge with a flat file or 120-grit on a block. Backup: 150 mm junior hacksaw, 24-32 TPI, board clamped in the vice or between two bits of ply; finish with P120-P180 on a block. Do NOT cut with the HOTO D-A03 (drill only, 1200 rpm max). A rotary tool with a cut-off disc works but throws fine GLASS DUST everywhere - mask, goggles, outdoors, wipe down after."),
        ("Drill pin holes", "Perfboard holes are 1.0 mm; LL1517 wants 1.5 mm. Open the ~25 footprint holes with the 1.5 mm bit in the HOTO at 600 rpm: the existing hole self-centres the bit, so light pressure and let it cut; pad rings survive. No-drill alternative: only headers through the board; cans on their sides on VHB, insulated solid-core wire soldered to each pin, adhesive-lined heat-shrink on every joint, wire ends into pads; outer sleeve locks it."),
    ]),
    ("B. Board build", [
        ("Ribbons", "IDC, no stripping or soldering. Cut the ribbon SQUARE. Lay it in the socket body with the marked stripe on conductor 1 over the pin-1 triangle, ribbon fully against the stop. Press the cap home in the KATSU vice with scrap card either side of the connector, winding down slowly so it seats parallel and even - never a hammer or single-sided pliers, or some blades cut and others miss. Fold the strain relief clip over the jacket and press home. Straight-through: pin 1 to pin 1, stripe on the same side at both ends. Make 2 short + 1 longer bypass, and make the IN and OUT ribbons DIFFERENT LENGTHS so the board can only be fitted one way round. Test each finished ribbon: continuity end to end on all 6, and no shorts between adjacent pins (a skewed press bridges them)."),
        ("Layout", "IN-LINE, not side by side: the two cans end to end along the board, IN header at one short end, OUT header at the other. Board ~123 x 45 mm, 22 mm tall (LL1517 is 47 x 34 x 18 above PCB; pin rows 35.56 mm apart). Wrap cross-section 45 x 22 = 132 mm perimeter, which is what the 110 mm flat-width sleeve is sized for. Side by side would be 71 x 80 mm and needs 130-140 mm flat sleeve instead. Leave one empty hole-row as a guard between IN-side and OUT-side wiring."),
        ("Routing v2 (see iso-board-routing.png)", "Both headers measured 13 Sept: top row GND GND, middle L+ L-, bottom R+ R-. Same 48 x 17 board, same transformer positions. Three changes from v1: (1) the header ends re-routed, with bottom lanes now row 15 = R+ and row 14 = R-, T2 primary bridge moved to col 26; (2) T2 is wired MIRRORED (IN hot to pin 4, cold to pin 1; OUT hot from pin 11, cold from pin 7), both sides reversed so phase is unchanged, which is what lets R+ and R- reach the header without crossing; (3) ONE insulated jumper, T2 shield from (42,6) to (45,6) over two bare wires, joining T1's shield on the same GND pin. Fit each header with its GND pins toward the top edge and the notch facing the same way as on the WMD/tile held GND-up."),
        ("Wiring", "T1 (left): IN hot -> pin 1, cold -> pin 4; OUT hot <- pin 7, cold <- pin 11. T2 (right), MIRRORED: IN hot -> pin 4, cold -> pin 1; OUT hot <- pin 11, cold <- pin 7. Bridges 3-6 and 8-12 on both. Pin 9 of both to OUT GND (45,7). Pins 2 and 5 unused. Reversing both windings of T2 cancels out, so L and R stay in phase; the bench tone test confirms it."),
        ("Grounds", "Transformer E pins + cans tie to OUT-side ground pins ONLY. WMD ground pins: not connected on the board. No 22k/1nF network (that was the LL1540 recipe)."),
        ("Connections", "Underside pad-to-pad runs in 0.5-0.6 mm tinned solid wire, soldered flat along the pads. Pad-per-hole board = every joint isolated unless you bridge it."),
        ("Sleeve", "Cut ~150 mm (board length + 30). Slide the sleeve on with both ribbons plugged, shrink from centre out, heat gun moving. Ends stay open; only plastic shrouds and ribbons show."),
        ("Insulating bed", "ALUMINIUM CASE: every interior surface is rig ground. Stick the EPDM foam tape to the case floor/wall where the board will sit (adhesive on aluminium is fine) so the board never rests metal-on-metal. Foam wider and longer than the board; it also stops the sleeve abrading through under vibration."),
        ("Mount", "No tie-down points exist in a Eurorack case, so make two: stick a cable-tie base either side of the board footprint, ~65-70 mm apart, on IPA-degreased aluminium. Press 30 s, leave 24 h BEFORE loading. Thread a zip tie through each base and pass the ONE-WRAP strap through those (base slot is 4.5 mm, the strap is 20 mm). Strap arches over the sleeved board and grips itself - nothing adheres to the board. Never adhesive onto the sleeve. Keep the cans clear of rails, neighbouring PCBs and bare case metal."),
    ]),
    ("C. Bench tests", [
        ("Isolation 1", "IN ground pin to OUT ground pin: OPEN."),
        ("Isolation 2", "Every IN signal pin to every OUT pin: OPEN (no copper path exists through a transformer)."),
        ("Windings", "Primary L+ to L-: approx 18 ohm (2 x 9.2). Secondary +: approx 19 ohm (2 x 9.5). Same both channels."),
        ("Installed", "RUN THIS AFTER THE STRAP IS TIGHT, not before - clamping is what pushes a can into the aluminium. Board wired, NO FOH cable: tile jack sleeve to any WMD jack sleeve: OPEN. Also meter tile jack sleeve to bare case metal: OPEN. Press and wiggle the board while watching the meter; any flicker means the sleeve is pinched through."),
        ("Listen", "Heaviest track in the set, full MSTR, into a desk: check bottom end, polarity L vs R, both channels equal."),
    ]),
    ("D. Gig prep", [
        ("Bypass", "Straight 6-pin ribbon (WMD direct to tile) lives in the flight case. 30-second field fix; loses isolation only."),
        ("Label", "Label the tile ISO OUT L/R **LINE LEVEL** so FOH patches the right jacks and knows this is not a DI. The board is 1:1, so it delivers line level on an XLR-terminated cable; if the Radials being replaced were step-down DIs rather than 1:1 isolators, FOH now needs a line input or a pad where they used to take mic level. Say it at line check. Also mark IN and OUT on the board sleeve with a paint pen: both headers are identical 2x3 shrouded parts with the same keying, so nothing mechanical stops the board going in backwards. Reversed it still passes audio and stays isolated, but the shield/cans end up on rig ground and the tile sleeves lose their board reference - not the configuration that was bench-tested."),
    ]),
]

r = HR2
for phase, items in steps:
    r += 1
    pc = ws2.cell(row=r, column=1, value=phase)
    pc.font = SEC_FONT
    pc.fill = SEC_FILL
    for col in range(1, 5):
        ws2.cell(row=r, column=col).fill = SEC_FILL
        ws2.cell(row=r, column=col).border = BORD
    for step, detail in items:
        r += 1
        ws2.cell(row=r, column=2, value=step).font = Font(name=AR, bold=True, size=11)
        d = ws2.cell(row=r, column=3, value=detail)
        d.font = BASE
        d.alignment = WRAP
        dn = ws2.cell(row=r, column=4, value="")
        dn.fill = YEL
        for col in range(1, 5):
            ws2.cell(row=r, column=col).border = BORD
        ws2.cell(row=r, column=2).alignment = TOP
        ws2.cell(row=r, column=3).alignment = WRAP

w2 = {"A": 18, "B": 16, "C": 88, "D": 7}
for col, w in w2.items():
    ws2.column_dimensions[col].width = w
ws2.freeze_panes = f"A{HR2+1}"

out = "/mnt/user-data/outputs/somnex-foh-iso-build-tracker.xlsx"
wb.save(out)
print("saved", out)
