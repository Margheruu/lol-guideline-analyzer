"""Rule package. Importing it registers all bundled rule modules."""
from . import (  # noqa: F401  (register on import)
    death,
    examples,
    itemization,
    laning,
    participation,
    vision,
)
