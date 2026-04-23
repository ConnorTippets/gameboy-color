# i'll handle bank switching later
WRAM_SIZE = 8 * 1024
DEFAULT_WRAM_START = 0xC000

ROM_SIZE = 32 * 1024 - 0x0100
DEFAULT_ROM_START = 0x0100

ECHO_START = 0xE000
ECHO_END = 0xFDFF


class Readable:
    buf: bytearray

    def read_byte(self, addr: int) -> int:
        return self.buf[addr]

    def read_word(self, addr: int) -> int:
        return (self.buf[addr + 1] << 4) & self.buf[addr]


class Writeable:
    buf: bytearray

    def write_byte(self, addr: int, val: int):
        self.buf[addr] = val


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


class Memory:
    def __init__(self):
        self.boot_rom = BootROM()
        self.rom = ROM()
        self.wram = WRAM()

    def read_byte(self, addr: int) -> int:
        if 0x0000 <= addr < 0x0100:
            return self.boot_rom.read_byte(addr)
        if self.rom.start <= addr and addr < self.rom.end:
            return self.rom.read_byte(addr - self.rom.start)
        elif self.wram.start <= addr and addr < self.wram.end:
            return self.wram.read_byte(addr - self.wram.start)
        elif ECHO_START <= addr and addr < ECHO_END:
            return self.wram.read_byte(addr - ECHO_START)
        else:
            raise Exception(f"Invalid mem read: {hex(addr).upper()[2:]}")

    def read_word(self, addr: int) -> int:
        if 0x0000 <= addr < 0x0100:
            return self.boot_rom.read_word(addr)
        if self.rom.start <= addr and addr < self.rom.end:
            return self.rom.read_word(addr - self.rom.start)
        elif self.wram.start <= addr and addr < self.wram.end:
            return self.wram.read_word(addr - self.wram.start)
        elif ECHO_START <= addr and addr < ECHO_END:
            return self.wram.read_word(addr - ECHO_START)
        else:
            raise Exception(f"Invalid mem read: {hex(addr).upper()[2:]}")

    def write_byte(self, addr: int, val: int):
        if self.rom.start - 0x0100 <= addr and addr < self.rom.end:
            raise Exception(
                f"Attempted to write to address in ROM space! Absolute: {hex(addr).upper()[2:]}; Relative: {hex(addr - self.rom.start).upper()[2:]}"
            )
        elif self.wram.start <= addr and addr < self.wram.end:
            return self.wram.write_byte(addr - self.wram.start, val)
        elif ECHO_START <= addr and addr < ECHO_END:
            return self.wram.write_byte(addr - ECHO_START, val)
        else:
            raise Exception(f"Invalid mem write: {hex(addr).upper()[2:]}")

    def load_boot_rom(self, path: str):
        buf = bytearray()
        with open(path, "rb") as handle:
            buf = bytearray(handle.read())

        # evil! >:)
        self.boot_rom.buf = buf[0x0000:0x0100]
