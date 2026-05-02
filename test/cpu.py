import sys
from pathlib import Path

root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from src import CPU
from src import Memory
from src import Debugger

mem = Memory()
# mem.load_boot_rom("test/dmg_boot.bin")
mem.load_game_rom("test/8.gb")

cpu = CPU(mem)
cpu.registers["A"] = 0x01
cpu.registers["F"] = 0xB0
cpu.registers["B"] = 0x00
cpu.registers["C"] = 0x13
cpu.registers["D"] = 0x00
cpu.registers["E"] = 0xD8
cpu.registers["H"] = 0x01
cpu.registers["L"] = 0x4D
cpu.sp = 0xFFFE
cpu.pc = 0x0100

try:
    for i in range(200000000):

        a_hex = hex(cpu.registers["A"])[2:].upper()
        f_hex = hex(cpu.registers["F"])[2:].upper()
        b_hex = hex(cpu.registers["B"])[2:].upper()
        c_hex = hex(cpu.registers["C"])[2:].upper()
        d_hex = hex(cpu.registers["D"])[2:].upper()
        e_hex = hex(cpu.registers["E"])[2:].upper()
        h_hex = hex(cpu.registers["H"])[2:].upper()
        l_hex = hex(cpu.registers["L"])[2:].upper()
        sp_hex = hex(cpu.sp)[2:].upper()
        pc_hex = hex(cpu.pc)[2:].upper()

        pcmem_hex = hex(cpu.memory.read_byte(cpu.pc))[2:].upper()
        pcmem1_hex = hex(cpu.memory.read_byte(cpu.pc + 1))[2:].upper()
        pcmem2_hex = hex(cpu.memory.read_byte(cpu.pc + 2))[2:].upper()
        pcmem3_hex = hex(cpu.memory.read_byte(cpu.pc + 3))[2:].upper()

        print(
            f"A:{a_hex:0>2} F:{f_hex:0>2} B:{b_hex:0>2} C:{c_hex:0>2} D:{d_hex:0>2} E:{e_hex:0>2} H:{h_hex:0>2} L:{l_hex:0>2} SP:{sp_hex:0>4} PC:{pc_hex:0>4} PCMEM:{pcmem_hex:0>2},{pcmem1_hex:0>2},{pcmem2_hex:0>2},{pcmem3_hex:0>2}"
        )
        cpu.step()
        sys.stdout.flush()
except BrokenPipeError:
    sys.exit(0)
except KeyboardInterrupt:
    sys.exit(0)

    # instr = Debugger.disasm(cpu)
    # try:
    #     cpu.step()
    # except Exception as e:
    #     print(instr)
    #     raise e
