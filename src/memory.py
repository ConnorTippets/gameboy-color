# i'll handle bank switching later
WRAM_SIZE = 8 * 1024
DEFAULT_WRAM_START = 0xC000

ROM_SIZE = 32 * 1024
DEFAULT_ROM_START = 0x0000

ECHO_START = 0xE000
ECHO_END = 0xFE00

VRAM_SIZE = 8 * 1024
DEFAULT_VRAM_START = 0x8000

HRAM_SIZE = 128
DEFAULT_HRAM_START = 0xFF80

IO_SIZE = 128
DEFAULT_IO_START = 0xFF00

ERAM_SIZE = 8 * 1024
DEFAULT_ERAM_START = 0xA000

OAM_SIZE = 0xA0
DEFAULT_OAM_START = 0xFE00


class Readable:
    buf: bytearray

    def read_byte(self, addr: int) -> int:
        return self.buf[addr]

    def read_word(self, addr: int) -> int:
        return (self.buf[addr + 1] << 8) | self.buf[addr]


class Writeable:
    buf: bytearray

    def write_byte(self, addr: int, val: int):
        self.buf[addr] = val

    def write_word(self, addr: int, val: int):
        self.buf[addr] = val & 0xFF
        self.buf[addr + 1] = (val & 0xFF00) >> 8


class MemoryMapped:
    start: int
    size: int

    @property
    def end(self):
        return self.start + self.size


class WRAM(Readable, Writeable, MemoryMapped):
    def __init__(self):
        self.buf = bytearray(WRAM_SIZE)
        self.start = DEFAULT_WRAM_START
        self.size = WRAM_SIZE


class VRAM(Readable, Writeable, MemoryMapped):
    def __init__(self):
        self.buf = bytearray(VRAM_SIZE)
        self.start = DEFAULT_VRAM_START
        self.size = VRAM_SIZE


class HRAM(Readable, Writeable, MemoryMapped):
    def __init__(self):
        self.buf = bytearray(HRAM_SIZE)
        self.start = DEFAULT_HRAM_START
        self.size = HRAM_SIZE


class ROM(Readable, MemoryMapped):
    def __init__(self):
        self.buf = bytearray(ROM_SIZE)
        self.start = DEFAULT_ROM_START
        self.size = ROM_SIZE

    @classmethod
    def load(cls, path: str):
        rom_buf = bytearray()

        with open(path, "rb") as handle:
            rom_buf = bytearray(handle.read())

        rom = cls()
        rom.buf[: len(rom_buf)] = rom_buf

        return rom


class BootROM(Readable):
    def __init__(self):
        self.buf = bytearray(0x0100)


class IO(Readable, Writeable, MemoryMapped):
    def __init__(self):
        self.buf = bytearray(IO_SIZE)
        self.buf[0x44] = 0x90
        self.start = DEFAULT_IO_START
        self.size = IO_SIZE

    def read_byte(self, addr: int) -> int:
        if 0x10 <= addr and addr <= 0x26:
            return self.buf[addr]
        elif 0x40 <= addr and addr <= 0x4B:
            return self.buf[addr]
        else:
            print(f"WARNING: ATTEMPTING TO READ UNMAPPED IO: 0x{hex(addr).upper()[2:]}")
            return 0xFF

    def read_word(self, addr: int) -> int:
        if 0x10 <= addr and addr <= 0x26:
            return (self.buf[addr + 1] << 8) | self.buf[addr]
        elif 0x40 <= addr and addr <= 0x4B:
            return (self.buf[addr + 1] << 8) | self.buf[addr]
        else:
            print(f"WARNING: ATTEMPTING TO READ UNMAPPED IO: 0x{hex(addr).upper()[2:]}")
            return 0xFFFF

    def write_byte(self, addr: int, val: int):
        if 0x10 <= addr and addr <= 0x26:
            self.buf[addr] = val
        elif 0x40 <= addr and addr <= 0x4B:
            self.buf[addr] = val
        else:
            print(f"WARNING: ATTEMPTING TO WRITE UNMAPPED IO 0x{hex(addr).upper()[2:]}")

    def write_word(self, addr: int, val: int):
        if 0x10 <= addr and addr <= 0x26:
            self.buf[addr] = val & 0xFF
            self.buf[addr + 1] = (val & 0xFF00) >> 8
        elif 0x40 <= addr and addr <= 0x4B:
            self.buf[addr] = val & 0xFF
            self.buf[addr + 1] = (val & 0xFF00) >> 8
        else:
            print(f"WARNING: ATTEMPTING TO WRITE UNMAPPED IO 0x{hex(addr).upper()[2:]}")


class ERAM(Readable, Writeable, MemoryMapped):
    def __init__(self):
        self.buf = bytearray(ERAM_SIZE)
        self.start = DEFAULT_ERAM_START
        self.size = ERAM_SIZE


class OAM(Readable, Writeable, MemoryMapped):
    def __init__(self):
        self.buf = bytearray(OAM_SIZE)
        self.start = DEFAULT_OAM_START
        self.size = OAM_SIZE


