import unittest
from attrs_structs import (RecordTypes as R,
        process_meta_record,
        tree_to_values,
        Node)
import random

sample_data_dir = 'sample-data'

# Just make sure we're always operating in little endian without
# re-writing it all the time.
def int_to_bytes(number, length, signed=False):
    return number.to_bytes(length, 'little', signed=signed)

class IntegersTests(unittest.TestCase):
    def testReadUnsigned(self):
        int_record = R.Integer(1)
        self.assertEqual(int_record(b'\x00'), (0, b''))
        self.assertEqual(int_record(b'\x01'), (1, b''))
        self.assertEqual(int_record(b'\x05'), (5, b''))
        self.assertEqual(int_record(b'\xff'), (255, b''))

    def testReadSigned(self):
        int_record = R.Integer(1, signed=True)
        self.assertEqual(int_record(b'\x00'), (0, b''))
        self.assertEqual(int_record(b'\x01'), (1, b''))
        self.assertEqual(int_record(b'\x05'), (5, b''))
        self.assertEqual(int_record(b'\xff'), (-1, b''))
        self.assertEqual(int_record(b'\xfe'), (-2, b''))
        self.assertEqual(int_record(b'\xf0'), (-16, b''))

    def testConsumesCorrectNumberBytes(self):
        source = b'\x00\x01\x02\x03'
        for i in range(1, 5):
            value, remaining_source = R.Integer(i)(source)
            self.assertEqual(len(remaining_source), len(source) - i)

        for i in range(1, 5):
            value, remaining_source = R.Integer(i, signed=True)(source)
            self.assertEqual(len(remaining_source), len(source) - i)

    def testReadLongerNumbers(self):
        random_numbers = [random.randrange(0, 256**4)  for x in range(10)]
        int_record = R.Integer(4)
        for number in random_numbers:
            the_bytes = int_to_bytes(number, 4, signed=False)
            self.assertEqual(int_record(the_bytes), (number, b''))

        int_record = R.Integer(5, signed=True)
        random_numbers = [random.randrange(-256**4, 256**4)  for x in range(10)]
        for number in random_numbers:
            the_bytes = int_to_bytes(number, 5, signed=True)
            self.assertEqual(int_record(the_bytes), (number, b''))

class MetaRecordBasicTests(unittest.TestCase):
    def testSeveralRecords(self):
        source = memoryview(bytes([
            0, 
            *int_to_bytes(600, 2),
            *int_to_bytes(70000, 3),
            ]))

        interpretation = {}
        value, rest = R.Integer(1)(source)
        interpretation['one'] = value
        value, rest = R.Integer(2)(rest)
        interpretation['two'] = value
        value, rest = R.Integer(3)(rest)
        interpretation['three'] = value

        self.assertEqual(interpretation['one'], 0)
        self.assertEqual(interpretation['two'], 600)
        self.assertEqual(interpretation['three'], 70000)

    def testProcessRecordOne(self):
        record = R.Series(
                one=R.Integer(1))

        source = memoryview(bytes([
            0, 
            *int_to_bytes(1, 1),
            *int_to_bytes(2, 1),
            ]))

        interpretation, remaining_source = process_meta_record(
                source, record)

        self.assertEqual(interpretation['one'].value, 0)

    def testProcessRecordTwo(self):
        record = R.Series(
                one=R.Integer(1),
                two=R.Integer(1),
                )

        source = memoryview(bytes([
            0, 
            *int_to_bytes(1, 1),
            *int_to_bytes(2, 1),
            ]))

        interpretation, remaining_source = process_meta_record(
                source, record)

        self.assertEqual(interpretation['one'].value, 0)
        self.assertEqual(interpretation['two'].value, 1)

    def testProcessRecord(self):
        record = R.Series(
                one=R.Integer(1),
                two=R.Integer(2),
                three=R.Integer(3)
                )
        source = memoryview(bytes([
            0, 
            *int_to_bytes(600, 2),
            *int_to_bytes(70000, 3),
            ]))


        interpretation, remaining_source = process_meta_record(
                source, record)

        self.assertEqual(interpretation['one'].value, 0)
        self.assertEqual(interpretation['two'].value, 600)
        self.assertEqual(interpretation['three'].value, 70000)

