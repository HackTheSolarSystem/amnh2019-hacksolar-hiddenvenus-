from attrs_structs import RecordTypes as R
from attrs_structs import tree_to_values


tdb_seconds = R.Float('double')
wall_clock_time = R.FixedLengthString(19)
vax_int = R.Integer(4)
sclk_time = R.FixedLengthString(15)
vbf85_coord = R._FigureOutLater(4)

annotation_labels = {
    'image-data' : R.Series(
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
    'processing/monitor' : R._FigureOutLater(7),
    'radiometer' : R.Series(
        scet=R.Float('double'),
        lat_q1=R.Float('single'),
        lon_q2=R.Float('single'),
        incidence_angle_q3=R.Float('single'),
        terrain_elevation_q4=R.Float('single'),
        spacecraft_pos=R.List(3*[R.Float('single')]),
        receiver_gain=R.Float('single'),
        receiver_temp=R.Float('single'),
        signal_sensor_temp_coefs=R.List(3*[R.Float('single')]),
        sensor_input_noise_temp=R.Float('single'),
        cable_segment_temps=R.List(5*[R.Float('single')]),
        cable_segment_losses=R.List(5*[R.Float('single')]),
        atmospheric_emission_temp=R.Float('single'),
        atmospheric_attentuation_factor=R.Float('single'),
        cold_sky_reference_temp=R.Float('single'),
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
        orbit_semi_major_axis=R.Float('double'),
        orbit_eccentricity=R.Float('double'),
        # degrees
        orbit_inclination_angle=R.Float('double'),
        # degrees
        lon_ascending_node=R.Float('double'),
        arg_periapsis=R.Float('double'),
        # seconds
        orbit_period=R._FigureOutLater(4),
        reference_sclk_factor=R.FixedLengthString(13),
        conversion_slope=R.FixedLengthString(12),
        intercept_coef=R.FixedLengthString(19),
        correction_factor=R.FixedLengthString(6),
        projection_burst_counters=R.Series(
            first_oblique=vax_int,
            last_oblique=vax_int,
            first_sinusoidal=vax_int,
            last_sinusoidal=vax_int,
        ),
        projection_params=R.Series(
            projection_reference_lon=R._FigureOutLater(4),
            burst_counter=vax_int,
            time_crosses_85_deg=R.Float('double'),
        ),
        # They're in VBF85 coords. Not sure what is.
        axis_coords=R.Series(
            x=R.List(3*[vbf85_coord]),
            y=R.List(3*[vbf85_coord]),
            z=R.List(3*[vbf85_coord]),
        ),
        # Not sure what type is. Could be single.
        lon_oblique_sinusoidal_origin=R._FigureOutLater(4),
        oblique_sinusoidal_start=vax_int,
        oblique_sinusoidal_stop=vax_int,
        blanks=R.PlainBytes(512-307),
    ),
    #'image-data' : R.If(
        #lambda root, current:
            #root['secondary_header']['annotation_block']['label'],
        #lambda v:
            #R.List(v['line_count'].value * 
                #[R._FigureOutLater(v['line_length'].value)])),
    'radiometer' : R._FigureOutLater(12),
}

def image_data_block(source, root_record, current):
    info = root_record['secondary_header']['annotation_block']['label']
    num_lines = info['line_count'].value
    line_length = info['line_length'].value

    def clean_line(source, root_record, current):
        offset = current['offset_to_first'].value
        pointer = current['pointer_to_last'].value
        valid_pixels = bytes(source[offset:pointer])
        # the -4 is for the two integers prior, as they're counted as
        # part of the line length.
        return list(valid_pixels), source[line_length - 4:]

    line = R.Series(
        offset_to_first = R.Integer(2),
        pointer_to_last = R.Integer(2),
        line=clean_line
    )

    image = R.List(num_lines*[line])
    value, rest = image(source)
    return value.value, rest

data_blocks['image-data'] = image_data_block

logical_record = R.Series(
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
                    annotation_labels['per-orbit'] if value == 1 else
                    annotation_labels['image-data'] if 
                        value in [2, 34, 66, 98] else
                    annotation_labels['processing/monitor'] if
                        value in [4, 68, 16] else
                    annotation_labels['radiometer']))),
    data_block=R.If(
        lambda root, current:
            root['secondary_header']['annotation_block']['data_class'],
        lambda value:
            data_blocks['per-orbit'] if value == 1 else
            data_blocks['image-data'] if 
                value in [2, 34, 66, 98] else
            data_blocks['processing/monitor'] if
                value in [4, 68, 16] else
            data_blocks['radiometer']))

# record representing a physical record. Physical records are always
# 32500 bytes long. If the information they contain was less than
# this, then the info is padded with the '^' character. All files
# should be integer multiples of 32500 bytes in size. This is true for
# orbit 376's (F_0376) files at least, as I checked.
def physical_record(source, root_record=None):
    value, rest = R.PlainBytes(32500)(source, root_record)
    return value.rstrip(b'^'), rest

def physical_records(source, root_record=None):
    rest = source
    records = []
    while len(rest) > 0:
        value, rest = physical_record(rest, root_record)
        records.append(value)

    return records, rest

def count_logical_recs(source):
    start = 0
    records = 0
    while start < len(source):
        label_offset = start + 12
        if not bytes(source[start:label_offset]).startswith(b"NJPL"):
            break
        length_bytes = source[label_offset:label_offset+8]
        length = R.AsciiInteger(8)(length_bytes)[0]
        #print(f'record {records}')
        start = label_offset + 8 + length
        records += 1

    return records

# NOTE: File 15 has more than one logical record. It's a series of
# logical records.
with open("sample-data/FILE_15", 'rb') as f:
    contents = f.read()
    records = []
    rest = memoryview(contents)
    num_records = count_logical_recs(rest)
    for i in range(num_records):
        value, rest = logical_record(rest)
        records.append(value)

    records = [tree_to_values(r) for r in records]

# File 15 notes:
# - For the 1st 1000 logical records of the test FILE_15, all the line
#   lengths are same, some have different line counts. So sounds safe
#   to assume that all logical records are same width.
# - Where to find the orientation of an image?
#   - found it in per-orbit parameters (file 12). See if you can find
#     another source that's in FILE_15 instead of reaching for another
#     file.
# - Some records had an offset and pointer that had to have been
#   wrong. Like, their values were just too large. What happened?
#       - I saw that the first two 16-bit values in each line are def
#         16 bit unsigned integers. I saw also that I have to
#         interpret these values a little differently for left/right
#         facing images. None of this accounts for the pointer and
#         offset being larger than the line length. Nor does it
#         account for the line length being larger than it apparently
#         should be
# - Do we interpret offset and pointer for left and right pointing
#   images diffrently?
#       - Yup. There's an example on page 51. 
#           - Left looking images: For a left looking image, the
#             offset is offset from the first pixel to the first valid
#             pixel. The pointer is the offset from the first pixel to
#             the last valid pixel (exclusive end).
#           - Right looking images: The same as left looking image but
#             with 4 added to both offset and pointer.
