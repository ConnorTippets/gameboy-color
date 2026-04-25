from .cpu import CPU
from .util import sign_convert

R8 = ["B", "C", "D", "E", "H", "L", "[HL]", "A"]
R16 = ["BC", "DE", "HL", "SP"]
R16STK = ["BC", "DE", "HL", "AF"]
R16MEM = ["BC", "DE", "HL+", "HL-"]
COND = ["NZ", "Z", "NC", "C"]

REGS = ["A", "B", "C", "D", "E", "H", "L"]
WORD_REGS = ["AF", "BC", "DE", "HL"]


class Debugger(CPU):
    def disasm(self) -> str:
        instr = self.memory.read_byte(self.pc)

        match instr:
            case 0x00:
                return "NOP"
            case 0x01 | 0x11 | 0x21 | 0x31:
                dest = R16[(instr & 0b00110000) >> 4]
                source = (
                    self.memory.read_byte(self.pc + 2) << 8
                ) | self.memory.read_byte(self.pc + 1)
                source_hex = hex(source).upper()[2:]

                return f"LD {dest}, 0x{source_hex}"
            case 0xA8 | 0xA9 | 0xAA | 0xAB | 0xAC | 0xAD | 0xAE | 0xAF:
                operand = R8[instr & 0b00000111]

                return f"XOR A, {operand}"
            case 0x02 | 0x12 | 0x22 | 0x32:
                dest = R16MEM[(instr & 0b00110000) >> 4]

                return f"LD [{dest}], A"
            case 0x20 | 0x28 | 0x30 | 0x38:
                cond = COND[(instr & 0b00011000) >> 3]
                addr = sign_convert(self.memory.read_byte(self.pc + 1))

                return f"JR {cond}, {addr}"
            case 0x06 | 0x0E | 0x16 | 0x1E | 0x26 | 0x2E | 0x36 | 0x3E:
                dest = R8[(instr & 0b00111000) >> 3]
                source = self.memory.read_byte(self.pc + 1)
                source_hex = hex(source).upper()[2:]

                return f"LD {dest}, 0x{source_hex}"
            case 0xE2:
                return "LD [0xFF00+C], A"
            case 0x04 | 0x0C | 0x14 | 0x1C | 0x24 | 0x2C | 0x34 | 0x3C:
                operand = R8[(instr & 0b00111000) >> 3]

                return f"INC {operand}"
            case 0x03 | 0x13 | 0x23 | 0x33:
                operand = R16[(instr & 0b00110000) >> 4]

                return f"INC {operand}"
            case 0x05 | 0x0D | 0x15 | 0x1D | 0x25 | 0x2D | 0x35 | 0x3D:
                operand = R8[(instr & 0b00111000) >> 3]

                return f"DEC {operand}"
            case 0x0B | 0x1B | 0x2B | 0x3B:
                operand = R16[(instr & 0b00110000) >> 4]

                return f"DEC {operand}"
            case 0x09 | 0x19 | 0x29 | 0x39:
                operand = R16[(instr & 0b00110000) >> 4]

                return f"ADD HL, {operand}"
            case (
                0x40
                | 0x41
                | 0x42
                | 0x43
                | 0x44
                | 0x45
                | 0x46
                | 0x47
                | 0x48
                | 0x49
                | 0x4A
                | 0x4B
                | 0x4C
                | 0x4D
                | 0x4E
                | 0x4F
                | 0x50
                | 0x51
                | 0x52
                | 0x53
                | 0x54
                | 0x55
                | 0x56
                | 0x57
                | 0x58
                | 0x59
                | 0x5A
                | 0x5B
                | 0x5C
                | 0x5D
                | 0x5E
                | 0x5F
                | 0x60
                | 0x61
                | 0x62
                | 0x63
                | 0x64
                | 0x65
                | 0x66
                | 0x67
                | 0x68
                | 0x69
                | 0x6A
                | 0x6B
                | 0x6C
                | 0x6D
                | 0x6E
                | 0x6F
                | 0x70
                | 0x71
                | 0x72
                | 0x73
                | 0x74
                | 0x75
                | 0x76
                | 0x77
                | 0x78
                | 0x79
                | 0x7A
                | 0x7B
                | 0x7C
                | 0x7D
                | 0x7E
                | 0x7F
            ):
                dest = R8[(instr & 0b00111000) >> 3]
                source = R8[instr & 0b00000111]

                return f"LD {dest}, {source}"
            case 0xE0:
                dest = self.memory.read_byte(self.pc + 1)
                dest_hex = hex(dest).upper()[2:]

                return f"LD [0xFF00+0x{dest_hex}], A"
            case 0x0A | 0x1A | 0x2A | 0x3A:
                source = R16MEM[(instr & 0b00110000) >> 4]

                return f"LD A, [{source}]"
            case 0xCD:
                addr = (
                    self.memory.read_byte(self.pc + 2) << 8
                ) | self.memory.read_byte(self.pc + 1)
                addr_hex = hex(addr).upper()[2:]

                return f"CALL 0x{addr_hex}"
            case 0xC5 | 0xD5 | 0xE5 | 0xF5:
                register = R16STK[(instr & 0b00110000) >> 4]

                return f"PUSH {register}"
            case 0xC1 | 0xD1 | 0xE1 | 0xF1:
                register = R16STK[(instr & 0b00110000) >> 4]

                return f"POP {register}"
            case 0b00000111:
                return "RLCA"
            case 0b00001111:
                return "RRCA"
            case 0b00010111:
                return "RLA"
            case 0b00011111:
                return "RRA"
            case 0b00100111:
                return "DAA"
            case 0b00101111:
                return "CPL"
            case 0b00110111:
                return "SCF"
            case 0b00111111:
                return "CCF"
            case 0xCB:
                instr = self.memory.read_byte(self.pc + 1)
                match instr:
                    case (
                        0x40
                        | 0x41
                        | 0x42
                        | 0x43
                        | 0x44
                        | 0x45
                        | 0x46
                        | 0x47
                        | 0x48
                        | 0x49
                        | 0x4A
                        | 0x4B
                        | 0x4C
                        | 0x4D
                        | 0x4E
                        | 0x4F
                        | 0x50
                        | 0x51
                        | 0x52
                        | 0x53
                        | 0x54
                        | 0x55
                        | 0x56
                        | 0x57
                        | 0x58
                        | 0x59
                        | 0x5A
                        | 0x5B
                        | 0x5C
                        | 0x5D
                        | 0x5E
                        | 0x5F
                        | 0x60
                        | 0x61
                        | 0x62
                        | 0x63
                        | 0x64
                        | 0x65
                        | 0x66
                        | 0x67
                        | 0x68
                        | 0x69
                        | 0x6A
                        | 0x6B
                        | 0x6C
                        | 0x6D
                        | 0x6E
                        | 0x6F
                        | 0x70
                        | 0x71
                        | 0x72
                        | 0x73
                        | 0x74
                        | 0x75
                        | 0x76
                        | 0x77
                        | 0x78
                        | 0x79
                        | 0x7A
                        | 0x7B
                        | 0x7C
                        | 0x7D
                        | 0x7E
                        | 0x7F
                    ):
                        bit = (instr & 0b00111000) >> 3
                        operand = R8[instr & 0b00000111]

                        return f"BIT {bit}, {operand}"
                    case (
                        0x80
                        | 0x81
                        | 0x82
                        | 0x83
                        | 0x84
                        | 0x85
                        | 0x86
                        | 0x87
                        | 0x88
                        | 0x89
                        | 0x8A
                        | 0x8B
                        | 0x8C
                        | 0x8D
                        | 0x8E
                        | 0x8F
                        | 0x90
                        | 0x91
                        | 0x92
                        | 0x93
                        | 0x94
                        | 0x95
                        | 0x96
                        | 0x97
                        | 0x98
                        | 0x99
                        | 0x9A
                        | 0x9B
                        | 0x9C
                        | 0x9D
                        | 0x9E
                        | 0x9F
                        | 0xA0
                        | 0xA1
                        | 0xA2
                        | 0xA3
                        | 0xA4
                        | 0xA5
                        | 0xA6
                        | 0xA7
                        | 0xA8
                        | 0xA9
                        | 0xAA
                        | 0xAB
                        | 0xAC
                        | 0xAD
                        | 0xAE
                        | 0xAF
                        | 0xB0
                        | 0xB1
                        | 0xB2
                        | 0xB3
                        | 0xB4
                        | 0xB5
                        | 0xB6
                        | 0xB7
                        | 0xB8
                        | 0xB9
                        | 0xBA
                        | 0xBB
                        | 0xBC
                        | 0xBD
                        | 0xBE
                        | 0xBF
                    ):
                        bit = (instr & 0b00111000) >> 3
                        operand = R8[instr & 0b00000111]

                        return f"RES {bit}, {operand}"
                    case (
                        0xC0
                        | 0xC1
                        | 0xC2
                        | 0xC3
                        | 0xC4
                        | 0xC5
                        | 0xC6
                        | 0xC7
                        | 0xC8
                        | 0xC9
                        | 0xCA
                        | 0xCB
                        | 0xCC
                        | 0xCD
                        | 0xCE
                        | 0xCF
                        | 0xD0
                        | 0xD1
                        | 0xD2
                        | 0xD3
                        | 0xD4
                        | 0xD5
                        | 0xD6
                        | 0xD7
                        | 0xD8
                        | 0xD9
                        | 0xDA
                        | 0xDB
                        | 0xDC
                        | 0xDD
                        | 0xDE
                        | 0xDF
                        | 0xE0
                        | 0xE1
                        | 0xE2
                        | 0xE3
                        | 0xE4
                        | 0xE5
                        | 0xE6
                        | 0xE7
                        | 0xE8
                        | 0xE9
                        | 0xEA
                        | 0xEB
                        | 0xEC
                        | 0xED
                        | 0xEE
                        | 0xEF
                        | 0xF0
                        | 0xF1
                        | 0xF2
                        | 0xF3
                        | 0xF4
                        | 0xF5
                        | 0xF6
                        | 0xF7
                        | 0xF8
                        | 0xF9
                        | 0xFA
                        | 0xFB
                        | 0xFC
                        | 0xFD
                        | 0xFE
                        | 0xFF
                    ):
                        bit = (instr & 0b00111000) >> 3
                        operand = R8[instr & 0b00000111]

                        return f"SET {bit}, {operand}"
                    case 0x00 | 0x01 | 0x02 | 0x03:
                        return f"RLC {R8[instr]}"
                    case 0x08 | 0x09 | 0x0A | 0x0B:
                        operand = R8[instr & 0b00000111]

                        return f"RLC {operand}"
                    case 0x10 | 0x11 | 0x12 | 0x13:
                        operand = R8[instr & 0b00000111]

                        return f"RL {operand}"
                    case 0x18 | 0x19 | 0x1A | 0x1B:
                        operand = R8[instr & 0b00000111]

                        return f"RR {operand}"
                    case 0x20 | 0x21 | 0x22 | 0x23:
                        operand = R8[instr & 0b0000111]

                        return f"SLA {operand}"
                    case 0x28 | 0x29 | 0x2A | 0x2B:
                        operand = R8[instr & 0b0000111]

                        return f"SRA {operand}"
                    case 0x30 | 0x31 | 0x32 | 0x33:
                        operand = R8[instr & 0b0000111]

                        return f"SWAP {operand}"
                    case 0x38 | 0x39 | 0x3A | 0x3B:
                        operand = R8[instr & 0b0000111]

                        return f"SRL {operand}"
                    case _:
                        hex_repr = hex(instr).upper()[2:]
                        bin_repr = bin(instr)[2:]
                        padded_bin_repr = "0" * (8 - len(bin_repr)) + bin_repr

                        return f"Unknown 0xCB instruction: 0x{hex_repr} (0b{padded_bin_repr})"
            case _:
                return "Unknown instruction!"

    def run(self):
        count = -1
        run_forever = False
        run_until_unknown = False
        while True:
            if run_until_unknown:
                disasm = self.disasm()
                if disasm.startswith("Unknown "):
                    run_until_unknown = False
                    continue

                self.step()
                continue

            if run_forever:
                pc = self.pc
                sp = self.sp
                regs = self.registers.copy()
                try:
                    print(self.disasm())
                    self.step()
                except Exception as e:
                    self.pc = pc
                    self.sp = sp
                    self.registers = regs
                    print(f"Error during execution of '{self.disasm()}': {str(e)}")
                    print("PC, SP, and registers have been restored")

                    run_forever = False
                    continue

                continue

            if count > 0:
                pc = self.pc
                sp = self.sp
                regs = self.registers.copy()
                try:
                    self.step()
                except Exception as e:
                    self.pc = pc
                    self.sp = sp
                    self.registers = regs
                    print(f"Error during execution of '{self.disasm()}': {str(e)}")
                    print("PC, SP, and registers have been restored")

                    count = -1
                    continue

                count -= 1
                continue
            else:
                count = -1

            cmd = input("gdb> ").strip()
            if cmd.upper() in REGS:
                hex_repr = hex(self.registers[cmd.upper()]).upper()[2:]
                bin_repr = bin(self.registers[cmd.upper()])[2:]
                padded_bin_repr = "0" * (8 - len(bin_repr)) + bin_repr

                print(f"{cmd.upper()}: 0x{hex_repr} (0b{padded_bin_repr})")
                continue

            if cmd.upper() in WORD_REGS:
                reg = (self.registers[cmd.upper()[0]] << 8) | self.registers[
                    cmd.upper()[1]
                ]
                hex_repr = hex(reg).upper()[2:]
                bin_repr = bin(reg)[2:]
                padded_bin_repr = "0" * (16 - len(bin_repr)) + bin_repr

                print(f"{cmd.upper()}: 0x{hex_repr} (0b{padded_bin_repr})")
                continue

            if cmd.lower().startswith("read byte "):
                operand = cmd.lower().replace("read byte ", "").strip()

                addr: int = 0
                if operand.upper() in WORD_REGS:
                    addr = (self.registers[operand.upper()[0]] << 8) | self.registers[
                        operand.upper()[1]
                    ]
                elif operand.upper() in REGS:
                    addr = self.registers[operand.upper()]
                else:
                    try:
                        addr = int(operand, 16)
                    except ValueError:
                        try:
                            addr = int(operand, 2)
                        except ValueError:
                            try:
                                addr = int(operand)
                            except ValueError:
                                print(f"Unknown address format: {operand}")
                                continue

                value = self.memory.read_byte(addr)
                hex_repr = hex(value).upper()[2:]
                bin_repr = bin(value)[2:]
                padded_bin_repr = "0" * (8 - len(bin_repr)) + bin_repr

                hex_addr = hex(addr).upper()[2:]

                print(f"0x{hex_addr}: 0x{hex_repr} (0b{padded_bin_repr})")
                continue

            if cmd.lower().startswith("step ") and cmd.lower().endswith(" times"):
                count = int(
                    cmd.lower().replace("step ", "").replace(" times", "").strip()
                )
                continue

            match cmd.lower():
                case "run until unknown":
                    run_until_unknown = True
                case "run forever":
                    run_forever = True
                case "step":
                    pc = self.pc
                    sp = self.sp
                    regs = self.registers.copy()
                    try:
                        self.step()
                    except Exception as e:
                        self.pc = pc
                        self.sp = sp
                        self.registers = regs
                        print(f"Error during execution of '{self.disasm()}': {str(e)}")
                        print("PC, SP, and registers have been restored")
                case "peek":
                    instr = self.memory.read_byte(self.pc)
                    hex_repr = hex(instr).upper()[2:]
                    bin_repr = bin(instr)[2:]
                    padded_bin_repr = "0" * (8 - len(bin_repr)) + bin_repr

                    print(f"0x{hex_repr} (0b{padded_bin_repr}): {self.disasm()}")
                case "pc":
                    pc_hex = hex(self.pc).upper()[2:]
                    print(f"0x{pc_hex}")
                case "sp":
                    sp_hex = hex(self.sp).upper()[2:]
                    print(f"0x{sp_hex}")
                case "":
                    continue
                case "exit":
                    exit(0)
                case _:
                    print("Unknown command!")
