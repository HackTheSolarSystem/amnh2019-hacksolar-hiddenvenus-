# The most basic function is an absolute range of bytes and a function
# to interpret those bytes.

# These are functions which take a series of bytes and interprets
# them. The source is a bytes object, and those bytes may represent
# ascii letters, or an integer.
# All Interpretations return a result of some kind, like a number or
# some string.

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

def dictPath(dic, path):
    if path in ['', '/']:
        return dic

    curVal = dic
    for element in [x for x in path.split('/') if x != '']:
        if element in curVal:
            curVal = curVal[element]
        else:
            raise KeyError

    return curVal

class RecordTypes:
    # Integer is little endian.
    class Integer:
        def __init__(self, length, signed=False):
            self.length = length
            self.signed = signed

        def __call__(self, source):
            number = int.from_bytes(
                    source[:self.length], byteorder='little',
                    signed=self.signed)
            return number, source[self.length:]

    class Fixed_length_string:
        def __init__(self, length):
            self.length = length

        def __call__(self, source):
            return source[:self.length].decode('ascii'), source[self.length:]

    # decimal integer
    class Ascii_integer:
        def __init__(self, length):
            self.length = length

        def __call__(self, source):
            return int(source[:self.length].decode('ascii')), source[self.length:]

    class Plain_bytes:
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
    # "fraction" here refers to the mantissa of a floating point
    # number, the terminology used by the NASA report on Magellan
    # data.
    @staticmethod
    def _fraction_from_bits(*bits):
        accum = 0
        # power should end in -1.
        # if there's one bit, then power starts at -1 and ends at -1.
        # if there's two bits, then power starts at -1, and ends at
        # -2.
        # if there's n bits, then power starts at -1 and ends at -n.
        power = -len(bits)

        # NOTE: The order of accumulation is important. Starting from
        # small amounts reduces possibility of rounding errors.
        # Though... in truth, I'm not sure if that matters for this
        # particular application. All of the values should be things
        # that could fit in the mantissa of a typical IEEE 754
        # floating point number. And they always will be.
        for bit in bits:
            accum = accum + bit * 2 ** power
            power = power + 1

        return 1.0 + accum

    # NOTE: These are not IEEE 754 floating point numbers. Their
    # format is different, as is the bias on the exponent (-128,
    # instead of IEEE 754's -127).
    class Single_float:
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

    class Double_float:
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

    # This is slightly different from the other functions, and only
    # makes sense with a Series record. This allows one to use the
    # value interpreted by a record to decide what record to use. This
    # way, information in a binary file can influence how later parts
    # of the file are interpreted.
    # Outside of a series record, there is no other information to
    # consider, thus this only makes sense when there are other
    # records.
    # referred_record : The name of a sibling record (another record
    # in the same Series record), or a path to the record, relative to
    # the outermost Series record).
    # action : A function which accepts a single value and produces a
    # record function, like RecordTypes.Integer(2), for instance.
    class If:
        def __init__(self, referred_record, action):
            self.record_path = referred_record
            self.action = action

        def __call__(self, source, record_value):
            return self.action(record_value)(source)

    # For a series of contiguous records.
    # Each record has a name. A few names may be reserved for special
    # things. The names of keyword arguments are the names of the
    # records, and the arguments are record functions.
    class Series:
        # NOTE: If I wanted to throw early errors where I KNOW
        # something is wrong just based on the order/type of records
        # given, here's the place to do it (eg having a record after
        # Plain_bytes with an unknown length, there should be no bytes
        # to read after that).
        def __init__(self, **records):
            self.records = records

        def __call__(self, source, parentDict=None, givenDict=None):
            remaining_source = source
            filled_records = {} if givenDict is None else givenDict

            # What needs special handling?
            # - reserved names for records, which should be handled
            #   specifically.
            # - Things of unknown length. They rely on knowing things
            #   about the current record.
            # - other Series type records.
            #   - This oughta work for a valid series of basic records.
            #     This alone. In fact, it should work even if one of
            #     the records is itself a series. Just so long as
            #     everything is of a fixed length, contiguous in
            #     memory.
            #   - Things should change if I want to allow references
            #     to other values of records. A name needs to be able
            #     to refer to the record that it looks up, and that
            #     name may refer to a "parent" series. Thus, children
            #     series need to be able to see their parent. So I
            #     need to pass in the parent. Maybe the best way to do
            #     this is to just pass in the whole current dictionary
            # - If type records.
            for name, func in self.records.items():
                if isinstance(func, RecordTypes.Series):
                    to_fill = {}
                    value, remaining_source = func(
                            remaining_source, filled_records, to_fill)
                elif isinstance(func, RecordTypes.If):
                    if '/' in func.record_path:
                        record_val = filled_records[func.record_path]
                    else:
                        record_val = dictPath(filled_records, func.record_path)
                    value, remaining_source = func(remaining_source,
                            record_val)
                else:
                    value, remaining_source = func(remaining_source)
                filled_records[name] = value

            return dict(filled_records), remaining_source

    # For a series of records that are named as one group rather than
    # indidivually. For example, the radiometer data annotation labels
    # contains some data describing the temperature of 5 segments of
    # cable (in the magellan spacecraft, probably). Rather than name
    # each individual one, as with 
    #   series = R.Series(one=R.Single_float(), two=R.Single_float(), ...)
    # name the whole:
    #   lst = R.List(5*[R.Single_float()])
    # NOTE: For now, list only supports basic records, that is any
    # record that requires only a source. Thus If is not a basic
    # record.
    class List:
        def __init__(self, record_list):
            self.record_list = record_list

        def __call__(self, source):
            remaining_source = source
            values = []
            for record in self.record_list:
                value, remaining_source = record(remaining_source)
                values.append(value)

            return values, remaining_source

# I've made a little error in reasoning. I figured that
# compose_records would be recursive. Basically, the input was either
# a series of simple records, or at least one of the records needed to
# be composed, too, and compose_records would take care of making
# those recursive calls. And this was under the assumtpion that the
# user would make calls to compose_records while making record
# functions. This can't be the case, unless I want the user to have to
# manually construct the paths for things (paths for referring to
# future values of records). So I'll have to make a way to signify
# that something is a series of records, and then have compose records
# act on that.

# TODO:
# - Improve on this to allow references to sibling records (I think
#   this is done).
