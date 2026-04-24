from .memory import Memory
from .util import sign_convert

ZERO_FLAG = 0b10000000


class CPU:
    def __init__(self, memory: Memory):
        self.memory = memory
        self.pc = 0x0000
        self.sp = 0x0000
        self.registers = {
            "A": 0x00,
            "F": 0x00,
            "B": 0x00,
            "C": 0x00,
            "D": 0x00,
            "E": 0x00,
            "H": 0x00,
            "L": 0x00,
        }

        self.word_regs = ["AF", "BC", "DE", "HL", "SP", "PC"]

    def cb_step(self):
        opcode = self.memory.read_byte(self.pc)
        self.pc += 1

        match opcode:
            case 0b01111100:  # BIT 7, H
                # print(
                #     "hi",
                #     self.registers["H"],
                #     "0" * (8 - len(bin(self.registers["H"])[2:]))
                #     + bin(self.registers["H"])[2:],
                #     "0" * (8 - len(bin(1 << 7)[2:])) + bin(1 << 7)[2:],
                # )
                if not ((1 << 7) & self.registers["H"]):
                    self.registers["F"] |= ZERO_FLAG
            case _:
                raise Exception(
                    f"Unknown 0xCB instruction opcode: {"0"*(8-len(bin(opcode)[2:]))+bin(opcode)[2:]}"
                )

    def step(self):
        opcode = self.memory.read_byte(self.pc)
        self.pc += 1

        match opcode:
            case 0b00000000:  # NOP
                return
            case 0b00110001:  # LD SP, IMM16
                imm = self.memory.read_word(self.pc)
                self.pc += 2
                self.sp = imm
            case 0b10101111:  # XOR A
                self.registers["A"] = 0x00
            case 0b00100001:  # LD HL, IMM16
                imm = self.memory.read_word(self.pc)
                self.pc += 2
                self.registers["L"] = imm & 0xFF
                self.registers["H"] = (imm & 0xFF00) >> 8
            case 0b00110010:  # LD HL-, A
                hl = (self.registers["H"] << 8) | self.registers["L"]
                self.memory.write_byte(hl, self.registers["A"])
                hl -= 1
                self.registers["L"] = hl & 0xFF
                self.registers["H"] = (hl & 0xFF00) >> 8
            case 0b11001011:  # 0xCB: Read next byte for opcode
                self.cb_step()
            case 0b00100000:  # JR NZ, IMM8
                jmp = self.memory.read_byte(self.pc)
                self.pc += 1
                if not (ZERO_FLAG & self.registers["F"]):
                    self.pc += sign_convert(jmp)
            case _:
                raise Exception(
                    f"Unknown instruction opcode: {"0"*(8-len(bin(opcode)[2:]))+bin(opcode)[2:]}"
                )

    def run(self):
        # placeholder, accurate timing will be stubbed in later
        while True:
            instr = self.memory.read_byte(self.pc)
            print(
                hex(instr).upper()[2:], "0" * (8 - len(bin(instr)[2:])) + bin(instr)[2:]
            )
            self.step()
            print(self.registers, self.pc, self.sp)
