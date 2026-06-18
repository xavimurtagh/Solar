"""solarlab — a first-principles toolkit for understanding solar cell efficiency.

The package answers three questions, each with computed numbers rather than
assertions:

1. *Why are panels only ~20% efficient?*  ``solarlab.sq`` implements the
   Shockley-Queisser detailed-balance limit from the standard solar spectrum.
2. *What has been done about it?*  ``solarlab.history`` analyses seven decades
   of certified efficiency records.
3. *How do we actually improve it?*  ``solarlab.system`` simulates a real
   rooftop with pvlib and ``solarlab.levers`` ranks concrete improvements.

Run ``python -m solarlab report`` to regenerate every figure and the report.
"""

__version__ = "0.1.0"
