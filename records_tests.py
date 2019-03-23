import unittest
from attrs_structs import (RecordTypes as R,
        process_meta_record,
        tree_to_values,
        Node)
import random

sample_data_dir = 'sample-data'
def translate_float(hex_string):
    the_bytes = bytes.fromhex(hex_string)
    if len(the_bytes) == 4:
        return R.Float('single')(the_bytes)[0]
    elif len(the_bytes) == 8:
        return R.Float('double')(the_bytes)[0]
    else:
        raise ValueError("Passed too few or too many bytes.")

def translate_int(int_string):
    the_bytes = bytes.fromhex(int_string)
    return R.Integer(len(the_bytes))(the_bytes)[0]

def translate_bytes(hex_string):
    return bytes.fromhex(hex_string)

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

# Other record types. Stand-ins for some things.
tdb_seconds = R.Float('double')
wall_clock_time = R.FixedLengthString(19)
vax_int = R.Integer(4)
sclk_time = R.FixedLengthString(15)

class LargeMetaRecordTests(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.maxDiff = None

    annotation_labels = {
        'image data' : R.Series(
            line_count=R.Integer(2),
            line_length=R.Integer(2),
            proj_origin_lat=R.Float('single'),
            proj_origin_lon=R.Float('single'),
            reference_lat=R.Float('single'),
            reference_lon=R.Float('single'),
            reference_offset_lines=R.Integer(4),
            reference_offset_pixels=R.Integer(4),
            burst_counter=R.Integer(4),
            nav_unique_id=R.FixedLengthString(32),
        ),
        'per-orbit' : R.PlainBytes(0),
        'processing/monitor parameters' : R._FigureOutLater(7),
        'radiometer' : R.Series(
            scet=R.Float('double'),
            lat_q1=R.Float('single'),
            lon_q2=R.Float('single'),
            incidence_angle_q3=R.Float('single'),
            terrain_elevation_q4=R.Float('single'),
            spacecraft_pos=R.List(3*[R.Float('single')]),
            #receiver_gain=R.Float('single'),
            #receiver_temp=R.Float('single'),
            #signal_sensor_temp_coefs=R.List(3*[R.Float('single')]),
            #sensor_input_noise_temp=R.Float('single'),
            #cable_segment_temps=R.List(5*[R.Float('single')]),
            #cable_segment_losses=R.List(5*[R.Float('single')]),
            #atmospheric_emission_temp=R.Float('single'),
            #atmospheric_attentuation_factor=R.Float('single'),
            #cold_sky_reference_temp=R.Float('single'),
            # The diagram from the book is misleading. There are no
            # blanks here up to 112. The file itself shows it.
            good_lord_im_done=R.PlainBytes(88 - 36),
        )
    }

    data_blocks = {
        'per-orbit' : R.Series(
            orbit_number=vax_int,
            mapping_start=tdb_seconds,
            mapping_stop=tdb_seconds,
            total_bursts=vax_int,
            product_id=R.FixedLengthString(9),
            volume_id=R.FixedLengthString(6),
            processing_start=wall_clock_time,
            number_of_looks=vax_int,
            orbit_look_direction=vax_int,
            nav_unique_id=R.FixedLengthString(32),
            predicted_periapsis_time_sclk=sclk_time,
            predicted_periapsis_time_tdb=tdb_seconds,
            #orbit_semi_major_axis=R.Float('double'),
            #orbit_eccentricity=R.Float('double'),
            ## degrees
            #orbit_inclination_angle=R.Float('double'),
            ## degrees
            #lon_ascending_node=R.Float('double'),
            #arg_periapsis=R.Float('double'),
            ## seconds
            #orbit_period=R._FigureOutLater(4),
            #reference_sclk_factor=R.FixedLengthString(13),
            #conversion_slope=R.FixedLengthString(12),
            #intercept_coef=R.FixedLengthString(19),
            #correction_factor=R.FixedLengthString(6),
            #projection_burst_counters=R.Series(
                #first_oblique=vax_int,
                #last_oblique=vax_int,
                #first_sinusoidal=vax_int,
                #last_sinusoidal=vax_int,
            #),
            #projection_params=R.Series(
                #projection_reference_lon=R._FigureOutLater(4),
                #burst_counter=vax_int,
                #time_crosses_85_deg=R.Float('double'),
            #),
            # They're in VBF85 coords. Not sure what is.
            #axis_coords=R.Series(
                #x=R.List(3*R._FigureOutLater(4)),
                #y=R.List(3*R._FigureOutLater(4)),
                #z=R.List(3*R._FigureOutLater(4)),
            #),
            # Not sure what type is. Could be single.
            #lon_oblique_sinusoidal_origin=R._FigureOutLater(4),
            #oblique_sinusoidal_start=vax_int,
            #oblique_sinusoidal_stop=vax_int,
            #blanks=R.PlainBytes(512-307),
            good_lord_im_done=R.PlainBytes(512 - 121),
        ),
        'image data' : R.If(
            lambda root, current:
                root['secondary_header']['annotation_block']['label'],
            lambda v:
                R.List(v['line_count'].value * 
                    [R._FigureOutLater(v['line_length'].value)])),
        'radiometer' : R._FigureOutLater(12),
    }

    # Assumes only per-orbit and radiometer files.
    # orbit data is file_12 and radiometer parameters is file_17
    logical_record_12_17 = R.Series(
        primary_type=R.FixedLengthString(12),
        remaining_length=R.AsciiInteger(8),
        secondary_header=R.Series(
            secondary_type=R.Integer(2),
            remaining_length=R.Integer(2),
            orbit_number=R.Integer(2),
            annotation_block=R.Series(
                data_class=R.Integer(1),
                remaining_length=R.Integer(1),
                label=R.If(
                    lambda root, current:
                        current['data_class'],
                    lambda value:
                        LargeMetaRecordTests.annotation_labels['per-orbit'] if value == 1 else
                        LargeMetaRecordTests.annotation_labels['radiometer']))),
        data_block=R.If(
            lambda root, current:
                root['secondary_header']['annotation_block']['data_class'],
            lambda value:
                LargeMetaRecordTests.data_blocks['per-orbit'] if value == 1 else
                LargeMetaRecordTests.data_blocks['radiometer']))

    def testFile12Start(self):
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

    def testFile12Full(self):
        with open(sample_data_dir + "/FILE_12", 'rb') as f:
            data = f.read()

        expected_interpretation = {
            # bytes 0-11
            'primary_type' : 'NJPL1I000104',
            # bytes 12-19
            'remaining_length' : 520,
            'secondary_header' : {
                # bytes 20-21
                'secondary_type' : translate_int('0100'),
                # bytes 22-23
                'remaining_length' : translate_int('0400'),
                # bytes 24-25
                'orbit_number' : translate_int('7801'),
                'annotation_block' : {
                    # byte 26
                    'data_class' : translate_int('01'),
                    # byte 27
                    'remaining_length' : 0,
                    'label' : b'',
                },
            },
            'data_block' : {
                # bytes 28-31
                'orbit_number' : translate_int('7801 0000'),
                # bytes 32-39
                'mapping_start' : translate_float('8bce b6dc de5c d913'),
                # bytes 40-47
                'mapping_stop' : translate_float('8bce 70dc 59b4 5820'),
                # bytes 48-51
                'total_bursts' : translate_int('8a14 0000'),  
                # bytes 52-60
                'product_id' : 'F00376.03',
                # bytes 61-66
                'volume_id' : 'F01781',
                # bytes 67-85
                'processing_start' : '90/282-07:34:02.030',
                # bytes 86-89
                'number_of_looks' : translate_int('0000 0000'),
                # bytes 90-93
                'orbit_look_direction' : translate_int('0000 0000'),
                # bytes 94-125
                'nav_unique_id' : 'ID = M0257.22-10                ',
                # bytes 126-140
                'predicted_periapsis_time_sclk' : '00723798.42.8.0',
                # bytes 141-148
                'predicted_periapsis_time_tdb' : translate_float('8bce 8ddc 5744 54a8'),
                ## bytes 149-156
                #'orbit_semi_major_axis' : translate_float('1f4c 8f12 e6ad 4c7b'),
                ## bytes 157 (0x9d)-164 (0xa4)
                #'orbit_eccentricity' : translate_float('c83f e952 aed7 a6b7'),
                ## degrees
                ## bytes 165 (0xa5)-173 (0xac)
                #'orbit_inclination_angle' : translate_float('c043 a3d0 ca01 39e8'),
                ## degrees
                ## bytes 173 (0xad)-181 (0xb4)
                #'lon_ascending_node' : R.Float('double'),
                #'arg_periapsis' : R.Float('double'),
                ## seconds
                #'orbit_period' : R._FigureOutLater(4),
                #'reference_sclk_factor' : R.FixedLengthString(13),
                #'conversion_slope' : R.FixedLengthString(12),
                #'intercept_coef' : R.FixedLengthString(19),
                #'correction_factor' : R.FixedLengthString(6),
                #'projection_burst_counters' : R.Series(
                    #'first_oblique' : vax_int,
                    #'last_oblique' : vax_int,
                    #'first_sinusoidal' : vax_int,
                    #'last_sinusoidal' : vax_int,
                #),
                #'projection_params' : R.Series(
                    #'projection_reference_lon' : R._FigureOutLater(4),
                    #'burst_counter' : vax_int,
                    #'time_crosses_85_deg' : R.Float('double'),
                #),
                ## They're in VBF85 coords. Not sure what is.
                #'axis_coords' : R.Series(
                    #'x' : R.List(3*[R._FigureOutLater(4)]),
                    #'y' : R.List(3*[R._FigureOutLater(4)]),
                    #'z' : R.List(3*[R._FigureOutLater(4)]),
                #),
                ## Not sure what type is. Could be single.
                #'lon_oblique_sinusoidal_origin' : R._FigureOutLater(4),
                #'oblique_sinusoidal_start' : vax_int,
                #'oblique_sinusoidal_stop' : vax_int, 
                'good_lord_im_done' : translate_bytes("""
                    1f4c 8f12 e6ad 4c7b c83f e952 aed7 a6b7 c043 a3d0
                    ca01 39e8 9644 4579 8d6b c567 1644 d446 264a d0b6
                    0b46 0a51 2020 3732 3235 3030 3a30 303a 3036 302e
                    3636 3636 3139 3036 3339 302d 3235 372f 3138 3a35
                    313a 3230 2e34 3731 3537 2e31 3832 0100 0000 1501
                    0000 4500 0000 8a14 0000 a444 8caf a400 0000 8bce
                    b1dc d8d4 52ed 24be 720b 8abe 276c 7f40 6e35 5c40
                    1a3d 02c0 ab80 0000 0000 0240 6719 5b40 d48e a03e
                    1de6 f1c3 3d4c aac3 ebfc 8bce b6dc 847c 4cc5 8bce
                    aedc fe9d 9f45 0000 0000 0000 0000 0000 0000 0000
                    0000 0000 0000 0000 0000 0000 0000 0000 0000 0000
                    0000 0000 0000 0000 0000 0000 0000 0000 0000 0000
                    0000 0000 0000 0000 0000 0000 0000 0000 0000 0000
                    0000 0000 0000 0000 0000 0000 0000 0000 0000 0000
                    0000 0000 0000 0000 0000 0000 0000 0000 0000 0000
                    0000 0000 0000 0000 0000 0000 0000 0000 0000 0000
                    0000 0000 0000 0000 0000 0000 0000 0000 0000 0000
                    0000 0000 0000 0000 0000 0000 0000 0000 0000 0000
                    0000 0000 0000 0000 0000 0000 0000 0000 0000 0000
                    0000 0000 0000 0000 0000 00
                """)
            }
        }

        record = LargeMetaRecordTests.logical_record_12_17
        interpretation, remaining_source = process_meta_record(data, record)
        interpretation = tree_to_values(interpretation)

        self.assertEqual(expected_interpretation, interpretation)

    def testFile17Full(self):
        with open(sample_data_dir + "/FILE_17", 'rb') as f:
            data = f.read()

        expected_interpretation = {
            # bytes 0-11
            'primary_type' : 'NJPL1I000104',
            # bytes 12-19
            'remaining_length' : 108,
            'secondary_header' : {
                # bytes 20-21
                'secondary_type' : 8,
                # bytes 22-23
                'remaining_length' : translate_int('5c00'),
                # bytes 24-25
                'orbit_number' : translate_int('7801'),
                'annotation_block' : {
                    # byte 26
                    'data_class' : 8,
                    # byte 27
                    'remaining_length' : translate_int('58'),
                    'label' : {
                        # bytes 28 - 35
                        'scet' : translate_float('8bce b6dc 3f4c 6330'),
                        # bytes 36 - 39
                        'lat_q1' : translate_float('b043 63c6'),
                        # bytes 40 - 43
                        'lon_q2' : translate_float('1944 acb2'),
                        # bytes 44 - 47
                        'incidence_angle_q3' : translate_float('3342 5b88'),
                        # bytes 48 - 51
                        'terrain_elevation_q4' : translate_float('2b44 01e0 '),
                        'spacecraft_pos' : [
                            # bytes 52 - 55
                            translate_float('01ca 4824 '),
                            # bytes 56 - 59
                            translate_float('dbc9 57c7'),
                            # bytes 60 - 63
                            translate_float('fe4b 7260'),
                        ],
                        'good_lord_im_done' : translate_bytes("""
                            8040 0000 9044 e1d8 813a 875c 4540 4a73
                            7d44 9ac5 f244 c5b8 a944 a1c9 a344 c17a
                            9c44 6b62 8c44 9bbd 8c44 9bbd 8f42 1eb8
                            7640 50cd 
                        """)
                    }
                },
            },
            # bytes 140 - 151
            'data_block' : translate_bytes("""
                3c07 2806 0145 3069 0145 4493 
            """)
        }

        record = LargeMetaRecordTests.logical_record_12_17
        interpretation, remaining_source = process_meta_record(data, record)
        print(interpretation)
        interpretation = tree_to_values(interpretation)

        self.assertEqual(expected_interpretation, interpretation)


unittest.main()
