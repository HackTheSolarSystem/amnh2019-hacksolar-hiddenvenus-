class Node():
    def __init__(self, value, parent=None):
        self.value = value
        self.parent = parent

    def add(self, value, name=None):
        if isinstance(self.value, list):
            self.value.append(value)
        elif isinstance(self.value, dict) and name is not None:
            self.value[name] = value
        else:
            # Assumes that no errors can happen with value type.
            raise KeyError("Need a name to add to dictionary.")

        if isinstance(value, Node):
            value.parent = self

    def __getitem__(self, *args):
        if isinstance(self.value, (dict, list)):
            return self.value.__getitem__(*args)
        else:
            raise ValueError("value is not a valid container.")

    @property
    def p(self):
        return self.parent

    def is_leaf(self):
        return isinstance(self.value, (dict, list))

# First, traverse the meta-record and get a list of all the leaf
# records. That's all records which are not Series/List. Ifs count as
# leaf records for now, but they will be updated later.

# One trouble of mine: if this scheme works with If, it should work
# with all records.

# Make an empty record in the same shape as the meta record with a
# list of "nodes": places to add values in when they've been processed
# from the input file.
#
# Then, pair up the leaf nodes and leaf records. This will be the
# processing order of the file. The order of the records to be
# processed and where to put the interpreted value.
#
# If encounter an if record, resolve it for it's record, and then put
# it ahead of everything else in the list of stuff to process. And we
# hit a problem. We have to make a general scheme. Because processing
# the if may return a non-leaf node. And whatever logic would've
# worked for the general case of "process all the nodes as they come
# without depending on some original shape" is exactly the logic I'd
# have to write for this situation of processing an If record.

class RecordTypes:
    class Integer:
        """Binary record for little endian integers of fixed length."""
        def __init__(self, length, signed=False):
            self.length = length
            self.signed = signed

        def __call__(self, source, **kwargs):
            number = int.from_bytes(
                    source[:self.length], byteorder='little',
                    signed=self.signed)
            return number, source[self.length:]

    class FixedLengthString:
        """Binary record for ASCII strings of fixed length."""
        def __init__(self, length):
            self.length = length

        def __call__(self, source, **kwargs):
            return (bytes(source[:self.length]).decode('ascii'),
                    source[self.length:])

    class AsciiInteger:
        """Binary record for ASCII strings which describe decimal
        numbers (just the characters 0-9), of fixed length."""
        def __init__(self, length):
            self.length = length

        def __call__(self, source, **kwargs):
            return (int(bytes(source[:self.length]).decode('ascii')),
                    source[self.length:])

    class PlainBytes:
        def __init__(self, length='unknown'):
            self.length = length

        def __call__(self, source, **kwargs):
            if self.length == 'unknown':
                return source, bytes()
            else:
                return bytes(source[:self.length]), source[self.length:]

    class _FigureOutLater:
        """length may be 'unknown', or int, or callable, where the
        callable takes the root_record as the argument."""
        def __init__(self, length='unknown'):
            self.length = length

        def __call__(self, source, **kwargs):
            if self.length == 'unknown':
                return source, bytes()
            else:
                length = (self.length if isinstance(self.length, int) else
                            self.length(root_record.root,
                                root_record.current))
                return bytes(source[:length]), source[length:]

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
    class Float:
        """Binary record for floating point numbers in NASA's format,
        which are not IEEE 754 floating point numbers."""
        def __init__(self, Type):
            if Type == 'single':
                self.length = 4
            elif Type == 'double':
                self.length = 8
            else:
                raise ValueError

        def __call__(self, source, **kwargs):
            bits = RecordTypes._bytes_to_bits(source[:self.length])
            exponent = RecordTypes._bytes_from_bits(*bits[7:15])
            if exponent == 0:
                return float(0), source[self.length:]

            exponent = exponent - 128
            sign = 1 if bits[15] == 0 else -1
            fraction = RecordTypes._fraction_from_bits(*bits[16:], *bits[:7])
            value = sign * fraction * 2 ** exponent
            return value, source[self.length:]

    class If:
        """Slightly different from other records. Only makes sense
        with a Series record. This allows one to use the value
        interpreted by a record to decide what record to
        use. This way, information in a previous part of a binary file
        can influence how later parts of the file are interpreted.
        Outside of a series record, there is no other information to
        consider, thus this only makes sense when there are other
        records.

        Parameters
        ==========

        referred_record, callable : A function which takes in the root
            record and returns an existing value in the root record.
        action, callable : A function which accepts a single value and
            produces a record function, like RecordTypes.Integer(2), for
            instance.
        """
        def __init__(self, referred_record, action):
            self.referred_record = referred_record
            self.action = action

        def __call__(self, root_record, current):
            # TODO: This is a problem, because arrays can return
            # slices. Just doing .value is not enough. Either that or
            # warn a user that this falls apart with array slices.
            value = self.referred_record(root_record, current).value
            return self.action(value)

    # For a series of contiguous records.
    # Each record has a name. A few names may be reserved for special
    # things. The names of keyword arguments are the names of the
    # records, and the arguments are record functions.
    class Series:
        """Interprets a series of named records. A few names may be
        reserved for special things in the future.

        **records : A dictionary of the records to interpret. The key
            is the name of the record and the value is a record
            function. The result is a dictionary whose keys are the
            record names and whose values are the interpreted records.
            Any record type may be a value of a series record,
            including another series record.
        """
        # NOTE: If I wanted to throw early errors where I KNOW
        # something is wrong just based on the order/type of records
        # given, here's the place to do it (eg having a record after
        # PlainBytes with an unknown length, there should be no bytes
        # to read after that).
        def __init__(self, **records):
            self.records = records

        # NOTE: The use of givenDict is to allow the root_record to
        # have a record's siblings as well as descendants. 
        def __call__(self, source, root_record=None):
            process_meta_record(source, self)

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
        """A series of unnamed records. Pass in a list of record
        functions. They will be interpreted one after the other.

        Supports only basic record functions, ones whose length is
        fixed.
        """
        def __init__(self, record_list):
            self.record_list = record_list

        def __call__(self, source):
            process_meta_record(self)

