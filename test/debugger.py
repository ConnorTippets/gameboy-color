import sys
from pathlib import Path

root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from src import Debugger
from src import Memory

mem = Memory()
mem.load_game_rom("test/8.gb")
# mem.load_boot_rom("test/dmg_boot.bin")

debug = Debugger(mem)
debug.registers["A"] = 0x01
debug.registers["F"] = 0xB0
debug.registers["B"] = 0x00
debug.registers["C"] = 0x13
debug.registers["D"] = 0x00
debug.registers["E"] = 0xD8
debug.registers["H"] = 0x01
debug.registers["L"] = 0x4D
debug.sp = 0xFFFE
debug.pc = 0x0100

try:
    debug.run()
except Exception as e:
    raise Exception(str(e) + " | " + "0x" + hex(debug.pc).upper()[2:].rjust(4, "0"))
