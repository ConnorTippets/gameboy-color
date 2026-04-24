from .memory import Memory
from .util import sign_convert

ZERO_FLAG = 0b10000000
SUB_FLAG = 0b01000000
HALF_CARRY_FLAG = 0b00100000
CARRY_FLAG = 0b00010000


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
                self.registers["F"] &= ~SUB_FLAG

                if not ((1 << 7) & self.registers["H"]):
                    self.registers["F"] |= ZERO_FLAG
            case 0b00010001:  # RL C
                val = self.registers["C"] << 1
                lsb = (val & 0xFF) | ((self.registers["F"] & CARRY_FLAG) >> 4)

                if (val & 0xFF00) >> 8:
                    self.registers["F"] |= CARRY_FLAG
                else:
                    self.registers["F"] &= ~CARRY_FLAG

                self.registers["F"] &= ~SUB_FLAG
                self.registers["F"] &= ~HALF_CARRY_FLAG

                if lsb == 0:
                    self.registers["F"] |= ZERO_FLAG
                else:
                    self.registers["F"] &= ~ZERO_FLAG

                self.registers["C"] = lsb
            case _:
                raise Exception(
                    f"Unknown 0xCB instruction opcode: {"0"*(8-len(bin(opcode)[2:]))+bin(opcode)[2:]}"
                )

    def _ld_reg_imm8(self, reg: str):
        imm = self.memory.read_byte(self.pc)
        self.pc += 1
        self.registers[reg] = imm

    def _ld_reg16_imm16(self, reg_high: str, reg_low: str):
        imm = self.memory.read_word(self.pc)
        self.pc += 2
        self.registers[reg_low] = imm & 0xFF
        self.registers[reg_high] = (imm & 0xFF00) >> 8

    def _inc_reg(self, reg: str):
        result = (self.registers[reg] + 1) & 0xFF
        self.registers["F"] &= ~SUB_FLAG

        if result == 0:
            self.registers["F"] |= ZERO_FLAG

        if (self.registers[reg] & 0xF) + 1 > 0xF:
            self.registers["F"] |= HALF_CARRY_FLAG

        self.registers[reg] = result

    def _inc_reg16(self, reg_high: str, reg_low: str):
        self._set_reg16(reg_high, reg_low, self._get_reg16(reg_high, reg_low) + 1)

    def _dec_reg(self, reg: str):
        result = (self.registers[reg] - 1) & 0xFF
        self.registers["F"] |= SUB_FLAG

        if result == 0:
            self.registers["F"] |= ZERO_FLAG

        if (result & 0xF) == 0xF:
            self.registers["F"] |= HALF_CARRY_FLAG

        self.registers[reg] = result

    def _get_reg16(self, reg_high: str, reg_low: str) -> int:
        return (self.registers[reg_high] << 8) | self.registers[reg_low]

    def _set_reg16(self, reg_high: str, reg_low: str, val: int):
        self.registers[reg_high] = (val & 0xFF00) >> 8
        self.registers[reg_low] = val & 0xFF

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
                self._ld_reg16_imm16("H", "L")
            case 0b00110010:  # LD [HL-], A
                hl = self._get_reg16("H", "L")
                self.memory.write_byte(hl, self.registers["A"])
                hl -= 1
                self._set_reg16("H", "L", hl)
            case 0b11001011:  # 0xCB: Read next byte for opcode
                self.cb_step()
            case 0b00100000:  # JR NZ, IMM8
                jmp = self.memory.read_byte(self.pc)
                self.pc += 1
                if not (ZERO_FLAG & self.registers["F"]):
                    self.pc += sign_convert(jmp)
            case 0b00001110:  # LD C, IMM8
                self._ld_reg_imm8("C")
            case 0b00111110:  # LD A, IMM8
                self._ld_reg_imm8("A")
            case 0b11100010:  # LDH C, A
                self.memory.write_byte(
                    0xFF00 | self.registers["C"], self.registers["A"]
                )
            case 0b00001100:  # INC C
                self._inc_reg("C")
            case 0b01110111:  # LD HL, A
                hl = self._get_reg16("H", "L")
                self.memory.write_byte(hl, self.registers["A"])
                self.registers["L"] = hl & 0xFF
                self.registers["H"] = (hl & 0xFF00) >> 8
            case 0b11100000:  # LDH IMM8, A
                self.memory.write_byte(
                    0xFF00 | self.memory.read_byte(self.pc), self.registers["A"]
                )
                self.pc += 1
            case 0b00010001:  # LD DE, IMM16
                self._ld_reg16_imm16("D", "E")
            case 0b00011010:  # LD A, [DE]
                self.registers["A"] = self.memory.read_byte(self._get_reg16("D", "E"))
            case 0b11001101:  # CALL IMM16
                addr = self.memory.read_word(self.pc)
                self.pc += 2
                self.sp -= 2
                self.memory.write_word(self.sp, self.pc)
                self.pc = addr
            case 0b01001111:  # LD C, A
                self.registers["C"] = self.registers["A"]
            case 0b00000110:  # LD B, IMM8
                self._ld_reg_imm8("B")
            case 0b11000101:  # PUSH BC
                self.sp -= 2
                self.memory.write_word(self.sp, self._get_reg16("B", "C"))
            case 0b00010111:  # RLA
                val = self.registers["A"] << 1
                lsb = (val & 0xFF) | ((self.registers["F"] & CARRY_FLAG) >> 4)

                if (val & 0xFF00) >> 8:
                    self.registers["F"] |= CARRY_FLAG
                else:
                    self.registers["F"] &= ~CARRY_FLAG

                self.registers["F"] &= ~SUB_FLAG
                self.registers["F"] &= ~HALF_CARRY_FLAG
                self.registers["F"] |= ZERO_FLAG

                self.registers["A"] = lsb
            case 0b11000001:  # POP BC
                self._set_reg16("B", "C", self.memory.read_word(self.sp))
                self.sp += 2
            case 0b00000101:  # DEC B
                self._dec_reg("B")
            case 0b00100010:  # LD [HL+], A
                hl = self._get_reg16("H", "L")
                self.memory.write_byte(hl, self.registers["A"])
                hl += 1
                self._set_reg16("H", "L", hl)
            case 0b00100011:  # INC HL
                self._inc_reg16("H", "L")
            case 0b11001001:  # RET
                addr = self.memory.read_word(self.sp)
                self.sp += 2
                self.pc = addr
            case 0b00010011:  # INC DE
                self._inc_reg16("D", "E")
            case 0b01111011:  # LD A, E
                self.registers["A"] = self.registers["E"]
            case 0b11111110:  # CP IMM8
                value = self.memory.read_byte(self.pc)
                result = value - self.registers["A"]
                self.pc += 1

                self.registers["F"] |= SUB_FLAG

                if result == 0:
                    self.registers["F"] |= ZERO_FLAG
                else:
                    self.registers["F"] &= ~ZERO_FLAG

                if value > self.registers["A"]:
                    self.registers["F"] |= CARRY_FLAG
                else:
                    self.registers["F"] &= ~CARRY_FLAG

                if (self.registers["A"] & 0xF) < (value & 0xF):
                    self.registers["F"] |= HALF_CARRY_FLAG
                else:
                    self.registers["F"] &= ~HALF_CARRY_FLAG
            case 0b11101010:  # LD IMM16, A
                self.memory.write_byte(
                    self.memory.read_word(self.pc), self.registers["A"]
                )
                self.pc += 2
            case 0b00111101:  # DEC A
                self._dec_reg("A")
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