class Memory:
    def __init__(self):
        self.boot_rom = BootROM()
        self.boot_rom_enabled = True
        self.rom = ROM()
        self.wram = WRAM()
        self.vram = VRAM()
        self.hram = HRAM()
        self.eram = ERAM()
        self.oam = OAM()
        self.io = IO()
        self.game_rom = bytearray()

    def read_byte(self, addr: int) -> int:
        if 0x0000 <= addr < 0x0100 and self.boot_rom_enabled:
            return self.boot_rom.read_byte(addr)
        if self.rom.start <= addr and addr < self.rom.end:
            return self.rom.read_byte(addr - self.rom.start)
        elif self.wram.start <= addr and addr < self.wram.end:
            return self.wram.read_byte(addr - self.wram.start)
        elif ECHO_START <= addr and addr < ECHO_END:
            return self.wram.read_byte(addr - ECHO_START)
        elif self.vram.start <= addr and addr < self.vram.end:
            return self.vram.read_byte(addr - self.vram.start)
        elif self.hram.start <= addr and addr < self.hram.end:
            return self.hram.read_byte(addr - self.hram.start)
        elif self.eram.start <= addr and addr < self.eram.end:
            return self.eram.read_byte(addr - self.eram.start)
        elif self.oam.start <= addr and addr < self.oam.end:
            return self.oam.read_byte(addr - self.oam.start)
        elif 0xFEA0 <= addr and addr < 0xFF00:
            return 0x00
        elif self.io.start <= addr and addr < self.io.end:
            return self.io.read_byte(addr - self.io.start)
        else:
            raise Exception(f"Invalid mem read: {hex(addr).upper()[2:]}")

    def read_word(self, addr: int) -> int:
        if 0x0000 <= addr < 0x0100 and self.boot_rom_enabled:
            return self.boot_rom.read_word(addr)
        if self.rom.start <= addr and addr < self.rom.end:
            return self.rom.read_word(addr - self.rom.start)
        elif self.wram.start <= addr and addr < self.wram.end:
            return self.wram.read_word(addr - self.wram.start)
        elif ECHO_START <= addr and addr < ECHO_END:
            return self.wram.read_word(addr - ECHO_START)
        elif self.vram.start <= addr and addr < self.vram.end:
            return self.vram.read_word(addr - self.vram.start)
        elif self.hram.start <= addr and addr < self.hram.end:
            return self.hram.read_word(addr - self.hram.start)
        elif self.eram.start <= addr and addr < self.eram.end:
            return self.eram.read_word(addr - self.eram.start)
        elif self.oam.start <= addr and addr < self.oam.end:
            return self.oam.read_word(addr - self.oam.start)
        elif 0xFEA0 <= addr and addr < 0xFF00:
            return 0x00
        elif self.io.start <= addr and addr < self.io.end:
            return self.io.read_word(addr - self.io.start)
        else:
            raise Exception(f"Invalid mem read: {hex(addr).upper()[2:]}")

    def write_byte(self, addr: int, val: int):
        if self.rom.start <= addr and addr < self.rom.end:
            raise Exception(
                f"Attempted to write to address in ROM space! Absolute: {hex(addr).upper()[2:]}; Relative: {hex(addr - self.rom.start).upper()[2:]}"
            )
        elif self.wram.start <= addr and addr < self.wram.end:
            return self.wram.write_byte(addr - self.wram.start, val)
        elif ECHO_START <= addr and addr < ECHO_END:
            return self.wram.write_byte(addr - ECHO_START, val)
        elif self.vram.start <= addr and addr < self.vram.end:
            return self.vram.write_byte(addr - self.vram.start, val)
        elif self.hram.start <= addr and addr < self.hram.end:
            return self.hram.write_byte(addr - self.hram.start, val)
        elif self.eram.start <= addr and addr < self.eram.end:
            return self.eram.write_byte(addr - self.eram.start, val)
        elif self.oam.start <= addr and addr < self.oam.end:
            return self.oam.write_byte(addr - self.oam.start, val)
        elif self.io.start <= addr and addr < self.io.end:
            return self.io.write_byte(addr - self.io.start, val)
        else:
            raise Exception(f"Invalid mem write: {hex(addr).upper()[2:]}")

    def write_word(self, addr: int, val: int):
        if self.rom.start <= addr and addr < self.rom.end:
            raise Exception(
                f"Attempted to write to address in ROM space! Absolute: {hex(addr).upper()[2:]}; Relative: {hex(addr - self.rom.start).upper()[2:]}"
            )
        elif self.wram.start <= addr and addr < self.wram.end:
            return self.wram.write_word(addr - self.wram.start, val)
        elif ECHO_START <= addr and addr < ECHO_END:
            return self.wram.write_word(addr - ECHO_START, val)
        elif self.vram.start <= addr and addr < self.vram.end:
            return self.vram.write_word(addr - self.vram.start, val)
        elif self.hram.start <= addr and addr < self.hram.end:
            return self.hram.write_word(addr - self.hram.start, val)
        elif self.eram.start <= addr and addr < self.eram.end:
            return self.eram.write_word(addr - self.eram.start, val)
        elif self.oam.start <= addr and addr < self.oam.end:
            return self.oam.write_word(addr - self.oam.start, val)
        elif self.io.start <= addr and addr < self.io.end:
            return self.io.write_word(addr - self.io.start, val)
        else:
            raise Exception(f"Invalid mem write: {hex(addr).upper()[2:]}")

    def load_boot_rom(self, path: str):
        buf = bytearray()
        with open(path, "rb") as handle:
            buf = bytearray(handle.read())

        # evil! >:)
        self.boot_rom.buf = buf[0x0000:0x0100]

    def load_game_rom(self, path: str):
        buf = bytearray()
        with open(path, "rb") as handle:
            buf = bytearray(handle.read())

        # evil! >:)
        self.rom.buf[: len(buf)] = buf
