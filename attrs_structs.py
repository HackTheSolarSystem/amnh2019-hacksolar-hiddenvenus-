# The most basic function is an absolute range of bytes and a function
# to interpret those bytes.

# These are functions which take a series of bytes and interprets
# them. The source is a bytes object, and those bytes may represent
# ascii letters, or an integer.
# All Interpretations return a result of some kind, like a number or
# some string.
class Interpretations:
    # the source argument is always a bytes object.
    # start and length are always bytes.
    # It's assumed that signed integers are in two's complement.
    # The most significant bit is in the most significant byte, which
    # is last.
    @staticmethod
    def integer(source, signed=False):
        big_endian = source[::-1]
        if signed:
            # Is the most significant bit equal to 1?
            nonnegative = big_endian[-1] < 0x80
            if nonnegative:
                return int(big_endian.hex(), 16)
            else:
                positive = int((~big_endian).hex(), 16) + 1
                return -positive
        else:
            return int(big_endian.hex(), 16)
    @staticmethod
    def ascii_integer(source):
        return int(source.decode('ascii'), 10)
    @staticmethod
    def ascii_string(source):
        return source.decode('ascii')
    @staticmethod
    def plain(source):
        return source
    # For now, enumeration is a dict of the form "unsigned integer : what it
    # means"
    @staticmethod
    def enumeration(source, enum):
        return lambda src: enum[Interpretations.integer(source)]

# This is a record function:
# It takes a bytes object, and returns an interpretation of some of
# the bytes, and returns the bytes that it does not use:
def ascii_string_length_4(source):
    return source[0:4].decode('ascii'), source[4:]

# A record function can consume all the bytes that it's given. Here
# are two examples:

# Really simple, just consume all the bytes. Though common enough.
def plain_bytes(source):
    return source

# the whole source may be one c_string, and thus consume all the
# bytes. Though it may not.
def c_string(source):
    end = source.find(0)
    if end == -1:
        return source.decode('ascii'), bytes()
    else:
        return source[:end].decode('ascii'), source[end:]

# Convenient composition of these records into larger records requires
# some metadata, like knowledge of how many bytes will be consumed.
# Because the next record has to pick up where the previous record
# left off. 
#
#   (I can see occasion to break this constraint of contiguous regions
#   of bytes corresponding only to one thing, but for now let's keep
#   it simple).
#   Also, doesn't the returning of unconsumed bytes handle that all on
#   it's own?
#   
# hm. The metadata would help for catching bugs before a records
# function is handed a bytes object.

# Compositions of bytes return dicts or named tuples. haven't decided.
# It's not super important, anyhow.

