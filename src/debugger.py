from .cpu import CPU
from .util import sign_convert

R8 = ["B", "C", "D", "E", "H", "L", "[HL]", "A"]
R16 = ["BC", "DE", "HL", "SP"]
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
                    case _:
                        hex_repr = hex(instr).upper()[2:]
                        bin_repr = bin(instr)[2:]
                        padded_bin_repr = "0" * (8 - len(bin_repr)) + bin_repr

                        return f"Unknown 0xCB instruction: 0x{hex_repr} (0b{padded_bin_repr})"
            case _:
                return "Unknown instruction!"

    def run(self):
        while True:
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

            match cmd.lower():
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
