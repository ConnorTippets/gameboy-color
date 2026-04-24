import sys
from pathlib import Path

root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from src import Debugger
from src import Memory

mem = Memory()
mem.load_boot_rom("test/dmg_boot.bin")

debug = Debugger(mem)
debug.run()
