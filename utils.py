import random
import string


def rand_u8():
    return random.randint(0, 0x100)


def rand_u16():
    return random.randint(0, 0x10000)


def rand_u32():
    return random.randint(0, 0x100000000)


def rand_octet(len: int):
    return "".join(random.choice(string.ascii_letters) for _ in range(len))
