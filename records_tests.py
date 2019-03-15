import unittest
from attrs_structs import RecordTypes as R
import random

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
            the_bytes = number.to_bytes(4, 'little', signed=False)
            self.assertEqual(int_record(the_bytes), (number, b''))

        int_record = R.Integer(5, signed=True)
        random_numbers = [random.randrange(-256**4, 256**4)  for x in range(10)]
        for number in random_numbers:
            the_bytes = number.to_bytes(5, 'little', signed=True)
            self.assertEqual(int_record(the_bytes), (number, b''))

class IfTests(unittest.TestCase):
    def testDifferentInterpretations(self):
        number = b'4321'
        ascii_number_value = int(number)
        ascii_string_value = number.decode('ascii')
        unsigned_int_value = int.from_bytes(number, byteorder='little')

        # None is not technically valid, but we're not using the
        # record_path here. It's metadata for a Series record to use.
        # While it's possible to use an If record outside of a series,
        # it's not useful.
        record = R.If(None, lambda value: 
                R.Ascii_integer(4) if value == 0 else
                R.Fixed_length_string(4) if value == 1 else
                R.Integer(4) if value == 2 else None)

        self.assertEqual((ascii_number_value, b''), record(number, 0))
        self.assertEqual((ascii_string_value, b''), record(number, 1))
        self.assertEqual((unsigned_int_value, b''), record(number, 2))



unittest.main()

