"""starlab: the code library behind *STAR on Atoms*.

Small on purpose. Each module is the instrument one chapter builds and
explains:

    circuits   QuEra's STAR injection circuits, at any angle   (Chapter 6)
    stats      Wilson intervals for rare events                (Chapter 7)
    sampling   sample, post-select, decode, count              (Chapter 7)
    renoise    Table II channels on the native gate set        (Chapter 11)
"""

from .circuits import (DISTANCES, branch_flip_shape, ideal_acceptance,
                       logical_angle, n_postselected, physical_angle,
                       star_circuit, star_text, with_angle)
from .stats import rate_record, wilson

__version__ = "0.1.0"

__all__ = ["DISTANCES", "branch_flip_shape", "ideal_acceptance",
           "logical_angle", "n_postselected", "physical_angle", "star_circuit", "star_text", "with_angle",
           "rate_record", "wilson", "__version__"]
