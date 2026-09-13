"""Wire colours shared by routing.py and build_doc.py.

Two things are encoded on every signal wire (Steven, 13 Sept: left and right in different colours):
- side of the isolation: IN (WMD side) = blues, OUT (tile side) = brick / amber;
- channel: LEFT = darker and solid, RIGHT = lighter and dashed. The dash is the backstop when the
  sheet is printed in greyscale; colour alone never carries the channel.
Shield green and bridge grey carry no channel.

Checked with the dataviz palette validator against the board colour #F3EFE4, all pairs:
colour-blind separation >= 7.1 (worst: shield vs OUT right, which also differs by the dash),
normal-vision separation >= 15.3, every wire colour >= 3:1 contrast. Greyscale lightness (L*):
IN left 22, OUT left 38, IN right 40, shield 52, OUT right 56, bridges 66. The bridges are lighter
(2.3:1) on purpose, to stay apart from the teal/amber pairs; they are short stubs beside a pin
column and are named in the pin key.
"""
IN_L, IN_R = "#0F3172", "#046491"      # navy, steel blue
OUT_L, OUT_R = "#A23125", "#B57A09"    # brick, amber
SH_C, BR_C = "#328B5F", "#A0A0A0"      # shield green, bridge grey
IN_C, OUT_C = IN_L, OUT_L              # each side's colour for text and header outlines
RIGHT_DASH = (0, (4.5, 2.0))           # matplotlib dash, in line widths
RIGHT_DASH_PDF = (4.5, 2.0)            # reportlab dash, in points


def wire_style(label):
    """(colour, is_right_channel) for a route label in routes_v*.py format."""
    if label.startswith("shield"): return SH_C, False
    if "bridge" in label: return BR_C, False
    right = label[0] == "R"
    if ": IN" in label: return (IN_R if right else IN_L), right
    return (OUT_R if right else OUT_L), right
