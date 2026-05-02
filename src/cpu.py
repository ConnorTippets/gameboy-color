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
        self.interrupts_enabled = False

    def _bit(self, bit: int, reg: str):
        self.registers["F"] &= ~SUB_FLAG
        self.registers["F"] |= HALF_CARRY_FLAG

        if not ((1 << bit) & self.registers[reg]):
            self.registers["F"] |= ZERO_FLAG
        else:
            self.registers["F"] &= ~ZERO_FLAG

    def _bit_hl(self, bit: int):
        self.registers["F"] &= ~SUB_FLAG
        self.registers["F"] |= HALF_CARRY_FLAG

        if not ((1 << bit) & self.memory.read_byte(self._get_reg16("H", "L"))):
            self.registers["F"] |= ZERO_FLAG
        else:
            self.registers["F"] &= ~ZERO_FLAG

    def _res(self, bit: int, reg: str):
        self.registers[reg] &= ~(1 << bit)

    def _res_hl(self, bit: int):
        hl = self._get_reg16("H", "L")
        self.memory.write_byte(hl, self.memory.read_byte(hl) & (~(1 << bit)))

    def _set(self, bit: int, reg: str):
        self.registers[reg] |= 1 << bit

    def _set_hl(self, bit: int):
        hl = self._get_reg16("H", "L")
        self.memory.write_byte(hl, self.memory.read_byte(hl) | (1 << bit))

    def _rlc_reg(self, reg: str):
        new_carry = self.registers[reg] & 0b10000000

        lsb = ((self.registers[reg] << 1) & 0xFF) | (new_carry >> 7)

        if new_carry:
            self.registers["F"] |= CARRY_FLAG
        else:
            self.registers["F"] &= ~CARRY_FLAG

        if lsb == 0:
            self.registers["F"] |= ZERO_FLAG
        else:
            self.registers["F"] &= ~ZERO_FLAG

        self.registers["F"] &= ~SUB_FLAG
        self.registers["F"] &= ~HALF_CARRY_FLAG

        self.registers[reg] = lsb

    def _rlc_hl(self):
        hl = self._get_reg16("H", "L")
        value = self.memory.read_byte(hl)
        new_carry = value & 0b10000000

        lsb = ((value << 1) & 0xFF) | (new_carry >> 7)

        if new_carry:
            self.registers["F"] |= CARRY_FLAG
        else:
            self.registers["F"] &= ~CARRY_FLAG

        if lsb == 0:
            self.registers["F"] |= ZERO_FLAG
        else:
            self.registers["F"] &= ~ZERO_FLAG

        self.registers["F"] &= ~SUB_FLAG
        self.registers["F"] &= ~HALF_CARRY_FLAG

        self.memory.write_byte(hl, lsb)

    def _rrc_reg(self, reg: str):
        new_carry = self.registers[reg] & 0b1

        lsb = ((self.registers[reg] >> 1) & 0xFF) | new_carry

        if new_carry:
            self.registers["F"] |= CARRY_FLAG
        else:
            self.registers["F"] &= ~CARRY_FLAG

        if lsb == 0:
            self.registers["F"] |= ZERO_FLAG
        else:
            self.registers["F"] &= ~ZERO_FLAG

        self.registers["F"] &= ~SUB_FLAG
        self.registers["F"] &= ~HALF_CARRY_FLAG

        self.registers[reg] = lsb

    def _rrc_hl(self):
        hl = self._get_reg16("H", "L")
        value = self.memory.read_byte(hl)
        new_carry = value & 0b1

        lsb = ((value >> 1) & 0xFF) | new_carry

        if new_carry:
            self.registers["F"] |= CARRY_FLAG
        else:
            self.registers["F"] &= ~CARRY_FLAG

        if lsb == 0:
            self.registers["F"] |= ZERO_FLAG
        else:
            self.registers["F"] &= ~ZERO_FLAG

        self.registers["F"] &= ~SUB_FLAG
        self.registers["F"] &= ~HALF_CARRY_FLAG

        self.memory.write_byte(hl, lsb)

    def _rl_reg(self, reg: str):
        old_carry = (self.registers["F"] & CARRY_FLAG) >> 4
        new_carry = self.registers[reg] & 0b10000000

        lsb = ((self.registers[reg] << 1) & 0xFF) | old_carry

        if new_carry:
            self.registers["F"] |= CARRY_FLAG
        else:
            self.registers["F"] &= ~CARRY_FLAG

        if lsb == 0:
            self.registers["F"] |= ZERO_FLAG
        else:
            self.registers["F"] &= ~ZERO_FLAG

        self.registers["F"] &= ~SUB_FLAG
        self.registers["F"] &= ~HALF_CARRY_FLAG

        self.registers[reg] = lsb

    def _rl_hl(self):
        hl = self._get_reg16("H", "L")
        value = self.memory.read_byte(hl)
        old_carry = (self.registers["F"] & CARRY_FLAG) >> 4
        new_carry = value & 0b10000000

        lsb = ((value << 1) & 0xFF) | old_carry

        if new_carry:
            self.registers["F"] |= CARRY_FLAG
        else:
            self.registers["F"] &= ~CARRY_FLAG

        if lsb == 0:
            self.registers["F"] |= ZERO_FLAG
        else:
            self.registers["F"] &= ~ZERO_FLAG

        self.registers["F"] &= ~SUB_FLAG
        self.registers["F"] &= ~HALF_CARRY_FLAG

        self.memory.write_byte(hl, lsb)

    def _rr_reg(self, reg: str):
        old_carry = (self.registers["F"] & CARRY_FLAG) << 3
        new_carry = self.registers[reg] & 0b1

        lsb = ((self.registers[reg] >> 1) & 0xFF) | old_carry

        if new_carry:
            self.registers["F"] |= CARRY_FLAG
        else:
            self.registers["F"] &= ~CARRY_FLAG

        if lsb == 0:
            self.registers["F"] |= ZERO_FLAG
        else:
            self.registers["F"] &= ~ZERO_FLAG

        self.registers["F"] &= ~SUB_FLAG
        self.registers["F"] &= ~HALF_CARRY_FLAG

        self.registers[reg] = lsb

    def _rr_hl(self):
        hl = self._get_reg16("H", "L")
        value = self.memory.read_byte(hl)
        old_carry = (self.registers["F"] & CARRY_FLAG) << 3
        new_carry = value & 0b1

        lsb = ((value >> 1) & 0xFF) | old_carry

        if new_carry:
            self.registers["F"] |= CARRY_FLAG
        else:
            self.registers["F"] &= ~CARRY_FLAG

        if lsb == 0:
            self.registers["F"] |= ZERO_FLAG
        else:
            self.registers["F"] &= ~ZERO_FLAG

        self.registers["F"] &= ~SUB_FLAG
        self.registers["F"] &= ~HALF_CARRY_FLAG

        self.memory.write_byte(hl, lsb)

    def _sla_reg(self, reg: str):
        new_carry = self.registers[reg] & 0b10000000

        lsb = (self.registers[reg] << 1) & 0xFF

        if new_carry:
            self.registers["F"] |= CARRY_FLAG
        else:
            self.registers["F"] &= ~CARRY_FLAG

        if lsb == 0:
            self.registers["F"] |= ZERO_FLAG
        else:
            self.registers["F"] &= ~ZERO_FLAG

        self.registers["F"] &= ~SUB_FLAG
        self.registers["F"] &= ~HALF_CARRY_FLAG

        self.registers[reg] = lsb

    def _sla_hl(self):
        hl = self._get_reg16("H", "L")
        value = self.memory.read_byte(hl)
        new_carry = value & 0b10000000

        lsb = (value << 1) & 0xFF

        if new_carry:
            self.registers["F"] |= CARRY_FLAG
        else:
            self.registers["F"] &= ~CARRY_FLAG

        if lsb == 0:
            self.registers["F"] |= ZERO_FLAG
        else:
            self.registers["F"] &= ~ZERO_FLAG

        self.registers["F"] &= ~SUB_FLAG
        self.registers["F"] &= ~HALF_CARRY_FLAG

        self.memory.write_byte(hl, lsb)

    def _sra_reg(self, reg: str):
        new_carry = self.registers[reg] & 0b1
        bit_7 = self.registers[reg] & 0b10000000

        lsb = ((self.registers[reg] >> 1) & 0xFF) | bit_7

        if new_carry:
            self.registers["F"] |= CARRY_FLAG
        else:
            self.registers["F"] &= ~CARRY_FLAG

        if lsb == 0:
            self.registers["F"] |= ZERO_FLAG
        else:
            self.registers["F"] &= ~ZERO_FLAG

        self.registers["F"] &= ~SUB_FLAG
        self.registers["F"] &= ~HALF_CARRY_FLAG

        self.registers[reg] = lsb

    def _sra_hl(self):
        hl = self._get_reg16("H", "L")
        value = self.memory.read_byte(hl)
        new_carry = value & 0b1
        bit_7 = value & 0b10000000

        lsb = ((value >> 1) & 0xFF) | bit_7

        if new_carry:
            self.registers["F"] |= CARRY_FLAG
        else:
            self.registers["F"] &= ~CARRY_FLAG

        if lsb == 0:
            self.registers["F"] |= ZERO_FLAG
        else:
            self.registers["F"] &= ~ZERO_FLAG

        self.registers["F"] &= ~SUB_FLAG
        self.registers["F"] &= ~HALF_CARRY_FLAG

        self.memory.write_byte(hl, lsb)

    def _swap_reg(self, reg: str):
        value = self.registers[reg]
        msb = (value & 0xF0) >> 4
        lsb = value & 0xF
        self.registers[reg] = (lsb << 4) | msb

        self.registers["F"] &= ~SUB_FLAG
        self.registers["F"] &= ~HALF_CARRY_FLAG
        self.registers["F"] &= ~CARRY_FLAG

        if self.registers[reg] == 0:
            self.registers["F"] |= ZERO_FLAG
        else:
            self.registers["F"] &= ~ZERO_FLAG

    def _swap_hl(self):
        hl = self._get_reg16("H", "L")
        value = self.memory.read_byte(hl)
        msb = (value & 0xF0) >> 4
        lsb = value & 0xF
        new_value = (lsb << 4) | msb
        self.memory.write_byte(hl, new_value)

        self.registers["F"] &= ~SUB_FLAG
        self.registers["F"] &= ~HALF_CARRY_FLAG
        self.registers["F"] &= ~CARRY_FLAG

        if new_value == 0:
            self.registers["F"] |= ZERO_FLAG
        else:
            self.registers["F"] &= ~ZERO_FLAG

    def _srl_reg(self, reg: str):
        new_carry = self.registers[reg] & 0b1

        lsb = (self.registers[reg] >> 1) & 0xFF

        if new_carry:
            self.registers["F"] |= CARRY_FLAG
        else:
            self.registers["F"] &= ~CARRY_FLAG

        if lsb == 0:
            self.registers["F"] |= ZERO_FLAG
        else:
            self.registers["F"] &= ~ZERO_FLAG

        self.registers["F"] &= ~SUB_FLAG
        self.registers["F"] &= ~HALF_CARRY_FLAG

        self.registers[reg] = lsb

    def _srl_hl(self):
        hl = self._get_reg16("H", "L")
        value = self.memory.read_byte(hl)
        new_carry = value & 0b1

        lsb = (value >> 1) & 0xFF

        if new_carry:
            self.registers["F"] |= CARRY_FLAG
        else:
            self.registers["F"] &= ~CARRY_FLAG

        if lsb == 0:
            self.registers["F"] |= ZERO_FLAG
        else:
            self.registers["F"] &= ~ZERO_FLAG

        self.registers["F"] &= ~SUB_FLAG
        self.registers["F"] &= ~HALF_CARRY_FLAG

        self.memory.write_byte(hl, lsb)

    def cb_step(self):
        opcode = self.memory.read_byte(self.pc)
        self.pc += 1

        match opcode:
            case 0x00:
                self._rlc_reg("B")  # RLC B
            case 0x01:
                self._rlc_reg("C")  # RLC C
            case 0x02:
                self._rlc_reg("D")  # RLC D
            case 0x03:
                self._rlc_reg("E")  # RLC E
            case 0x04:
                self._rlc_reg("H")  # RLC H
            case 0x05:
                self._rlc_reg("L")  # RLC L
            case 0x06:
                self._rlc_hl()  # RLC [HL]
            case 0x07:
                self._rlc_reg("A")  # RLC A

            case 0x08:
                self._rrc_reg("B")  # RRC B
            case 0x09:
                self._rrc_reg("C")  # RRC C
            case 0x0A:
                self._rrc_reg("D")  # RRC D
            case 0x0B:
                self._rrc_reg("E")  # RRC E
            case 0x0C:
                self._rrc_reg("H")  # RRC H
            case 0x0D:
                self._rrc_reg("L")  # RRC L
            case 0x0E:
                self._rrc_hl()  # RRC [HL]
            case 0x0F:
                self._rrc_reg("A")  # RRC A

            case 0x10:
                self._rl_reg("B")  # RL B
            case 0x11:
                self._rl_reg("C")  # RL C
            case 0x12:
                self._rl_reg("D")  # RL D
            case 0x13:
                self._rl_reg("E")  # RL E
            case 0x14:
                self._rl_reg("H")  # RL H
            case 0x15:
                self._rl_reg("L")  # RL L
            case 0x16:
                self._rl_hl()  # RL [HL]
            case 0x17:
                self._rl_reg("A")  # RL A

            case 0x18:
                self._rr_reg("B")  # RR B
            case 0x19:
                self._rr_reg("C")  # RR C
            case 0x1A:
                self._rr_reg("D")  # RR D
            case 0x1B:
                self._rr_reg("E")  # RR E
            case 0x1C:
                self._rr_reg("H")  # RR H
            case 0x1D:
                self._rr_reg("L")  # RR L
            case 0x1E:
                self._rr_hl()  # RR [HL]
            case 0x1F:
                self._rr_reg("A")  # RR A

            case 0x20:
                self._sla_reg("B")  # SLA B
            case 0x21:
                self._sla_reg("C")  # SLA C
            case 0x22:
                self._sla_reg("D")  # SLA D
            case 0x23:
                self._sla_reg("E")  # SLA E
            case 0x24:
                self._sla_reg("H")  # SLA H
            case 0x25:
                self._sla_reg("L")  # SLA L
            case 0x26:
                self._sla_hl()  # SLA [HL]
            case 0x27:
                self._sla_reg("A")  # SLA A

            case 0x28:
                self._sra_reg("B")  # SRA B
            case 0x29:
                self._sra_reg("C")  # SRA C
            case 0x2A:
                self._sra_reg("D")  # SRA D
            case 0x2B:
                self._sra_reg("E")  # SRA E
            case 0x2C:
                self._sra_reg("H")  # SRA H
            case 0x2D:
                self._sra_reg("L")  # SRA L
            case 0x2E:
                self._sra_hl()  # SRA [HL]
            case 0x2F:
                self._sra_reg("A")  # SRA A

            case 0x30:
                self._swap_reg("B")  # SWAP B
            case 0x31:
                self._swap_reg("C")  # SWAP C
            case 0x32:
                self._swap_reg("D")  # SWAP D
            case 0x33:
                self._swap_reg("E")  # SWAP E
            case 0x34:
                self._swap_reg("H")  # SWAP H
            case 0x35:
                self._swap_reg("L")  # SWAP L
            case 0x36:
                self._swap_hl()  # SWAP [HL]
            case 0x37:
                self._swap_reg("A")  # SWAP A

            case 0x38:
                self._srl_reg("B")  # SRL B
            case 0x39:
                self._srl_reg("C")  # SRL C
            case 0x3A:
                self._srl_reg("D")  # SRL D
            case 0x3B:
                self._srl_reg("E")  # SRL E
            case 0x3C:
                self._srl_reg("H")  # SRL H
            case 0x3D:
                self._srl_reg("L")  # SRL L
            case 0x3E:
                self._srl_hl()  # SRL [HL]
            case 0x3F:
                self._srl_reg("A")  # SRL A

            case 0x40:
                self._bit(0, "B")  # BIT 0, B
            case 0x41:
                self._bit(0, "C")  # BIT 0, C
            case 0x42:
                self._bit(0, "D")  # BIT 0, D
            case 0x43:
                self._bit(0, "E")  # BIT 0, E
            case 0x44:
                self._bit(0, "H")  # BIT 0, H
            case 0x45:
                self._bit(0, "L")  # BIT 0, L
            case 0x46:
                self._bit_hl(0)  # BIT 0, [HL]
            case 0x47:
                self._bit(0, "A")  # BIT 0, A
            case 0x48:
                self._bit(1, "B")  # BIT 1, B
            case 0x49:
                self._bit(1, "C")  # BIT 1, C
            case 0x4A:
                self._bit(1, "D")  # BIT 1, D
            case 0x4B:
                self._bit(1, "E")  # BIT 1, E
            case 0x4C:
                self._bit(1, "H")  # BIT 1, H
            case 0x4D:
                self._bit(1, "L")  # BIT 1, L
            case 0x4E:
                self._bit_hl(1)  # BIT 1, [HL]
            case 0x4F:
                self._bit(1, "A")  # BIT 1, A
            case 0x50:
                self._bit(2, "B")  # BIT 2, B
            case 0x51:
                self._bit(2, "C")  # BIT 2, C
            case 0x52:
                self._bit(2, "D")  # BIT 2, D
            case 0x53:
                self._bit(2, "E")  # BIT 2, E
            case 0x54:
                self._bit(2, "H")  # BIT 2, H
            case 0x55:
                self._bit(2, "L")  # BIT 2, L
            case 0x56:
                self._bit_hl(2)  # BIT 2, [HL]
            case 0x57:
                self._bit(2, "A")  # BIT 2, A
            case 0x58:
                self._bit(3, "B")  # BIT 3, B
            case 0x59:
                self._bit(3, "C")  # BIT 3, C
            case 0x5A:
                self._bit(3, "D")  # BIT 3, D
            case 0x5B:
                self._bit(3, "E")  # BIT 3, E
            case 0x5C:
                self._bit(3, "H")  # BIT 3, H
            case 0x5D:
                self._bit(3, "L")  # BIT 3, L
            case 0x5E:
                self._bit_hl(3)  # BIT 3, [HL]
            case 0x5F:
                self._bit(3, "A")  # BIT 3, A
            case 0x60:
                self._bit(4, "B")  # BIT 4, B
            case 0x61:
                self._bit(4, "C")  # BIT 4, C
            case 0x62:
                self._bit(4, "D")  # BIT 4, D
            case 0x63:
                self._bit(4, "E")  # BIT 4, E
            case 0x64:
                self._bit(4, "H")  # BIT 4, H
            case 0x65:
                self._bit(4, "L")  # BIT 4, L
            case 0x66:
                self._bit_hl(4)  # BIT 4, [HL]
            case 0x67:
                self._bit(4, "A")  # BIT 4, A
            case 0x68:
                self._bit(5, "B")  # BIT 5, B
            case 0x69:
                self._bit(5, "C")  # BIT 5, C
            case 0x6A:
                self._bit(5, "D")  # BIT 5, D
            case 0x6B:
                self._bit(5, "E")  # BIT 5, E
            case 0x6C:
                self._bit(5, "H")  # BIT 5, H
            case 0x6D:
                self._bit(5, "L")  # BIT 5, L
            case 0x6E:
                self._bit_hl(5)  # BIT 5, [HL]
            case 0x6F:
                self._bit(5, "A")  # BIT 5, A
            case 0x70:
                self._bit(6, "B")  # BIT 6, B
            case 0x71:
                self._bit(6, "C")  # BIT 6, C
            case 0x72:
                self._bit(6, "D")  # BIT 6, D
            case 0x73:
                self._bit(6, "E")  # BIT 6, E
            case 0x74:
                self._bit(6, "H")  # BIT 6, H
            case 0x75:
                self._bit(6, "L")  # BIT 6, L
            case 0x76:
                self._bit_hl(6)  # BIT 6, [HL]
            case 0x77:
                self._bit(6, "A")  # BIT 6, A
            case 0x78:
                self._bit(7, "B")  # BIT 7, B
            case 0x79:
                self._bit(7, "C")  # BIT 7, C
            case 0x7A:
                self._bit(7, "D")  # BIT 7, D
            case 0x7B:
                self._bit(7, "E")  # BIT 7, E
            case 0x7C:
                self._bit(7, "H")  # BIT 7, H
            case 0x7D:
                self._bit(7, "L")  # BIT 7, L
            case 0x7E:
                self._bit_hl(7)  # BIT 7, [HL]
            case 0x7F:
                self._bit(7, "A")  # BIT 7, A

            case 0x80:
                self._res(0, "B")  # RES 0, B
            case 0x81:
                self._res(0, "C")  # RES 0, C
            case 0x82:
                self._res(0, "D")  # RES 0, D
            case 0x83:
                self._res(0, "E")  # RES 0, E
            case 0x84:
                self._res(0, "H")  # RES 0, H
            case 0x85:
                self._res(0, "L")  # RES 0, L
            case 0x86:
                self._res_hl(0)  # RES 0, [HL]
            case 0x87:
                self._res(0, "A")  # RES 0, A
            case 0x88:
                self._res(1, "B")  # RES 1, B
            case 0x89:
                self._res(1, "C")  # RES 1, C
            case 0x8A:
                self._res(1, "D")  # RES 1, D
            case 0x8B:
                self._res(1, "E")  # RES 1, E
            case 0x8C:
                self._res(1, "H")  # RES 1, H
            case 0x8D:
                self._res(1, "L")  # RES 1, L
            case 0x8E:
                self._res_hl(1)  # RES 1, [HL]
            case 0x8F:
                self._res(1, "A")  # RES 1, A
            case 0x90:
                self._res(2, "B")  # RES 2, B
            case 0x91:
                self._res(2, "C")  # RES 2, C
            case 0x92:
                self._res(2, "D")  # RES 2, D
            case 0x93:
                self._res(2, "E")  # RES 2, E
            case 0x94:
                self._res(2, "H")  # RES 2, H
            case 0x95:
                self._res(2, "L")  # RES 2, L
            case 0x96:
                self._res_hl(2)  # RES 2, [HL]
            case 0x97:
                self._res(2, "A")  # RES 2, A
            case 0x98:
                self._res(3, "B")  # RES 3, B
            case 0x99:
                self._res(3, "C")  # RES 3, C
            case 0x9A:
                self._res(3, "D")  # RES 3, D
            case 0x9B:
                self._res(3, "E")  # RES 3, E
            case 0x9C:
                self._res(3, "H")  # RES 3, H
            case 0x9D:
                self._res(3, "L")  # RES 3, L
            case 0x9E:
                self._res_hl(3)  # RES 3, [HL]
            case 0x9F:
                self._res(3, "A")  # RES 3, A
            case 0xA0:
                self._res(4, "B")  # RES 4, B
            case 0xA1:
                self._res(4, "C")  # RES 4, C
            case 0xA2:
                self._res(4, "D")  # RES 4, D
            case 0xA3:
                self._res(4, "E")  # RES 4, E
            case 0xA4:
                self._res(4, "H")  # RES 4, H
            case 0xA5:
                self._res(4, "L")  # RES 4, L
            case 0xA6:
                self._res_hl(4)  # RES 4, [HL]
            case 0xA7:
                self._res(4, "A")  # RES 4, A
            case 0xA8:
                self._res(5, "B")  # RES 5, B
            case 0xA9:
                self._res(5, "C")  # RES 5, C
            case 0xAA:
                self._res(5, "D")  # RES 5, D
            case 0xAB:
                self._res(5, "E")  # RES 5, E
            case 0xAC:
                self._res(5, "H")  # RES 5, H
            case 0xAD:
                self._res(5, "L")  # RES 5, L
            case 0xAE:
                self._res_hl(5)  # RES 5, [HL]
            case 0xAF:
                self._res(5, "A")  # RES 5, A
            case 0xB0:
                self._res(6, "B")  # RES 6, B
            case 0xB1:
                self._res(6, "C")  # RES 6, C
            case 0xB2:
                self._res(6, "D")  # RES 6, D
            case 0xB3:
                self._res(6, "E")  # RES 6, E
            case 0xB4:
                self._res(6, "H")  # RES 6, H
            case 0xB5:
                self._res(6, "L")  # RES 6, L
            case 0xB6:
                self._res_hl(6)  # RES 6, [HL]
            case 0xB7:
                self._res(6, "A")  # RES 6, A
            case 0xB8:
                self._res(7, "B")  # RES 7, B
            case 0xB9:
                self._res(7, "C")  # RES 7, C
            case 0xBA:
                self._res(7, "D")  # RES 7, D
            case 0xBB:
                self._res(7, "E")  # RES 7, E
            case 0xBC:
                self._res(7, "H")  # RES 7, H
            case 0xBD:
                self._res(7, "L")  # RES 7, L
            case 0xBE:
                self._res_hl(7)  # RES 7, [HL]
            case 0xBF:
                self._res(7, "A")  # RES 7, A

            case 0xC0:
                self._set(0, "B")  # SET 0, B
            case 0xC1:
                self._set(0, "C")  # SET 0, C
            case 0xC2:
                self._set(0, "D")  # SET 0, D
            case 0xC3:
                self._set(0, "E")  # SET 0, E
            case 0xC4:
                self._set(0, "H")  # SET 0, H
            case 0xC5:
                self._set(0, "L")  # SET 0, L
            case 0xC6:
                self._set_hl(0)  # SET 0, [HL]
            case 0xC7:
                self._set(0, "A")  # SET 0, A
            case 0xC8:
                self._set(1, "B")  # SET 1, B
            case 0xC9:
                self._set(1, "C")  # SET 1, C
            case 0xCA:
                self._set(1, "D")  # SET 1, D
            case 0xCB:
                self._set(1, "E")  # SET 1, E
            case 0xCC:
                self._set(1, "H")  # SET 1, H
            case 0xCD:
                self._set(1, "L")  # SET 1, L
            case 0xCE:
                self._set_hl(1)  # SET 1, [HL]
            case 0xCF:
                self._set(1, "A")  # SET 1, A
            case 0xD0:
                self._set(2, "B")  # SET 2, B
            case 0xD1:
                self._set(2, "C")  # SET 2, C
            case 0xD2:
                self._set(2, "D")  # SET 2, D
            case 0xD3:
                self._set(2, "E")  # SET 2, E
            case 0xD4:
                self._set(2, "H")  # SET 2, H
            case 0xD5:
                self._set(2, "L")  # SET 2, L
            case 0xD6:
                self._set_hl(2)  # SET 2, [HL]
            case 0xD7:
                self._set(2, "A")  # SET 2, A
            case 0xD8:
                self._set(3, "B")  # SET 3, B
            case 0xD9:
                self._set(3, "C")  # SET 3, C
            case 0xDA:
                self._set(3, "D")  # SET 3, D
            case 0xDB:
                self._set(3, "E")  # SET 3, E
            case 0xDC:
                self._set(3, "H")  # SET 3, H
            case 0xDD:
                self._set(3, "L")  # SET 3, L
            case 0xDE:
                self._set_hl(3)  # SET 3, [HL]
            case 0xDF:
                self._set(3, "A")  # SET 3, A
            case 0xE0:
                self._set(4, "B")  # SET 4, B
            case 0xE1:
                self._set(4, "C")  # SET 4, C
            case 0xE2:
                self._set(4, "D")  # SET 4, D
            case 0xE3:
                self._set(4, "E")  # SET 4, E
            case 0xE4:
                self._set(4, "H")  # SET 4, H
            case 0xE5:
                self._set(4, "L")  # SET 4, L
            case 0xE6:
                self._set_hl(4)  # SET 4, [HL]
            case 0xE7:
                self._set(4, "A")  # SET 4, A
            case 0xE8:
                self._set(5, "B")  # SET 5, B
            case 0xE9:
                self._set(5, "C")  # SET 5, C
            case 0xEA:
                self._set(5, "D")  # SET 5, D
            case 0xEB:
                self._set(5, "E")  # SET 5, E
            case 0xEC:
                self._set(5, "H")  # SET 5, H
            case 0xED:
                self._set(5, "L")  # SET 5, L
            case 0xEE:
                self._set_hl(5)  # SET 5, [HL]
            case 0xEF:
                self._set(5, "A")  # SET 5, A
            case 0xF0:
                self._set(6, "B")  # SET 6, B
            case 0xF1:
                self._set(6, "C")  # SET 6, C
            case 0xF2:
                self._set(6, "D")  # SET 6, D
            case 0xF3:
                self._set(6, "E")  # SET 6, E
            case 0xF4:
                self._set(6, "H")  # SET 6, H
            case 0xF5:
                self._set(6, "L")  # SET 6, L
            case 0xF6:
                self._set_hl(6)  # SET 6, [HL]
            case 0xF7:
                self._set(6, "A")  # SET 6, A
            case 0xF8:
                self._set(7, "B")  # SET 7, B
            case 0xF9:
                self._set(7, "C")  # SET 7, C
            case 0xFA:
                self._set(7, "D")  # SET 7, D
            case 0xFB:
                self._set(7, "E")  # SET 7, E
            case 0xFC:
                self._set(7, "H")  # SET 7, H
            case 0xFD:
                self._set(7, "L")  # SET 7, L
            case 0xFE:
                self._set_hl(7)  # SET 7, [HL]
            case 0xFF:
                self._set(7, "A")  # SET 7, A
            case _:
                raise Exception(
                    f"Unknown 0xCB instruction opcode: {"0"*(8-len(bin(opcode)[2:]))+bin(opcode)[2:]}"
                )

    def _ld_reg_imm8(self, reg: str):
        imm = self.memory.read_byte(self.pc)
        self.pc += 1
        self.registers[reg] = imm

    def _ld_reg16_imm16(self, reg_high: str, reg_low: str):
        imm = self._get_imm16()
        self.registers[reg_low] = imm & 0xFF
        self.registers[reg_high] = (imm & 0xFF00) >> 8

    def _inc_reg(self, reg: str):
        result = (self.registers[reg] + 1) & 0xFF
        self.registers["F"] &= ~SUB_FLAG

        if result == 0:
            self.registers["F"] |= ZERO_FLAG
        else:
            self.registers["F"] &= ~ZERO_FLAG

        if (self.registers[reg] & 0xF) + 1 > 0xF:
            self.registers["F"] |= HALF_CARRY_FLAG
        else:
            self.registers["F"] &= ~HALF_CARRY_FLAG

        self.registers[reg] = result

    def _inc_reg16(self, reg_high: str, reg_low: str):
        self._set_reg16(
            reg_high, reg_low, (self._get_reg16(reg_high, reg_low) + 1) & 0xFFFF
        )

    def _dec_reg16(self, reg_high: str, reg_low: str):
        self._set_reg16(
            reg_high, reg_low, (self._get_reg16(reg_high, reg_low) - 1) & 0xFFFF
        )

    def _dec_reg(self, reg: str):
        result = (self.registers[reg] - 1) & 0xFF
        self.registers["F"] |= SUB_FLAG

        if result == 0:
            self.registers["F"] |= ZERO_FLAG
        else:
            self.registers["F"] &= ~ZERO_FLAG

        if (result & 0xF) == 0xF:
            self.registers["F"] |= HALF_CARRY_FLAG
        else:
            self.registers["F"] &= ~HALF_CARRY_FLAG

        self.registers[reg] = result

    def _get_reg16(self, reg_high: str, reg_low: str) -> int:
        return (self.registers[reg_high] << 8) | self.registers[reg_low]

    def _set_reg16(self, reg_high: str, reg_low: str, val: int):
        self.registers[reg_high] = (val & 0xFF00) >> 8
        self.registers[reg_low] = val & 0xFF

    def _jr_cond_imm8(self, cond):
        jmp = self.memory.read_byte(self.pc)
        self.pc += 1
        if cond:
            self.pc += sign_convert(jmp)

    def _get_imm16(self) -> int:
        imm16 = self.memory.read_word(self.pc)
        self.pc += 2
        return imm16

    def _ld_memreg16_reg8(self, reg_high: str, reg_low: str, reg_val: str):
        self.memory.write_byte(
            self._get_reg16(reg_high, reg_low), self.registers[reg_val]
        )

    def _ld_hli_reg8(self, reg_val: str):
        hl = self._get_reg16("H", "L")
        self.memory.write_byte(hl, self.registers[reg_val])
        hl = (hl + 1) & 0xFFFF
        self._set_reg16("H", "L", hl)

    def _ld_hld_reg8(self, reg_val: str):
        hl = self._get_reg16("H", "L")
        self.memory.write_byte(hl, self.registers[reg_val])
        hl = (hl - 1) & 0xFFFF
        self._set_reg16("H", "L", hl)

    def _ld_reg8_memreg16(self, reg_val: str, reg_high: str, reg_low: str):
        self.registers[reg_val] = self.memory.read_byte(
            self._get_reg16(reg_high, reg_low)
        )

    def _ld_reg8_hli(self, reg_val: str):
        hl = self._get_reg16("H", "L")
        self.registers[reg_val] = self.memory.read_byte(hl)
        hl = (hl + 1) & 0xFFFF
        self._set_reg16("H", "L", hl)

    def _ld_reg8_hld(self, reg_val: str):
        hl = self._get_reg16("H", "L")
        self.registers[reg_val] = self.memory.read_byte(hl)
        hl = (hl - 1) & 0xFFFF
        self._set_reg16("H", "L", hl)

    def _add_hl_reg16(self, reg_high: str, reg_low: str):
        reg = self._get_reg16(reg_high, reg_low)
        hl = self._get_reg16("H", "L")
        result = reg + hl
        self.registers["F"] &= ~SUB_FLAG

        if (result & 0x10000) != 0:
            self.registers["F"] |= CARRY_FLAG
        else:
            self.registers["F"] &= ~CARRY_FLAG

        if (reg & 0xFFF) + (hl & 0xFFF) > 0xFFF:
            self.registers["F"] |= HALF_CARRY_FLAG
        else:
            self.registers["F"] &= ~HALF_CARRY_FLAG

        self._set_reg16("H", "L", result & 0xFFFF)

    def _add_hl_sp(self):
        reg = self.sp
        hl = self._get_reg16("H", "L")
        result = reg + hl
        self.registers["F"] &= ~SUB_FLAG

        if (result & 0x10000) != 0:
            self.registers["F"] |= CARRY_FLAG
        else:
            self.registers["F"] &= ~CARRY_FLAG

        if (reg & 0xFFF) + (hl & 0xFFF) > 0xFFF:
            self.registers["F"] |= HALF_CARRY_FLAG
        else:
            self.registers["F"] &= ~HALF_CARRY_FLAG

        self._set_reg16("H", "L", result & 0xFFFF)

    def _inc_hl(self):
        hl = self._get_reg16("H", "L")
        data = self.memory.read_byte(hl)
        result = data + 1
        self.registers["F"] &= ~SUB_FLAG

        if (result & 0xFF) == 0:
            self.registers["F"] |= ZERO_FLAG
        else:
            self.registers["F"] &= ~ZERO_FLAG

        if (data & 0xF) + 1 > 0xF:
            self.registers["F"] |= HALF_CARRY_FLAG
        else:
            self.registers["F"] &= ~HALF_CARRY_FLAG

        self.memory.write_byte(hl, result & 0xFF)

    def _dec_hl(self):
        hl = self._get_reg16("H", "L")
        data = self.memory.read_byte(hl)
        result = data - 1
        self.registers["F"] |= SUB_FLAG

        if (result & 0xFF) == 0:
            self.registers["F"] |= ZERO_FLAG
        else:
            self.registers["F"] &= ~ZERO_FLAG

        if (result & 0xF) == 0xF:
            self.registers["F"] |= HALF_CARRY_FLAG
        else:
            self.registers["F"] &= ~HALF_CARRY_FLAG

        self.memory.write_byte(hl, result & 0xFF)

    def _get_imm8(self):
        imm8 = self.memory.read_byte(self.pc)
        self.pc += 1
        return imm8

    def _ld_hl_imm8(self):
        self.memory.write_byte(self._get_reg16("H", "L"), self._get_imm8())

    def _rlca(self):
        new_carry = self.registers["A"] & 0b10000000

        lsb = ((self.registers["A"] << 1) & 0xFF) | (new_carry >> 7)

        if new_carry:
            self.registers["F"] |= CARRY_FLAG
        else:
            self.registers["F"] &= ~CARRY_FLAG

        self.registers["F"] &= ~ZERO_FLAG
        self.registers["F"] &= ~SUB_FLAG
        self.registers["F"] &= ~HALF_CARRY_FLAG

        self.registers["A"] = lsb

    def _rrca(self):
        new_carry = self.registers["A"] & 0b1

        lsb = ((self.registers["A"] >> 1) & 0xFF) | new_carry

        if new_carry:
            self.registers["F"] |= CARRY_FLAG
        else:
            self.registers["F"] &= ~CARRY_FLAG

        self.registers["F"] &= ~ZERO_FLAG
        self.registers["F"] &= ~SUB_FLAG
        self.registers["F"] &= ~HALF_CARRY_FLAG

        self.registers["A"] = lsb

    def _rla(self):
        old_carry = (self.registers["F"] & CARRY_FLAG) >> 4
        new_carry = self.registers["A"] & 0b10000000

        lsb = ((self.registers["A"] << 1) & 0xFF) | old_carry

        if new_carry:
            self.registers["F"] |= CARRY_FLAG
        else:
            self.registers["F"] &= ~CARRY_FLAG

        self.registers["F"] &= ~ZERO_FLAG
        self.registers["F"] &= ~SUB_FLAG
        self.registers["F"] &= ~HALF_CARRY_FLAG

        self.registers["A"] = lsb

    def _rra(self):
        old_carry = (self.registers["F"] & CARRY_FLAG) << 3
        new_carry = self.registers["A"] & 0b1

        lsb = ((self.registers["A"] >> 1) & 0xFF) | old_carry

        if new_carry:
            self.registers["F"] |= CARRY_FLAG
        else:
            self.registers["F"] &= ~CARRY_FLAG

        self.registers["F"] &= ~ZERO_FLAG
        self.registers["F"] &= ~SUB_FLAG
        self.registers["F"] &= ~HALF_CARRY_FLAG

        self.registers["A"] = lsb

    def _cpl(self):
        self.registers["A"] = ~self.registers["A"]
        self.registers["F"] |= SUB_FLAG
        self.registers["F"] |= HALF_CARRY_FLAG

    def _scf(self):
        self.registers["F"] |= CARRY_FLAG
        self.registers["F"] &= ~SUB_FLAG
        self.registers["F"] &= ~HALF_CARRY_FLAG

    def _ccf(self):
        carry_set = self.registers["F"] & CARRY_FLAG

        if carry_set:
            self.registers["F"] &= ~CARRY_FLAG
        else:
            self.registers["F"] |= CARRY_FLAG

        self.registers["F"] &= ~SUB_FLAG
        self.registers["F"] &= ~HALF_CARRY_FLAG

    def _jr_imm8(self):
        self.pc += 1 + sign_convert(self.memory.read_byte(self.pc))

    def _add_a_reg(self, reg: str):
        value = self.registers[reg]
        result = value + self.registers["A"]

        self.registers["F"] &= ~SUB_FLAG

        if (result & 0xFF) == 0:
            self.registers["F"] |= ZERO_FLAG
        else:
            self.registers["F"] &= ~ZERO_FLAG

        if result & 0x100 != 0:
            self.registers["F"] |= CARRY_FLAG
        else:
            self.registers["F"] &= ~CARRY_FLAG

        if (self.registers["A"] & 0xF) + (value & 0xF) > 0xF:
            self.registers["F"] |= HALF_CARRY_FLAG
        else:
            self.registers["F"] &= ~HALF_CARRY_FLAG

        self.registers["A"] = result & 0xFF

    def _add_a_imm8(self):
        value = self._get_imm8()
        result = value + self.registers["A"]

        self.registers["F"] &= ~SUB_FLAG

        if (result & 0xFF) == 0:
            self.registers["F"] |= ZERO_FLAG
        else:
            self.registers["F"] &= ~ZERO_FLAG

        if result & 0x100 != 0:
            self.registers["F"] |= CARRY_FLAG
        else:
            self.registers["F"] &= ~CARRY_FLAG

        if (self.registers["A"] & 0xF) + (value & 0xF) > 0xF:
            self.registers["F"] |= HALF_CARRY_FLAG
        else:
            self.registers["F"] &= ~HALF_CARRY_FLAG

        self.registers["A"] = result & 0xFF

    def _add_sp_imm8(self):
        value = sign_convert(self._get_imm8())
        result = value + self.sp

        self.registers["F"] &= ~SUB_FLAG
        self.registers["F"] &= ~ZERO_FLAG

        if ((self.sp ^ value ^ (result & 0xFFFF)) & 0x100) == 0x100:
            self.registers["F"] |= CARRY_FLAG
        else:
            self.registers["F"] &= ~CARRY_FLAG

        if ((self.sp ^ value ^ (result & 0xFFFF)) & 0x10) == 0x10:
            self.registers["F"] |= HALF_CARRY_FLAG
        else:
            self.registers["F"] &= ~HALF_CARRY_FLAG

        self.sp = result & 0xFFFF

    def _add_a_hl(self):
        value = self.memory.read_byte(self._get_reg16("H", "L"))
        result = value + self.registers["A"]

        self.registers["F"] &= ~SUB_FLAG

        if (result & 0xFF) == 0:
            self.registers["F"] |= ZERO_FLAG
        else:
            self.registers["F"] &= ~ZERO_FLAG

        if result & 0x100 != 0:
            self.registers["F"] |= CARRY_FLAG
        else:
            self.registers["F"] &= ~CARRY_FLAG

        if (self.registers["A"] & 0xF) + (value & 0xF) > 0xF:
            self.registers["F"] |= HALF_CARRY_FLAG
        else:
            self.registers["F"] &= ~HALF_CARRY_FLAG

        self.registers["A"] = result & 0xFF

    def _adc_a_reg(self, reg: str):
        value = self.registers[reg]
        carry = (self.registers["F"] & CARRY_FLAG) >> 4
        result = value + self.registers["A"] + carry

        self.registers["F"] &= ~SUB_FLAG

        if (result & 0xFF) == 0:
            self.registers["F"] |= ZERO_FLAG
        else:
            self.registers["F"] &= ~ZERO_FLAG

        if result & 0x100 != 0:
            self.registers["F"] |= CARRY_FLAG
        else:
            self.registers["F"] &= ~CARRY_FLAG

        if (self.registers["A"] & 0xF) + (value & 0xF) + carry > 0xF:
            self.registers["F"] |= HALF_CARRY_FLAG
        else:
            self.registers["F"] &= ~HALF_CARRY_FLAG

        self.registers["A"] = result & 0xFF

    def _adc_a_imm8(self):
        value = self._get_imm8()
        carry = (self.registers["F"] & CARRY_FLAG) >> 4
        result = value + self.registers["A"] + carry

        self.registers["F"] &= ~SUB_FLAG

        if (result & 0xFF) == 0:
            self.registers["F"] |= ZERO_FLAG
        else:
            self.registers["F"] &= ~ZERO_FLAG

        if result & 0x100 != 0:
            self.registers["F"] |= CARRY_FLAG
        else:
            self.registers["F"] &= ~CARRY_FLAG

        if (self.registers["A"] & 0xF) + (value & 0xF) + carry > 0xF:
            self.registers["F"] |= HALF_CARRY_FLAG
        else:
            self.registers["F"] &= ~HALF_CARRY_FLAG

        self.registers["A"] = result & 0xFF

    def _adc_a_hl(self):
        value = self.memory.read_byte(self._get_reg16("H", "L"))
        carry = (self.registers["F"] & CARRY_FLAG) >> 4
        result = value + self.registers["A"] + carry

        self.registers["F"] &= ~SUB_FLAG

        if (result & 0xFF) == 0:
            self.registers["F"] |= ZERO_FLAG
        else:
            self.registers["F"] &= ~ZERO_FLAG

        if result & 0x100 != 0:
            self.registers["F"] |= CARRY_FLAG
        else:
            self.registers["F"] &= ~CARRY_FLAG

        if (self.registers["A"] & 0xF) + (value & 0xF) + carry > 0xF:
            self.registers["F"] |= HALF_CARRY_FLAG
        else:
            self.registers["F"] &= ~HALF_CARRY_FLAG

        self.registers["A"] = result & 0xFF

    def _sub_a_reg(self, reg: str):
        value = self.registers[reg]
        result = (self.registers["A"] - value) & 0xFF

        self.registers["F"] |= SUB_FLAG

        if result == 0:
            self.registers["F"] |= ZERO_FLAG
        else:
            self.registers["F"] &= ~ZERO_FLAG

        if self.registers["A"] < value:
            self.registers["F"] |= CARRY_FLAG
        else:
            self.registers["F"] &= ~CARRY_FLAG

        if (self.registers["A"] & 0xF) - (value & 0xF) < 0:
            self.registers["F"] |= HALF_CARRY_FLAG
        else:
            self.registers["F"] &= ~HALF_CARRY_FLAG

        self.registers["A"] = result

    def _sub_a_imm8(self):
        value = self._get_imm8()
        result = (self.registers["A"] - value) & 0xFF

        self.registers["F"] |= SUB_FLAG

        if result == 0:
            self.registers["F"] |= ZERO_FLAG
        else:
            self.registers["F"] &= ~ZERO_FLAG

        if self.registers["A"] < value:
            self.registers["F"] |= CARRY_FLAG
        else:
            self.registers["F"] &= ~CARRY_FLAG

        if (self.registers["A"] & 0xF) - (value & 0xF) < 0:
            self.registers["F"] |= HALF_CARRY_FLAG
        else:
            self.registers["F"] &= ~HALF_CARRY_FLAG

        self.registers["A"] = result

    def _sub_a_hl(self):
        value = self.memory.read_byte(self._get_reg16("H", "L"))
        result = (self.registers["A"] - value) & 0xFF

        self.registers["F"] |= SUB_FLAG

        if result == 0:
            self.registers["F"] |= ZERO_FLAG
        else:
            self.registers["F"] &= ~ZERO_FLAG

        if self.registers["A"] < value:
            self.registers["F"] |= CARRY_FLAG
        else:
            self.registers["F"] &= ~CARRY_FLAG

        if (self.registers["A"] & 0xF) - (value & 0xF) < 0:
            self.registers["F"] |= HALF_CARRY_FLAG
        else:
            self.registers["F"] &= ~HALF_CARRY_FLAG

        self.registers["A"] = result

    def _sbc_a_reg(self, reg: str):
        value = self.registers[reg]
        carry = (self.registers["F"] & CARRY_FLAG) >> 4
        result = self.registers["A"] - value - carry

        self.registers["F"] |= SUB_FLAG

        if (result & 0xFF) == 0:
            self.registers["F"] |= ZERO_FLAG
        else:
            self.registers["F"] &= ~ZERO_FLAG

        if result < 0:
            self.registers["F"] |= CARRY_FLAG
        else:
            self.registers["F"] &= ~CARRY_FLAG

        if (self.registers["A"] & 0xF) - (value & 0xF) - carry < 0:
            self.registers["F"] |= HALF_CARRY_FLAG
        else:
            self.registers["F"] &= ~HALF_CARRY_FLAG

        self.registers["A"] = result & 0xFF

    def _sbc_a_imm8(self):
        value = self._get_imm8()
        carry = (self.registers["F"] & CARRY_FLAG) >> 4
        result = self.registers["A"] - value - carry

        self.registers["F"] |= SUB_FLAG

        if (result & 0xFF) == 0:
            self.registers["F"] |= ZERO_FLAG
        else:
            self.registers["F"] &= ~ZERO_FLAG

        if result < 0:
            self.registers["F"] |= CARRY_FLAG
        else:
            self.registers["F"] &= ~CARRY_FLAG

        if (self.registers["A"] & 0xF) - (value & 0xF) - carry < 0:
            self.registers["F"] |= HALF_CARRY_FLAG
        else:
            self.registers["F"] &= ~HALF_CARRY_FLAG

        self.registers["A"] = result & 0xFF

    def _sbc_a_hl(self):
        value = self.memory.read_byte(self._get_reg16("H", "L"))
        carry = (self.registers["F"] & CARRY_FLAG) >> 4
        result = self.registers["A"] - value - carry

        self.registers["F"] |= SUB_FLAG

        if (result & 0xFF) == 0:
            self.registers["F"] |= ZERO_FLAG
        else:
            self.registers["F"] &= ~ZERO_FLAG

        if result < 0:
            self.registers["F"] |= CARRY_FLAG
        else:
            self.registers["F"] &= ~CARRY_FLAG

        if (self.registers["A"] & 0xF) - (value & 0xF) - carry < 0:
            self.registers["F"] |= HALF_CARRY_FLAG
        else:
            self.registers["F"] &= ~HALF_CARRY_FLAG

        self.registers["A"] = result & 0xFF

    def _and_a_reg(self, src: str):
        self.registers["A"] &= self.registers[src]

        if self.registers["A"] == 0:
            self.registers["F"] |= ZERO_FLAG
        else:
            self.registers["F"] &= ~ZERO_FLAG

        self.registers["F"] |= HALF_CARRY_FLAG
        self.registers["F"] &= ~SUB_FLAG
        self.registers["F"] &= ~CARRY_FLAG

    def _and_a_imm8(self):
        self.registers["A"] &= self._get_imm8()

        if self.registers["A"] == 0:
            self.registers["F"] |= ZERO_FLAG
        else:
            self.registers["F"] &= ~ZERO_FLAG

        self.registers["F"] |= HALF_CARRY_FLAG
        self.registers["F"] &= ~SUB_FLAG
        self.registers["F"] &= ~CARRY_FLAG

    def _and_a_hl(self):
        self.registers["A"] &= self.memory.read_byte(self._get_reg16("H", "L"))

        if self.registers["A"] == 0:
            self.registers["F"] |= ZERO_FLAG
        else:
            self.registers["F"] &= ~ZERO_FLAG

        self.registers["F"] |= HALF_CARRY_FLAG
        self.registers["F"] &= ~SUB_FLAG
        self.registers["F"] &= ~CARRY_FLAG

    def _xor_a_reg(self, src: str):
        self.registers["A"] ^= self.registers[src]

        if self.registers["A"] == 0:
            self.registers["F"] |= ZERO_FLAG
        else:
            self.registers["F"] &= ~ZERO_FLAG

        self.registers["F"] &= ~HALF_CARRY_FLAG
        self.registers["F"] &= ~SUB_FLAG
        self.registers["F"] &= ~CARRY_FLAG

    def _xor_a_imm8(self):
        self.registers["A"] ^= self._get_imm8()

        if self.registers["A"] == 0:
            self.registers["F"] |= ZERO_FLAG
        else:
            self.registers["F"] &= ~ZERO_FLAG

        self.registers["F"] &= ~HALF_CARRY_FLAG
        self.registers["F"] &= ~SUB_FLAG
        self.registers["F"] &= ~CARRY_FLAG

    def _xor_a_hl(self):
        self.registers["A"] ^= self.memory.read_byte(self._get_reg16("H", "L"))

        if self.registers["A"] == 0:
            self.registers["F"] |= ZERO_FLAG
        else:
            self.registers["F"] &= ~ZERO_FLAG

        self.registers["F"] &= ~HALF_CARRY_FLAG
        self.registers["F"] &= ~SUB_FLAG
        self.registers["F"] &= ~CARRY_FLAG

    def _or_a_reg(self, src: str):
        self.registers["A"] |= self.registers[src]

        if self.registers["A"] == 0:
            self.registers["F"] |= ZERO_FLAG
        else:
            self.registers["F"] &= ~ZERO_FLAG

        self.registers["F"] &= ~HALF_CARRY_FLAG
        self.registers["F"] &= ~SUB_FLAG
        self.registers["F"] &= ~CARRY_FLAG

    def _or_a_imm8(self):
        self.registers["A"] |= self._get_imm8()

        if self.registers["A"] == 0:
            self.registers["F"] |= ZERO_FLAG
        else:
            self.registers["F"] &= ~ZERO_FLAG

        self.registers["F"] &= ~HALF_CARRY_FLAG
        self.registers["F"] &= ~SUB_FLAG
        self.registers["F"] &= ~CARRY_FLAG

    def _or_a_hl(self):
        self.registers["A"] |= self.memory.read_byte(self._get_reg16("H", "L"))

        if self.registers["A"] == 0:
            self.registers["F"] |= ZERO_FLAG
        else:
            self.registers["F"] &= ~ZERO_FLAG

        self.registers["F"] &= ~HALF_CARRY_FLAG
        self.registers["F"] &= ~SUB_FLAG
        self.registers["F"] &= ~CARRY_FLAG

    def _cp_a_reg(self, src: str):
        value = self.registers[src]
        result = self.registers["A"] - value

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

    def _cp_a_imm8(self):
        value = self._get_imm8()
        result = self.registers["A"] - value

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

    def _cp_a_hl(self):
        value = self.memory.read_byte(self._get_reg16("H", "L"))
        result = self.registers["A"] - value

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

    def _ret_cond(self, cond):
        if cond:
            addr = self.memory.read_word(self.sp)
            self.sp = (self.sp + 2) & 0xFFFF
            self.pc = addr

    def _ret(self):
        addr = self.memory.read_word(self.sp)
        self.sp = (self.sp + 2) & 0xFFFF
        self.pc = addr

    def _reti(self):
        self._ret()
        self.interrupts_enabled = True

    def _jp_cond_imm16(self, cond):
        addr = self._get_imm16()
        if cond:
            self.pc = addr

    def _call_cond_imm16(self, cond):
        addr = self._get_imm16()
        if cond:
            self.sp = (self.sp - 2) & 0xFFFF
            self.memory.write_word(self.sp, self.pc)
            self.pc = addr

    def _call_imm16(self):
        addr = self._get_imm16()
        self.sp = (self.sp - 2) & 0xFFFF
        self.memory.write_word(self.sp, self.pc)
        self.pc = addr

    def _rst(self, target: int):
        self.sp = (self.sp - 2) & 0xFFFF
        self.memory.write_word(self.sp, self.pc)
        self.pc = target

    def _pop(self, reg_high: str, reg_low: str):
        data = self.memory.read_word(self.sp)
        self.sp = (self.sp + 2) & 0xFFFF
        self._set_reg16(reg_high, reg_low, data)

    def _push(self, reg_high: str, reg_low: str):
        self.sp = (self.sp - 2) & 0xFFFF
        self.memory.write_word(self.sp, self._get_reg16(reg_high, reg_low))

    def _ld_hl_sp_imm8(self):
        value = sign_convert(self._get_imm8())
        result = value + self.sp

        self.registers["F"] &= ~SUB_FLAG
        self.registers["F"] &= ~ZERO_FLAG

        if ((self.sp ^ value ^ (result & 0xFFFF)) & 0x100) == 0x100:
            self.registers["F"] |= CARRY_FLAG
        else:
            self.registers["F"] &= ~CARRY_FLAG

        if ((self.sp ^ value ^ (result & 0xFFFF)) & 0x10) == 0x10:
            self.registers["F"] |= HALF_CARRY_FLAG
        else:
            self.registers["F"] &= ~HALF_CARRY_FLAG

        self._set_reg16("H", "L", result & 0xFFFF)

    def _ld_reg8_reg8(self, dest: str, src: str):
        self.registers[dest] = self.registers[src]

    def _ld_reg8_hl(self, dest: str):
        self.registers[dest] = self.memory.read_byte(self._get_reg16("H", "L"))

    def _ld_hl_reg8(self, src: str):
        self.memory.write_byte(self._get_reg16("H", "L"), self.registers[src])

    def step(self):
        opcode = self.memory.read_byte(self.pc)
        self.pc += 1

        match opcode:
            case 0x0:
                return  # nop
            case 0x1:
                self._ld_reg16_imm16("B", "C")  # ld BC, imm16
            case 0x11:
                self._ld_reg16_imm16("D", "E")  # ld DE, imm16
            case 0x21:
                self._ld_reg16_imm16("H", "L")  # ld HL, imm16
            case 0x31:
                self.sp = self._get_imm16()  # ld SP, imm16
            case 0x2:
                self._ld_memreg16_reg8("B", "C", "A")  # ld [BC], a
            case 0x12:
                self._ld_memreg16_reg8("D", "E", "A")  # ld [DE], a
            case 0x22:
                self._ld_hli_reg8("A")  # ld [HL+], a
            case 0x32:
                self._ld_hld_reg8("A")  # ld [HL-], a
            case 0xA:
                self._ld_reg8_memreg16("A", "B", "C")  # ld a, [BC]
            case 0x1A:
                self._ld_reg8_memreg16("A", "D", "E")  # ld a, [DE]
            case 0x2A:
                self._ld_reg8_hli("A")  # ld a, [HL+]
            case 0x3A:
                self._ld_reg8_hld("A")  # ld a, [HL-]
            case 0x8:
                self.memory.write_word(self._get_imm16(), self.sp)  # ld [imm16], sp
            case 0x3:
                self._inc_reg16("B", "C")  # inc BC
            case 0x13:
                self._inc_reg16("D", "E")  # inc DE
            case 0x23:
                self._inc_reg16("H", "L")  # inc HL
            case 0x33:
                self.sp = (self.sp + 1) & 0xFFFF  # inc SP
            case 0xB:
                self._dec_reg16("B", "C")  # dec BC
            case 0x1B:
                self._dec_reg16("D", "E")  # dec DE
            case 0x2B:
                self._dec_reg16("H", "L")  # dec HL
            case 0x3B:
                self.sp = (self.sp - 1) & 0xFFFF  # dec SP
            case 0x9:
                self._add_hl_reg16("B", "C")  # add hl, BC
            case 0x19:
                self._add_hl_reg16("D", "E")  # add hl, DE
            case 0x29:
                self._add_hl_reg16("H", "L")  # add hl, HL
            case 0x39:
                self._add_hl_sp()  # add hl, SP
            case 0x4:
                self._inc_reg("B")  # inc B
            case 0xC:
                self._inc_reg("C")  # inc C
            case 0x14:
                self._inc_reg("D")  # inc D
            case 0x1C:
                self._inc_reg("E")  # inc E
            case 0x24:
                self._inc_reg("H")  # inc H
            case 0x2C:
                self._inc_reg("L")  # inc L
            case 0x34:
                self._inc_hl()  # inc [HL]
            case 0x3C:
                self._inc_reg("A")  # inc A
            case 0x5:
                self._dec_reg("B")  # dec B
            case 0xD:
                self._dec_reg("C")  # dec C
            case 0x15:
                self._dec_reg("D")  # dec D
            case 0x1D:
                self._dec_reg("E")  # dec E
            case 0x25:
                self._dec_reg("H")  # dec H
            case 0x2D:
                self._dec_reg("L")  # dec L
            case 0x35:
                self._dec_hl()  # dec [HL]
            case 0x3D:
                self._dec_reg("A")  # dec A
            case 0x6:
                self._ld_reg_imm8("B")  # ld B, imm8
            case 0xE:
                self._ld_reg_imm8("C")  # ld C, imm8
            case 0x16:
                self._ld_reg_imm8("D")  # ld D, imm8
            case 0x1E:
                self._ld_reg_imm8("E")  # ld E, imm8
            case 0x26:
                self._ld_reg_imm8("H")  # ld H, imm8
            case 0x2E:
                self._ld_reg_imm8("L")  # ld L, imm8
            case 0x36:
                self._ld_hl_imm8()  # ld [HL], imm8
            case 0x3E:
                self._ld_reg_imm8("A")  # ld A, imm8
            case 0x7:
                self._rlca()  # rlca
            case 0xF:
                self._rrca()  # rrca
            case 0x17:
                self._rla()  # rla
            case 0x1F:
                self._rra()  # rra
            case 0x27:
                raise Exception("TODO: Implement DAA")  # daa
            case 0x2F:
                self._cpl()  # cpl
            case 0x37:
                self._scf()  # scf
            case 0x3F:
                self._ccf()  # ccf
            case 0x18:
                self._jr_imm8()  # jr imm8
            case 0x20:
                self._jr_cond_imm8(self.registers["F"] & ZERO_FLAG == 0)  # jr NZ, imm8
            case 0x28:
                self._jr_cond_imm8(self.registers["F"] & ZERO_FLAG)  # jr Z, imm8
            case 0x30:
                self._jr_cond_imm8(self.registers["F"] & CARRY_FLAG == 0)  # jr NC, imm8
            case 0x38:
                self._jr_cond_imm8(self.registers["F"] & CARRY_FLAG)  # jr C, imm8
            case 0x10:
                raise Exception("TODO: Implement stop")  # stop
            case 0x76:
                raise Exception("TODO: Implement halt")  # halt
            case 0x80:
                self._add_a_reg("B")  # add a, B
            case 0x81:
                self._add_a_reg("C")  # add a, C
            case 0x82:
                self._add_a_reg("D")  # add a, D
            case 0x83:
                self._add_a_reg("E")  # add a, E
            case 0x84:
                self._add_a_reg("H")  # add a, H
            case 0x85:
                self._add_a_reg("L")  # add a, L
            case 0x86:
                self._add_a_hl()  # add a, [HL]
            case 0x87:
                self._add_a_reg("A")  # add a, A
            case 0x88:
                self._adc_a_reg("B")  # adc a, B
            case 0x89:
                self._adc_a_reg("C")  # adc a, C
            case 0x8A:
                self._adc_a_reg("D")  # adc a, D
            case 0x8B:
                self._adc_a_reg("E")  # adc a, E
            case 0x8C:
                self._adc_a_reg("H")  # adc a, H
            case 0x8D:
                self._adc_a_reg("L")  # adc a, L
            case 0x8E:
                self._adc_a_hl()  # adc a, [HL]
            case 0x8F:
                self._adc_a_reg("A")  # adc a, A
            case 0x90:
                self._sub_a_reg("B")  # sub a, B
            case 0x91:
                self._sub_a_reg("C")  # sub a, C
            case 0x92:
                self._sub_a_reg("D")  # sub a, D
            case 0x93:
                self._sub_a_reg("E")  # sub a, E
            case 0x94:
                self._sub_a_reg("H")  # sub a, H
            case 0x95:
                self._sub_a_reg("L")  # sub a, L
            case 0x96:
                self._sub_a_hl()  # sub a, [HL]
            case 0x97:
                self._sub_a_reg("A")  # sub a, A
            case 0x98:
                self._sbc_a_reg("B")  # sbc a, B
            case 0x99:
                self._sbc_a_reg("C")  # sbc a, C
            case 0x9A:
                self._sbc_a_reg("D")  # sbc a, D
            case 0x9B:
                self._sbc_a_reg("E")  # sbc a, E
            case 0x9C:
                self._sbc_a_reg("H")  # sbc a, H
            case 0x9D:
                self._sbc_a_reg("L")  # sbc a, L
            case 0x9E:
                self._sbc_a_hl()  # sbc a, [HL]
            case 0x9F:
                self._sbc_a_reg("A")  # sbc a, A
            case 0xA0:
                self._and_a_reg("B")  # and a, B
            case 0xA1:
                self._and_a_reg("C")  # and a, C
            case 0xA2:
                self._and_a_reg("D")  # and a, D
            case 0xA3:
                self._and_a_reg("E")  # and a, E
            case 0xA4:
                self._and_a_reg("H")  # and a, H
            case 0xA5:
                self._and_a_reg("L")  # and a, L
            case 0xA6:
                self._and_a_hl()  # and a, [HL]
            case 0xA7:
                self._and_a_reg("A")  # and a, A
            case 0xA8:
                self._xor_a_reg("B")  # xor a, B
            case 0xA9:
                self._xor_a_reg("C")  # xor a, C
            case 0xAA:
                self._xor_a_reg("D")  # xor a, D
            case 0xAB:
                self._xor_a_reg("E")  # xor a, E
            case 0xAC:
                self._xor_a_reg("H")  # xor a, H
            case 0xAD:
                self._xor_a_reg("L")  # xor a, L
            case 0xAE:
                self._xor_a_hl()  # xor a, [HL]
            case 0xAF:
                self._xor_a_reg("A")  # xor a, A
            case 0xB0:
                self._or_a_reg("B")  # or a, B
            case 0xB1:
                self._or_a_reg("C")  # or a, C
            case 0xB2:
                self._or_a_reg("D")  # or a, D
            case 0xB3:
                self._or_a_reg("E")  # or a, E
            case 0xB4:
                self._or_a_reg("H")  # or a, H
            case 0xB5:
                self._or_a_reg("L")  # or a, L
            case 0xB6:
                self._or_a_hl()  # or a, [HL]
            case 0xB7:
                self._or_a_reg("A")  # or a, A
            case 0xB8:
                self._cp_a_reg("B")  # cp a, B
            case 0xB9:
                self._cp_a_reg("C")  # cp a, C
            case 0xBA:
                self._cp_a_reg("D")  # cp a, D
            case 0xBB:
                self._cp_a_reg("E")  # cp a, E
            case 0xBC:
                self._cp_a_reg("H")  # cp a, H
            case 0xBD:
                self._cp_a_reg("L")  # cp a, L
            case 0xBE:
                self._cp_a_hl()  # cp a, [HL]
            case 0xBF:
                self._cp_a_reg("A")  # cp a, A
            case 0xC6:
                self._add_a_imm8()  # add a, imm8
            case 0xCE:
                self._adc_a_imm8()  # adc a, imm8
            case 0xD6:
                self._sub_a_imm8()  # sub a, imm8
            case 0xDE:
                self._sbc_a_imm8()  # sbc a, imm8
            case 0xE6:
                self._and_a_imm8()  # and a, imm8
            case 0xEE:
                self._xor_a_imm8()  # xor a, imm8
            case 0xF6:
                self._or_a_imm8()  # or a, imm8
            case 0xFE:
                self._cp_a_imm8()  # cp a, imm8
            case 0xC0:
                self._ret_cond(self.registers["F"] & ZERO_FLAG == 0)  # ret NZ
            case 0xC8:
                self._ret_cond(self.registers["F"] & ZERO_FLAG)  # ret Z
            case 0xD0:
                self._ret_cond(self.registers["F"] & CARRY_FLAG == 0)  # ret NC
            case 0xD8:
                self._ret_cond(self.registers["F"] & CARRY_FLAG)  # ret C
            case 0xC9:
                self._ret()  # ret
            case 0xD9:
                self._reti()  # reti
            case 0xC2:
                self._jp_cond_imm16(
                    self.registers["F"] & ZERO_FLAG == 0
                )  # jp NZ, imm16
            case 0xCA:
                self._jp_cond_imm16(self.registers["F"] & ZERO_FLAG)  # jp Z, imm16
            case 0xD2:
                self._jp_cond_imm16(
                    self.registers["F"] & CARRY_FLAG == 0
                )  # jp NC, imm16
            case 0xDA:
                self._jp_cond_imm16(self.registers["F"] & CARRY_FLAG)  # jp C, imm16
            case 0xC3:
                self.pc = self._get_imm16()  # jp imm16
            case 0xE9:
                self.pc = self._get_reg16("H", "L")  # jp hl
            case 0xC4:
                self._call_cond_imm16(
                    self.registers["F"] & ZERO_FLAG == 0
                )  # call NZ, imm16
            case 0xCC:
                self._call_cond_imm16(self.registers["F"] & ZERO_FLAG)  # call Z, imm16
            case 0xD4:
                self._call_cond_imm16(
                    self.registers["F"] & CARRY_FLAG == 0
                )  # call NC, imm16
            case 0xDC:
                self._call_cond_imm16(self.registers["F"] & CARRY_FLAG)  # call C, imm16
            case 0xCD:
                self._call_imm16()  # call imm16
            case 0xC7:
                self._rst(0)  # rst 0
            case 0xCF:
                self._rst(8)  # rst 1
            case 0xD7:
                self._rst(16)  # rst 2
            case 0xDF:
                self._rst(24)  # rst 3
            case 0xE7:
                self._rst(32)  # rst 4
            case 0xEF:
                self._rst(40)  # rst 5
            case 0xF7:
                self._rst(48)  # rst 6
            case 0xFF:
                self._rst(56)  # rst 7
            case 0xC1:
                self._pop("B", "C")  # pop BC
            case 0xD1:
                self._pop("D", "E")  # pop DE
            case 0xE1:
                self._pop("H", "L")  # pop HL
            case 0xF1:
                self._pop("A", "F")  # pop AF
            case 0xC5:
                self._push("B", "C")  # push BC
            case 0xD5:
                self._push("D", "E")  # push DE
            case 0xE5:
                self._push("H", "L")  # push HL
            case 0xF5:
                self._push("A", "F")  # push AF
            case 0xE2:
                self.memory.write_byte(
                    0xFF00 | self.registers["C"], self.registers["A"]
                )  # ldh [c], a
            case 0xE0:
                self.memory.write_byte(
                    0xFF00 | self._get_imm8(), self.registers["A"]
                )  # ldh [imm8], a
            case 0xEA:
                self.memory.write_byte(
                    self._get_imm16(), self.registers["A"]
                )  # ld [imm16], a
            case 0xF2:
                self.registers["A"] = self.memory.read_byte(
                    0xFF00 | self.registers["C"]
                )  # ldh a, [c]
            case 0xF0:
                self.registers["A"] = self.memory.read_byte(
                    0xFF00 | self._get_imm8()
                )  # ldh a, [imm8]
            case 0xFA:
                self.registers["A"] = self.memory.read_byte(
                    self._get_imm16()
                )  # ld a, [imm16]
            case 0xE8:
                self._add_sp_imm8()  # add sp, imm8
            case 0xF8:
                self._ld_hl_sp_imm8()  # ld hl, sp + imm8
            case 0xF9:
                self.sp = self._get_reg16("H", "L")  # ld sp, hl
            case 0xF3:
                self.interrupts_enabled = False  # di
            case 0xFB:
                self.interrupts_enabled = True  # ei
            case 0x40:
                self._ld_reg8_reg8("B", "B")  # LD B, B
            case 0x41:
                self._ld_reg8_reg8("B", "C")  # LD B, C
            case 0x42:
                self._ld_reg8_reg8("B", "D")  # LD B, D
            case 0x43:
                self._ld_reg8_reg8("B", "E")  # LD B, E
            case 0x44:
                self._ld_reg8_reg8("B", "H")  # LD B, H
            case 0x45:
                self._ld_reg8_reg8("B", "L")  # LD B, L
            case 0x46:
                self._ld_reg8_hl("B")  # LD B, [HL]
            case 0x47:
                self._ld_reg8_reg8("B", "A")  # LD B, A
            case 0x48:
                self._ld_reg8_reg8("C", "B")  # LD C, B
            case 0x49:
                self._ld_reg8_reg8("C", "C")  # LD C, C
            case 0x4A:
                self._ld_reg8_reg8("C", "D")  # LD C, D
            case 0x4B:
                self._ld_reg8_reg8("C", "E")  # LD C, E
            case 0x4C:
                self._ld_reg8_reg8("C", "H")  # LD C, H
            case 0x4D:
                self._ld_reg8_reg8("C", "L")  # LD C, L
            case 0x4E:
                self._ld_reg8_hl("C")  # LD C, [HL]
            case 0x4F:
                self._ld_reg8_reg8("C", "A")  # LD C, A
            case 0x50:
                self._ld_reg8_reg8("D", "B")  # LD D, B
            case 0x51:
                self._ld_reg8_reg8("D", "C")  # LD D, C
            case 0x52:
                self._ld_reg8_reg8("D", "D")  # LD D, D
            case 0x53:
                self._ld_reg8_reg8("D", "E")  # LD D, E
            case 0x54:
                self._ld_reg8_reg8("D", "H")  # LD D, H
            case 0x55:
                self._ld_reg8_reg8("D", "L")  # LD D, L
            case 0x56:
                self._ld_reg8_hl("D")  # LD D, [HL]
            case 0x57:
                self._ld_reg8_reg8("D", "A")  # LD D, A
            case 0x58:
                self._ld_reg8_reg8("E", "B")  # LD E, B
            case 0x59:
                self._ld_reg8_reg8("E", "C")  # LD E, C
            case 0x5A:
                self._ld_reg8_reg8("E", "D")  # LD E, D
            case 0x5B:
                self._ld_reg8_reg8("E", "E")  # LD E, E
            case 0x5C:
                self._ld_reg8_reg8("E", "H")  # LD E, H
            case 0x5D:
                self._ld_reg8_reg8("E", "L")  # LD E, L
            case 0x5E:
                self._ld_reg8_hl("E")  # LD E, [HL]
            case 0x5F:
                self._ld_reg8_reg8("E", "A")  # LD E, A
            case 0x60:
                self._ld_reg8_reg8("H", "B")  # LD H, B
            case 0x61:
                self._ld_reg8_reg8("H", "C")  # LD H, C
            case 0x62:
                self._ld_reg8_reg8("H", "D")  # LD H, D
            case 0x63:
                self._ld_reg8_reg8("H", "E")  # LD H, E
            case 0x64:
                self._ld_reg8_reg8("H", "H")  # LD H, H
            case 0x65:
                self._ld_reg8_reg8("H", "L")  # LD H, L
            case 0x66:
                self._ld_reg8_hl("H")  # LD H, [HL]
            case 0x67:
                self._ld_reg8_reg8("H", "A")  # LD H, A
            case 0x68:
                self._ld_reg8_reg8("L", "B")  # LD L, B
            case 0x69:
                self._ld_reg8_reg8("L", "C")  # LD L, C
            case 0x6A:
                self._ld_reg8_reg8("L", "D")  # LD L, D
            case 0x6B:
                self._ld_reg8_reg8("L", "E")  # LD L, E
            case 0x6C:
                self._ld_reg8_reg8("L", "H")  # LD L, H
            case 0x6D:
                self._ld_reg8_reg8("L", "L")  # LD L, L
            case 0x6E:
                self._ld_reg8_hl("L")  # LD L, [HL]
            case 0x6F:
                self._ld_reg8_reg8("L", "A")  # LD L, A
            case 0x70:
                self._ld_hl_reg8("B")  # LD [HL], B
            case 0x71:
                self._ld_hl_reg8("C")  # LD [HL], C
            case 0x72:
                self._ld_hl_reg8("D")  # LD [HL], D
            case 0x73:
                self._ld_hl_reg8("E")  # LD [HL], E
            case 0x74:
                self._ld_hl_reg8("H")  # LD [HL], H
            case 0x75:
                self._ld_hl_reg8("L")  # LD [HL], L
            case 0x77:
                self._ld_hl_reg8("A")  # LD [HL], A
            case 0x78:
                self._ld_reg8_reg8("A", "B")  # LD A, B
            case 0x79:
                self._ld_reg8_reg8("A", "C")  # LD A, C
            case 0x7A:
                self._ld_reg8_reg8("A", "D")  # LD A, D
            case 0x7B:
                self._ld_reg8_reg8("A", "E")  # LD A, E
            case 0x7C:
                self._ld_reg8_reg8("A", "H")  # LD A, H
            case 0x7D:
                self._ld_reg8_reg8("A", "L")  # LD A, L
            case 0x7E:
                self._ld_reg8_hl("A")  # LD A, [HL]
            case 0x7F:
                self._ld_reg8_reg8("A", "A")  # LD A, A
            case 0xCB:
                self.cb_step()
            case _:
                raise Exception(
                    f"Unknown instruction opcode: {"0"*(8-len(bin(opcode)[2:]))+bin(opcode)[2:]}"
                )

    def run(self):
        # placeholder, accurate timing will be stubbed in later
        while True:
            instr = self.memory.read_byte(self.pc)

            # if instr == 0b11110000 and self.memory.read_byte(self.pc + 1) == 0b01000100:
            #     # screen refresh byte according to disassembly
            #     self.memory.write_byte(0xFF44, 0x90)

            # print(
            #     hex(instr).upper()[2:], "0" * (8 - len(bin(instr)[2:])) + bin(instr)[2:]
            # )
            self.step()
            # print(self.registers, self.pc, self.sp)
            self.memory.write_byte(0xFF44, 0x00)
