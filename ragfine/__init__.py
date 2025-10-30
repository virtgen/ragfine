from .core import *
import ragfine.steps
from ragfine.steps import *

# Auto-load domain steps if requested
#if os.getenv("RAGFINE_AUTOLOAD_INSIGHTGEN") == "1":
ragfine.steps.load_insightgen()

# --- Compose __all__ from both core and steps ------------------------------
__all__ = []
__all__ += list(globals().keys())  # crude merge, but ok for top-level import * semantics
# Optional: filter or override with an explicit list if you want finer control

# --- Optional: short version info ------------------------------------------
__version__ = "1.0.0"