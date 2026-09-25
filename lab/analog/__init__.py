"""Public analog-model API. These models do not establish hardware safety.

Consumers import from lab.analog; implementation modules import each other
without looping back through this facade. Importing performs no simulation.
"""

from ._model import Drive, InputNetwork
from ._report import CircuitReport, circuit_report
from ._solver import transfer
from ._spice import export_spice, run_ngspice, run_ngspice_transient

__all__ = [
    "CircuitReport",
    "Drive",
    "InputNetwork",
    "circuit_report",
    "export_spice",
    "run_ngspice",
    "run_ngspice_transient",
    "transfer",
]
