def sign_convert(unsigned: int) -> int:
    return unsigned - 256 if unsigned >= 128 else unsigned
