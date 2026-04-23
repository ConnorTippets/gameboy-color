WRAM_SIZE = 32 * 1024


class Readable:
    buf: bytearray

    def read_byte(self, addr: int) -> int:
        return self.buf[addr]


class Writeable:
    buf: bytearray

    def write_byte(self, addr: int, val: int):
        self.buf[addr] = val


class WRAM(Readable, Writeable):
    def __init__(self):
        self.buf = bytearray(WRAM_SIZE)


class ROM(Readable):
    def __init__(self):
        self.buf = bytearray()

    @classmethod
    def load(cls, path: str):
        rom = cls()
        with open(path, "rb") as handle:
            rom.buf = bytearray(handle.read())

        return rom