def tree_to_values(tree):
    inside = tree.value
    if isinstance(inside, dict):
        for k, v in inside.items():
            inside[k] = tree_to_values(v)
    elif isinstance(inside, list):
        for i in range(len(inside)):
            inside[i] = tree_to_values(inside[i])
    #else:
        #return tree.value

    return inside

# source is a memoryview of a bytes object.
def process_meta_record(source, meta_record):
    # node_stack here will contain an old tree node and it's
    # corresponding new tree node. And the node's name if it has one.
    if isinstance(meta_record, RecordTypes.Series):
        root = Node(dict())
    else:
        root = Node(list())
    remaining_source = source

    node_stack = [[meta_record, root, None]]

    while len(node_stack) != 0:
        old, new, name = node_stack.pop()
        if isinstance(old, RecordTypes.Series):
            old_children = old.records.items()
            new.value = dict()
            length = len(node_stack)
            for k, v in old_children:
                new_node = Node(None, parent=new)
                node_stack.insert(length, [v, new_node, k])
                new.add(new_node, name=k)
        elif isinstance(old, RecordTypes.List):
            new.value = list()
            length = len(node_stack)
            for child in old.record_list:
                new_node = Node(None, parent=new)
                node_stack.insert(length, [v, new_node, None])
                new.add(child, name=k)
        elif isinstance(old, RecordTypes.If):
            resolved_record = old(root, new)
            node_stack.append([resolved_record, new, name])
        else:
            # Only "leaf records" are actual non-meta record functions
            # that consume source.
            #print(f'name: {name}, old: {old}')
            value, remaining_source = old(
                    remaining_source, root_record=root, current=new)
            #print(f'value info: ({value}, {bytes(remaining_source)})')
            new.value = value

    #return tree_to_values(root), remaining_source
    return root, remaining_source

# TODO:
# - Improve on this to allow references to sibling records (I think
#   this is done).
# - Solidify this concept of a "basic record". What is it? Is is just
#   a record of fixed length which requires no information aside from
#   the binary source to read stuff from? Does it have to know its
#   length?
#       - This is good enough for now. Later and better meanings will
#         come from working with this and running face-first into
#         errors, not from a bunch of armchair planning.