class RecordTypes:
    # Integer is little endian.
    class integer:
        def __init__(self, length, signed=False):
            self.length = length
            self.signed = signed

        def __call__(self, source):
            number = int.from_bytes(
                    source[:self.length], byteorder='little',
                    signed=self.signed)
            return number, source[self.length:]

    class fixed_length_string:
        def __init__(self, length):
            self.length = length

        def __call__(self, source):
            return source[:self.length].decode('ascii'), source[self.length:]

    # decimal integer
    class ascii_integer:
        def __init__(self, length):
            self.length = length

        def __call__(self, source):
            return int(source[:self.length].decode('ascii')), source[self.length:]

    class plain_bytes:
        def __init__(self, length='unknown'):
            self.length = length

        def __call__(self, source):
            if self.length == 'unknown':
                return source, bytes()
            else:
                source[:self.length], source[self.length:]

    @staticmethod
    def _bytes_from_bits(*args, order='little'):
        # The first bit is the least significant.
        if order == 'little':
             bit_value = 1;
             number = 0
             for bit in args:
                 number = number + bit * bit_value
                 bit_value = bit_value * 2
        # The first bit is the most significant.
        else: 
            number = 0
            for bit in args:
                number = number * 2 + bit
        return number

    # num is a nonnegative integer between 0 and 255,
    @staticmethod
    def _byte_to_bits(num):
        return [(num >> i) & 1 for i in range(7, -1, -1)]

    @staticmethod
    def _bytes_to_bits(source):
        bytes_as_bits = [RecordTypes._byte_to_bits(i) for i in source]
        ret = []
        for bit_array in bytes_as_bits:
            ret = ret + bit_array

        return ret

    # Assumes that the 1st bit in bits is the least significant.
    @staticmethod
    def _fraction_from_bits(*bits):
        accum = 0
        # power should end in -1.
        # if there's one bit, then power starts at -1 and ends at -1.
        # if there's two bits, then power starts at -1, and ends at
        # -2.
        # if there's n bits, then power starts at -1 and ends at -n.
        power = -len(bits)

        for bit in bits:
            accum = accum + bit * 2 ** power
            power = power + 1

        return 1.0 + accum

    # NOTE: These are not IEEE 754 floating point numbers. Their
    # format is very different, as is the bias on the exponent (-128,
    # instead of IEEE 754's -127).
    class single_float:
        def __init__(self):
            self.length = 4

        def __call__(self, source):
            bits = RecordTypes._bytes_to_bits(source[:self.length])
            exponent = RecordTypes._bytes_from_bits(*bits[7:15])
            if exponent == 0:
                return float(0), source[self.length:]

            exponent = exponent - 128
            sign = 1 if bits[15] == 0 else -1
            fraction = RecordTypes._fraction_from_bits(*bits[16:], *bits[:7])
            value = sign * fraction * 2 ** exponent
            return value, source[self.length:]

    class double_float:
        def __init__(self):
            self.length = 8

        def __call__(self, source):
            bits = RecordTypes._bytes_to_bits(source[:self.length])
            exponent = RecordTypes._bytes_from_bits(*bits[7:15])
            if exponent == 0:
                return float(0), source[self.length:]

            exponent = exponent - 128
            sign = 1 if bits[15] == 0 else -1
            fraction = RecordTypes._fraction_from_bits(*bits[16:], *bits[:7])
            value = sign * fraction * 2 ** exponent
            return value, source[self.length:]
            
# for the data annotation label, I may need to allow decision making
# (feels like overkill), or something else. Because there's different
# formats for the data annotation label (even empty) based on what the
# data is. The only reason for trying to do this is for trying to
# maintain a completely declarative description.

# For the time being, I'll describe each data annotation for each kind
# of data separately.

def image_data_annoation_label(source):
    records = [
        ('image line count', RecordTypes.integer(2)),
        ('image line length', RecordTypes.integer(2)),
        ('projection origin latittude', RecordTypes.single_float()),
        ('projection origin longitude', RecordTypes.single_float()),
        ('reference point latitude', RecordTypes.single_float()),
        ('reference point offset in lines', 
            RecordTypes.integer(4, signed=True)),
        ('reference point offset in pixels', 
            RecordTypes.integer(4, signed=True)),
        ('burst counter', RecordTypes.integer(4)),
        ('nav unique id', RecordTypes.fixed_length_string(32)),
    ]

    remaining_source = source
    filled_records = []
    for record in records:
        value, remaining_source = record[1](remaining_source)
        filled_records.append((record[0], value))

    return dict(filled_records), remaining_source

def annotation_block(source):
    length = 'unknown'
    remaining_length = 'unknown'
    records = [
        ('data class', RecordTypes.integer(1)),
        ('remaining_record_length', RecordTypes.integer(2)),
        ('data annotation label', RecordTypes.plain_bytes()),
    ]

    remaining_source = source
    filled_records = []
    for record in records:
        name, recordType = record
        if name == 'remaining_record_length':
            remaining_length, remaining_source = recordType(remaining_source)
            # What would I do here if I didn't know if
            # remaining_record_length would show up at all?
            remaining_source = source[:remaining_length]
            source_to_return = source[remaining_length:]
        else:
            value, remaining_source = recordType(remaining_source)
            filled_records.append((name, value))

    return dict(filled_records), source_to_return

def secondary_header(source):
    record_length = 'unknown'
    remaining_record_length = 'unknown'
    records = [
        ('BIDR secondary label type', RecordTypes.integer(2)),
        ('remaining_record_length', RecordTypes.integer(2)),
        ('orbit number', RecordTypes.integer(2)),
        ('annotation block', RecordTypes.plain_bytes()),
    ]
