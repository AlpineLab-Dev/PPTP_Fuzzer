import random
import string


def rand_u8():
    return random.randint(0, 0xFF)


def rand_u16():
    return random.randint(0, 0xFFFF)


def rand_u32():
    return random.randint(0, 0xFFFFFFFF)


def rand_octet(len: int):
    return "".join(random.choice(string.ascii_letters) for _ in range(len)).encode()
