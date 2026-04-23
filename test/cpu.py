from src import CPU
from src import Memory

mem = Memory()
mem.load_boot_rom("test/dmg_boot.bin")

cpu = CPU(mem)
cpu.run()
