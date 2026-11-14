"""
ESF-DT :: Electric Smelting Furnace Digital Twin
================================================
First-principles process model, digital twin and operator workbench for the
Electric Smelting Furnace (open slag bath furnace) used to melt and reduce
direct-reduced iron from low-grade ores into blast-furnace-grade hot metal.

Version 1.1 adds industrial and experimental reference data published in
2025-2026: the blast-furnace / open-bath-furnace composition comparison and
the Tenova iBlue design envelope (Sabah et al., J. Sustain. Metall. 2026),
the stream-by-stream mass and energy balance of Shahabuddin et al., and the
FeO-reduction kinetics measured under ESF conditions by Bae and Park
(J. Cleaner Prod. 2025).  It also models the hot heel explicitly and scores
the tapped slag for cement reuse.

(c) Extractmet Private Limited, IIT Madras Research Park.
All plant references in this package are anonymised as "Industry-X".
"""

__version__ = "1.1.0"
__product__ = "ESF-DT"
__vendor__ = "Extractmet Private Limited"

PRODUCT = __product__
VENDOR = __vendor__
TAGLINE = ("First-principles digital twin for DRI smelting in the "
           "Electric Smelting Furnace")

__all__ = ["__version__", "__product__", "__vendor__",
           "PRODUCT", "VENDOR", "TAGLINE"]
