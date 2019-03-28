class Node():
    def __init__(self, value, parent=None):
        self.value = value
        self.parent = parent
        self._debug_info = None
        self._ismrecord = False

    def add(self, value, name=None):
        if isinstance(self.value, list):
            if name is not None:
                self.value[name] = value
            else:
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

    # TODO: A distinction between metarecord nodes and nodes that just
    # happen to contain a list or dict should be made. The printing is
    # very ugly for lists of stuff. Change process_meta_record and
    # Node to include this information on the node, have _print use
    # the info for printing. Basically, only metarecord nodes will get
    # the recursive treatment.
    @staticmethod
    def _print(tree, prefix="", path=None):
        real_path = ['/'] if path is None else path
        inside = tree.value
        new_prefix = prefix + '\t'
        tree_text = ''
        tree_text += f'{prefix}{repr(tree)}: {tree._debug_info}\n'
        if isinstance(inside, dict) and tree._ismrecord:
            for k, v in inside.items():
                tree_text += f'{prefix}{k}\n'
                tree_text += Node._print(v, new_prefix, real_path + [k]) + "\n"
        elif isinstance(inside, list) and tree._ismrecord:
            for i in range(len(inside)):
                tree_text += f'{prefix}{i}\n'
                tree_text += Node._print(inside[i], new_prefix, real_path + [i]) + "\n"
        else:
            tree_text += f'{prefix}{inside}'

        return tree_text

    def __str__(self):
        return self._print(self)


