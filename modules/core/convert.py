# Author:       Connor DeCamp
# Created on:   7/29/2021
#
# History:      7/29/2021 - Added byte conversions 
#               9/09/2021 - Fixed type error in ieee754_to_int()
#
# See SFF-8472 for tables that determine what each
# value means in the memory map.

from decimal import *

def ieee754_to_int(b3: int, b2: int, b1: int, b0: int) -> int:
    '''
    Takes 4 bytes in IEEE 754 floating point format and converts it into a floating point
    number as per the IEEE 754 specification. The MSB (bit 31) is the sign bit,
    bits 2-9 are the exponent, and the rest belong to the mantissa.

    S = sign
    E = Exponent
    M = Mantissa
    
    (Byte, Contents, Significance)\n
    (b3,     SEEEEEEE,       most)\n
    (b2,     EMMMMMMM,    second most)\n
    (b1,     MMMMMMMM,    second least)\n
    (b0,     MMMMMMMM,       least)\n
    '''

    # Put bytes into array to make it easier to
    # convert into binary string
    bytelist = [b3, b2, b1, b0]
    s = ""
    for b in bytelist:
        s += format(b, '08b')        # Format each number in binary

    sign = int(s[0:1])               # Sign is the first bit
    exponent = int(s[1:9], 2) - 127  # Exponent is the next 8 bits, subtract 127 to unbias it
    mantissa_str = s[9:32]           # Mantissa (fraction) is the rest of the number (1.M)
    mantissa_int = Decimal('1')      # Begin converting mantissa bits into fraction
    power = -1                       # We need 1.M, so first power is 2^(-1) * bit and decreases from there

    for bit in mantissa_str:
        mantissa_int += Decimal(str(int(bit) * (2 ** power)))
        power -= 1
    

    result = Decimal(pow(-1, int(sign))) * Decimal(pow(2, exponent)) * mantissa_int # (-1)^sign * 2^(exponent) * 1.M
    
    return result

def bytes_to_unsigned_decimal(b1: int, b0: int) -> Decimal:
    '''
    Takes in 2 bytes, formatted as b1.b0 and returns the
    unsigned decimal equivalent. For example:
        b1 = 1111 1111
        b0 = 1111 1111

    Number it represents is 1111 1111.1111 1111
    which is 255 + (255) / 256
    '''

    integer = Decimal(str(b1))
    mantissa_str = format(b0, '08b')
    mantissa_int = Decimal('0')
    power = -1

    for b in mantissa_str:
        mantissa_int += Decimal(str(int(b) * pow(2, power)))
        power -= 1

    return Decimal(str(integer + mantissa_int))

def signed_twos_complement_to_int(b1: int, b0: int) -> int:
    '''
    Takes two bytes (b1, b0) and converts it from signed two's complement
    into an integer.
    '''

    bit_string = format(b1, '08b') + format(b0, '08b')
    bits = len(bit_string)
    val = int(bit_string, 2)

    if (val & (1 << (bits - 1))) != 0:
        val = val - (1 << bits)
    
    return val