import sys
from pathlib import Path

# Los módulos del dashboard se importan planos (import datos), así que dashboard/ va al path.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "dashboard"))
