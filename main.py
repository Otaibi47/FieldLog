"""Root-level launcher — delegates to desktop/main.py."""
import runpy, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).parent / "desktop"))
runpy.run_path(str(pathlib.Path(__file__).parent / "desktop" / "main.py"), run_name="__main__")
