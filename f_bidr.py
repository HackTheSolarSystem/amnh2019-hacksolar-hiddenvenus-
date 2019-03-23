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
    'radiometer' : R._FigureOutLater(12),
}

def image_data_block(source, root_record, current):
    info = root_record['secondary_header']['annotation_block']['label']
    num_lines = info['line_count'].value
    line_length = info['line_length'].value

    def pixels(source, root_record, current):
        num_pixels = line_length - 4
        the_pixels = bytes(source[:num_pixels])
        # the -4 is for the two integers prior, as they're counted as
        # part of the line length.
        return list(the_pixels), source[num_pixels:]

    line = R.Series(
        offset_to_first = R.Integer(2),
        pointer_to_last = R.Integer(2),
        line=pixels
    )

    image = R.List(num_lines*[line])
    #value, rest = image(source)
    #return value.value, rest
    return image(source)

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

# Jesus, there was some terrible fucking bug in here before. There's
# 5187 logical records in these files. Sigh. FILE_15 is 90 MB large,
# and I saw 30+ million logical records. That would mean each logical
# record is at most 3 bytes big. That should've sent huge alarm bells
# ringing. largest file I have is 99 MB large.
def count_logical_recs(source):
    start = 0
    records = 0
    prefix_length = 9
    primary_label_length = 12
    while start < len(source):
        check = source[start:start+12].startswith(b'NJPL1I000')
        if not check:
            break
        label_offset = start + primary_label_length
        length_bytes = source[label_offset:label_offset+8]
        length = R.AsciiInteger(8)(length_bytes)[0]
        start += 20 + length
        records += 1

    return records

def read_logical_records(source, number=None):
    """
    - source is a bytes object.
    - number is the number of records to read. If omitted, read as
      many records as possible.
    - This is not a record function. Think of it as a front-end to
      this whole file.
    """
    records = []
    rest = memoryview(source)
    max_records = count_logical_recs(source)
    to_read = (max_records if number is None 
                else min(number, max_records))

    for i in range(to_read):
        value, rest = logical_record(rest)
        records.append(value)

    records = [tree_to_values(r) for r in records]
    return records

# File 15 notes:
# - For the 1st 1000 logical records of the test FILE_15, all the line
#   lengths are same, some have different line counts. So sounds safe
#   to assume that all logical records are same width.
# - The offset and pointer in the first line of each image block (the
#   data block in each logical record) are copied from the 2nd line.
#   This is an error in the original Magellan work (page 49 of BIDR
#   book).
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
