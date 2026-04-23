# i'll handle bank switching later
WRAM_SIZE = 8 * 1024
DEFAULT_WRAM_START = 0xC000

ROM_SIZE = 32 * 1024
DEFAULT_ROM_START = 0x0000

ECHO_START = 0xE000
ECHO_END = 0xFDFF


class Readable:
    buf: bytearray

    def read_byte(self, addr: int) -> int:
        return self.buf[addr]


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


class Memory:
    def __init__(self):
        self.rom = ROM()
        self.wram = WRAM()

    def read_byte(self, addr: int) -> int:
        if self.rom.start <= addr and addr < self.rom.end:
            return self.rom.read_byte(addr - self.rom.start)
        elif self.wram.start <= addr and addr < self.wram.end:
            return self.wram.read_byte(addr - self.wram.start)
        elif ECHO_START <= addr and addr < ECHO_END:
            return self.wram.read_byte(addr - ECHO_START)
        else:
            raise Exception(f"Invalid mem read: {hex(addr).upper()[2:]}")
