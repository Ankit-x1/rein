"""Allow `python -m stars_forecast`."""
from .cli import main
import sys

sys.exit(main())
