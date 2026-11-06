#!/usr/bin/env python3
"""Delegates to build_site.py so the documented entry point keeps working."""
import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).with_name('build_site.py')), run_name='__main__')
