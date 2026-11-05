#!/usr/bin/env python3
"""Apply the current smart-home dashboard refinement."""
from pathlib import Path
import subprocess
import sys

source = Path(sys.argv[1])
refiner = Path(__file__).with_name("refine_dashboard.py")
subprocess.run([sys.executable, str(refiner), str(source)], check=True)
