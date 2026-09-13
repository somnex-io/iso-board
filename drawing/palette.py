"""Wire colours shared by routing.py and build_doc.py.

Steven, 13 Sept: draw left and right channels in different colours. The sheet is printed in colour,
so colour alone carries the channel (no line-style difference):
  IN (WMD side):   left = blue,  right = purple
  OUT (tile side): left = red,   right = orange
  shield = green, bridges = grey (no channel)

Checked with the dataviz palette validator against the board colour #F3EFE4, all pairs: colour-blind
separation >= 7.1 (worst: shield vs OUT right), normal-vision separation >= 15.3, left vs right
>= 18 on each side, every wire colour >= 3:1 contrast. No left/right pair is red/green. Bridges are a
lighter grey (2.3:1) on purpose; they are short stubs beside a pin column and named in the pin key.
"""
IN_L, IN_R = "#10347D", "#7456B8"      # blue, purple
OUT_L, OUT_R = "#A23125", "#B57A09"    # red (brick), orange (amber)
SH_C, BR_C = "#328B5F", "#A0A0A0"      # shield green, bridge grey
IN_C, OUT_C = IN_L, OUT_L              # each side's colour for text and header outlines


def wire_colour(label):
    """Colour for a route label in routes_v*.py format."""
    if label.startswith("shield"): return SH_C
    if "bridge" in label: return BR_C
    right = label[0] == "R"
    if ": IN" in label: return IN_R if right else IN_L
    return OUT_R if right else OUT_L