# TODO: Memoize the basic record functions. saves memory. The
# initializers, that is.
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
        # Sources:
        # <https://sixlettervariable.blogspot.com/2007/05/vax-floating-point-numbers.html>
        # <https://nssdc.gsfc.nasa.gov/nssdc/formats/VAXFloatingPoint.htm>
        # BIDR Document
        # The MSB should have place value 2^(-2) (2^0, and 2^(-1) are
        # implicit).
        # power should end in -2.
        # if there's one bit, then power starts at -2 and ends at -2.
        # if there's two bits, then power starts at -2, and ends at
        # -3.
        # if there's n bits, then power starts at -2 and ends at -(n + 1).
        power = -len(bits) - 1

        # NOTE: The order of accumulation is important. Starting from
        # small amounts reduces possibility of rounding errors.
        # Though... in truth, I'm not sure if that matters for this
        # particular application. All of the values should be things
        # that could fit in the mantissa of a typical IEEE 754
        # floating point number. And they always will be.
        for bit in bits:
            accum = accum + bit * 2 ** power
            power = power + 1

        return 0.1 + accum

    # NOTE: These are not IEEE 754 floating point numbers. Their
    # format is different, as is the bias on the exponent (-128,
    # instead of IEEE 754's -127).
    # TODO: See if you can just write the mantissa bits to memory in
    # correct arrangement, rather than perform arithmetic.
    # TODO: Rename of VAXFloat.
    # TODO: Consider 
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

        # Could be a bit of a bottleneck of speed if a file has tons
        # of VAX floats. Slow parts:
        # - Creating a bit array.
        # - Creating the fraction. This should be hands-down slowest
        #   part. Rearranging lists, copies, a loop.
        # - Calculating sign. This shouldn't be very expensive as
        #   compared to getting the fraction value. That should be so
        #   much more expensive.
        def __call__(self, source, **kwargs): 
            bits = RecordTypes._bytes_to_bits(source[:self.length])
            exponent = RecordTypes._bytes_from_bits(*bits[7:15])
            if exponent == 0:
                return float(0), source[self.length:]

            exponent = exponent - 128
            # If necessary an optimization is:
            # sign = 1 - 2 * bit
            sign = 1 if bits[15] == 0 else -1

            # Using this line with 32-bit floats is harmless, because
            # there will be no bits from the first two lists.
            fraction = RecordTypes._fraction_from_bits(
                    *bits[48:], *bits[32:48], *bits[16:32], *bits[:7])
            value = sign * fraction * 2 ** exponent
            return value, source[self.length:]

    class If:
        """A meta-record. Not a record function on its own, but gives
        some information about record functions used within. This
        allows one to use the value of a previously interpreted record
        to decide what record function to use. This way, information
        in a previous part of a binary file can influence how later
        parts of the file are interpreted.  Outside of a series/list
        records, there is no other information to consider, thus this
        only makes sense when there are other records.

        Parameters
        ==========

        referred_record, callable : A function which takes in both the
            root record and the current record (if you'd prefer to
            work relative to current record) and returns an existing
            value in the root record.
        action, callable : A function which accepts a single value and
            produces a record function, like RecordTypes.Integer(2).
        """
        def __init__(self, referred_record, action):
            self.referred_record = referred_record
            self.action = action

        def __call__(self, root_record, current):
            # TODO: This is a problem, because arrays can return
            # slices. Just doing .value is not enough. Either that or
            # warn a user that this falls apart with array slices.
            # TODO: you may want to let user return a list or tuple,
            # too. Using .value or tree_to_values gets in the way of
            # that.
            value = self.referred_record(root_record, current).value
            return self.action(value)

    class Series:
        """A meta-record. Interprets a series of named records. A few
        names may be reserved for special things in the future.

        **records : A dictionary of the records to interpret. The key
            is the name of the record and the value is any record
            function or meta-record. The result is a dictionary whose
            keys are the record names and whose values are the
            interpreted records.
        """
        # NOTE: If I wanted to throw early errors where I KNOW
        # something is wrong just based on the order/type of records
        # given, here's the place to do it (eg having a record after
        # PlainBytes with an unknown length, there should be no bytes
        # to read after that).
        # TODO: I never implemented some of the functionality, like
        # giving a series metarecord a length, and working with record
        # functions of unknown length.
        def __init__(self, **records):
            self.records = records

        def __call__(self, source, root_record=None):
            return process_meta_record(source, self)

    # NOTE: THe common idiom of creating lists from a multiplied list
    # of records isn't too harsh on memory. It doesn't deep copy those
    # records, it's all shallow copies.
    class List:
        """Metarecord. A series of unnamed records. Pass in a list of
        record functions. They will be interpreted one after the
        other.

        For a series of records that are named as one group rather than
        indidivually. For example, the radiometer data annotation labels
        contains some data describing the temperature of 5 segments of
        cable (in the magellan spacecraft, probably). Rather than name
        each individual one, as with 
          series = R.Series(one=R.Integer(4), two=R.Integer(4), ...)
        name the whole:
          lst = R.List(5*[R.Integer(4)])

        """
        def __init__(self, record_list):
            self.record_list = record_list

        def __call__(self, source):
            return process_meta_record(source, self)

# Mutates original tree.
# TODO: Changes from Node._print are applicable here, too.
def tree_to_values(tree):
    inside = tree.value
    if isinstance(inside, dict) and tree._ismrecord:
        for k, v in inside.items():
            inside[k] = tree_to_values(v)
    elif isinstance(inside, list) and tree._ismrecord:
        for i in range(len(inside)):
            inside[i] = tree_to_values(inside[i])

    # Also works for leaf nodes, just return inside w/o doing
    # anything.
    return inside

