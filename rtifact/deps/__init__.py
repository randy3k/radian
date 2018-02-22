import os
import sys

# this directory would not be needed after prompt_toolkit 2.0 is released.


deps_path = os.path.join(os.path.dirname(__file__))
sys.path.insert(1, deps_path)

dependencies_loaded = True