class IfTests(unittest.TestCase):
    def testDifferentInterpretations(self):
        number = b'4321'
        ascii_number_value = int(number)
        ascii_string_value = number.decode('ascii')
        unsigned_int_value = int.from_bytes(number, byteorder='little')
        number = memoryview(number)

        # None is not technically valid, but we're not using the
        # record_path here. It's metadata for a Series record to use.
        # While it's possible to use an If record outside of a series,
        # it's not useful.
        record = R.If(
                lambda root, current: root,
                lambda value: 
                    R.AsciiInteger(4) if value == 0 else
                    R.FixedLengthString(4) if value == 1 else
                    R.Integer(4) if value == 2 else None)

        self.assertEqual(ascii_number_value, 
                record(Node(0), None)(number)[0])
        self.assertEqual(ascii_string_value, 
                record(Node(1), None)(number)[0])
        self.assertEqual(unsigned_int_value, 
                record(Node(2), None)(number)[0])

class SeriesTests(unittest.TestCase):
    # Start with the complicated tests. Make the simple tests to
    # diagnose errors in the complicated ones.


    # one basic series tests with a series of fixed length records
    def testBasicSeries(self):
        data = [b'01234', 
                int_to_bytes(4090, 2),
                b'foolish']
        expected_interpretation = {
            'num_1' : int(data[0]),
            'num_2' : int.from_bytes(data[1], byteorder='little'),
            # Note, there's a difference between b'foolish', the raw
            # bytes that represent the string 'foolish', and
            # 'foolish', the actual string itself (stored in a
            # different way).
            'string' : 'foolish',
        }
        source = b''.join(data)
        record = R.Series(
                    num_1=R.AsciiInteger(5),
                    num_2=R.Integer(2),
                    string=R.FixedLengthString(7)
                )
        interpretation = tree_to_values(process_meta_record(source, record)[0])
        self.assertEqual(expected_interpretation, interpretation)

    def testBasicIf(self):
        data = [b'01234', 
                int_to_bytes(4090, 2),
                b'foolish']
        source = memoryview(b''.join(data))
        expected_interpretation = {
                    'num' : int(data[0]),
                    'plain_bytes' : data[1],
                    'string' : data[2].decode('ascii'),
                }
        record = R.Series(
                    num=R.AsciiInteger(5),
                    plain_bytes=R.If(
                        lambda root, _: root['num'],
                        lambda value: 
                            R.PlainBytes(2) if value == 1234 else 
                            R.Integer(2)),
                    string=R.FixedLengthString(7)
                )
        interpretation = tree_to_values(process_meta_record(source, record)[0])
        self.assertEqual(expected_interpretation, interpretation)

    # wanna test references to parents in if records
    def testParentReferenceInSeries(self):
        data = [b'01234', 
                int_to_bytes(4090, 2),
                b'foolish']
        source = memoryview(b''.join(data))
        expected_interpretation = {
                    'num' : int(data[0]),
                    'rest' : {
                        'plain_bytes' : data[1],
                        'string' : data[2].decode('ascii'),
                    }
                }
        record = R.Series(
                    num=R.AsciiInteger(5),
                    rest=R.Series(
                        plain_bytes=R.If(
                            lambda root, _: root['num'],
                            lambda value:
                                R.PlainBytes(2) if value == 1234 else
                                R.Integer(2)), 
                        string=R.FixedLengthString(7)),
                    )
        #interpretation = process_meta_record(source, record)[0]
        interpretation = tree_to_values(process_meta_record(source, record)[0])
        self.assertEqual(expected_interpretation, interpretation)

class LargeMetaRecordTests(unittest.TestCase):
    def testFile12(self):
        # Just reading the primary header and secondary header. Extra
        # byte to test that correct number of bytes is consumed by
        # record function.
        orbit_params_length = 28 + 1
        with open(sample_data_dir + "/FILE_12", 'rb') as f:
            data = f.read(orbit_params_length)

        record = R.Series(
            primary_type=R.FixedLengthString(12),
            remaining_length=R.AsciiInteger(8),
            secondary_header=R.Series(
                secondary_type=R.Integer(2),
                remaining_length=R.Integer(2),
                orbit_number=R.Integer(2),
                annotation_block=R.Series(
                    data_class=R.Integer(1),
                    remaining_length=R.Integer(1),
                    label=R.PlainBytes(0),
                )))

        expected_interpretation = {
            'primary_type' : 'NJPL1I000104',
            'remaining_length' : 520,
            'secondary_header' : {
                'secondary_type' : 1,
                'remaining_length' : 4,
                'orbit_number' : 376,
                'annotation_block' : {
                    'data_class' : 1,
                    'remaining_length' : 0,
                    'label' : b'',
                },
            }
        }


        interpretation, remaining_source = process_meta_record(data, record)
        interpretation = tree_to_values(interpretation)

        self.assertEqual(len(remaining_source), 1)
        self.assertEqual(interpretation, expected_interpretation)



unittest.main()