# TODO: Add an optional start value. Would go a long way toward
# intelligble debug info for custom record functions that use
# process_meta_record internally.
# TODO: Give meta records starts and ends, too, based on the start of
# their first child and end of their last child.
def process_meta_record(source, meta_record):
    """
    Uses a meta-record to interpret a source of bytes. Behaves
    somewhat like a record function, returning an interpreted value
    and unconsumed bytes from the source, but is not a record function.

    Parameters
    ==========

    source, memoryview: A memoryview of bytes object. Bytes from this
        source will be interpreted by meta_record.
    meta_record : one of RecordTypes's If, Series, or List.

    Returns
    =======

    tree, Node: The tree of interpreted values.
    remaining_source, memoryview : The bytes not consumed from source.
    """
    root = Node(None)
    remaining_source = source
    start = 0

    # elements of node_stack will contain an old tree node and its
    # corresponding new tree node. And the node's name if it has one.
    node_stack = [[meta_record, root, None]]

    while len(node_stack) != 0:
        # Old nodes are meta-record functions, or record functions.
        old, new, name = node_stack.pop()
        if isinstance(old, RecordTypes.Series):
            old_children = old.records.items()
            new.value = dict()
            new._ismrecord = True
            length = len(node_stack)
            for k, v in old_children:
                new_node = Node(None, parent=new)
                node_stack.insert(length, [v, new_node, k])
                new.add(new_node, name=k)
        elif isinstance(old, RecordTypes.List):
            new.value = list()
            new._ismrecord = True
            length = len(node_stack)
            for i, child in enumerate(old.record_list):
                new_node = Node(None, parent=new)
                node_stack.insert(length, [child, new_node, i])
                new.add(new_node, name=None)
        elif isinstance(old, RecordTypes.If):
            resolved_record = old(root, new.p)
            node_stack.append([resolved_record, new, name])
        else:
            # Only "leaf records" are actual non-meta record functions
            # that consume source. This is in contrast to before,
            # where series/list were treated as record functions,
            # could be passed source to consume it, and returned
            # remaining source.
            orig_length = len(remaining_source)
            value, remaining_source = old(
                    remaining_source, root_record=root, current=new.p)
            if isinstance(value, Node):
                value.parent = new.p
                new.p.add(value, name)
                new = value
            else:
                new.value = value

            new_length = len(remaining_source)
            consumed_bytes = orig_length - new_length

            new._debug_info = {'start' : start, 'end' : start + consumed_bytes - 1}
            start += consumed_bytes

    return root, remaining_source

# TODO:
# - Create an Ignore metarecord. Can take length or a record function.
#   The length ignores some number of bytes, the record function
#   processes the record function, but then tosses the value. The tree
#   structure makes an Ignore metarecord very easy. I can have
#   tree_to_values get rid of ignore values. Good use case is for
#   simplified versions of bidr records, where I wanna look at just a
#   little bit of data and ignore the rest.
#       - Optimization: For records with known and fixed length,
#         extract the length and use that instead, rather than using
#         the record function. If length is not present or is unknown,
#         then use the record function and toss the result.
#       - Allow to give a length like an If, using the root_record.
#         Not sure how to pass that in, though. record function is a
#         callable, so is this. How to differentiate? This would make
#         for real simple
# - Make a metarecord for remaining length of a metarecord, rather
#   than a reserved name (which is a bit clunky). f-bidr works like
#   so: the total length of record is bytes so far (after length has
#   been read in) remaining bytes. example: logical record length is
#   bytes 12-19. The read-in length gives bytes remaining from byte 20
#   and on. So if remaining_length were 0, then last byte of record is
#   19. So the exclusive end is byte after remaining_length field +
#   remaining_length. (with example, the exclusive end byte of a
#   logical record with remaining length 0 is byte 20: 20 + 0). Input
#   should be similar to Ignore metarecord.
# - Change is_leaf to use _ismrecord. That's really what _ismrecord
#   records.
# - Optional: At one point, I wanted a record function to be able to
#   return multiple values. I can now do that pretty easily with a
#   metarecord function that wraps around another record function. Or,
#   I could handle it seamlessly at the record function itself. If the
#   record function returns a tuple of values (and remaining source,
#   so ( (), src ), then I could attach the tuple of values as more
#   children to the same parent. Could be name value pairs, too. I've
#   got options. Writing everything in one loop gives me a lot of
#   flexibility, as does separating metarecords from records. I could
#   combine the two, so that I've got a way of differentiating between
#   a value that's a tuple (plain record function) and a tuple of
#   values (trying to return several values).
# - Consider lazy-loading for all known-length records. That would
#   reduce some waiting.
