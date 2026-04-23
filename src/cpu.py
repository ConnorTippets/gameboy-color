from .memory import Memory


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
                return
            case 0b10101111:  # XOR A
                self.registers["A"] = 0x00
                return
            case 0b00100001:  # LD HL, IMM16
                imm = self.memory.read_word(self.pc)
                self.pc += 2
                self.registers["L"] = imm & 0xFF
                self.registers["H"] = (imm & 0xFF00) >> 8
                return
            case 0b00110010:  # LD HL-, 
            case _:
                raise Exception(
                    f"Unknown instruction opcode: {"0"*(8-len(bin(opcode)[2:]))+bin(opcode)[2:]}"
                )

    def run(self):
        # placeholder, accurate timing will be stubbed in later
        while True:
            self.step()
            print(self.registers, self.pc, self.sp)
