#!/usr/bin/env python3
"""Inventaire vidéo partagé avec le pilote ; bibliothèque standard uniquement."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pilot.video_inventory import *

if __name__=='__main__':
    raise SystemExit(main())
