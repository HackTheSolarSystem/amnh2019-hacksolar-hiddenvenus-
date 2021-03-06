from attrs_structs import RecordTypes as R
from attrs_structs import tree_to_values

# TODO: 
# - Translate the times into python/earth times.
# - Build an index of longitudes + latitudes of the reference points
#   of each logical record in an image. At least for file 15. This
#   would allow you to focus on an arbitrary longitude latitude range
#   without having to worry about which orbit(s) cover it up front.
#   Helps keep storage use low, too.
tdb_seconds = R.Float('double')
wall_clock_time = R.FixedLengthString(19)
vax_int = R.Integer(4)
sclk_time = R.FixedLengthString(15)
vbf85_coord = R._FigureOutLater(4)

def complex_number(source, **kwargs):
    flt = R.Float('single')
    real, rest = flt(source)
    imag, rest = flt(rest)
    return complex(real, imag), rest

def byteArray(length):
    return lambda s, **rest: bytearray(s[:length]), s[length:]

annotation_labels = {
    'image-data' : R.Series(
        line_count=R.Integer(2),
        line_length=R.Integer(2),
        proj_origin_lat=R.Float('single'),
        proj_origin_lon=R.Float('single'),
        reference_lat=R.Float('single'),
        reference_lon=R.Float('single'),
        reference_offset_lines=R.Integer(4, signed=True),
        reference_offset_pixels=R.Integer(4, signed=True),
        burst_counter=R.Integer(4),
        nav_unique_id=R.FixedLengthString(32),
    ),
    'per-orbit' : R.PlainBytes(0),
    'processing/monitor' : R._FigureOutLater(7),
    'radiometer' : R.Series(
        scet=tdb_seconds,
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
        # This seems to be a typo. The binary data itself doesn't
        # contain enough space for this, and the graph of fields
        # doesn't contain this (page 43, BIDR report). And the byte
        # ranges are off for the losses. They go above 88 bytes, and
        # then back below it for atmospheric_emission_temp.
        #cable_segment_losses=R.List(5*[R.Float('single')]),
        atmospheric_emission_temp=R.Float('single'),
        atmospheric_attentuation_factor=R.Float('single'),
        # Same as for cable_segment_losses. Doesn't seem to actually
        # be there.
        #cold_sky_reference_temp=R.Float('single'),
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
        orbit_period=R.Float('single'),
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
            projection_reference_lon=R.Float('single'),
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
        lon_oblique_sinusoidal_origin=R.Float('single'),
        inverse_lat_oblique_sinusoidal_origin=R.Float('single'),
        oblique_sinusoidal_start=R.Float('double'),
        oblique_sinusoidal_stop=R.Float('double'),
        blanks=R.PlainBytes(512-307),
    ),
    'radiometer' : R._FigureOutLater(12),
    'processing' : R.Series(
        burst_counter=vax_int,
        burst_reference_time=tdb_seconds,
        burst_center_time=tdb_seconds,
        echo_delay_time=R.Float('single'),
        is_test=vax_int,
        is_anomaly=vax_int,
        is_error=vax_int,
        # TODO: This is a good candidate for an enumeration.
        projection=vax_int,
        craft_pos_j2000=R.List(3*[R.Float('single')]),
        craft_pos_vbf85=R.List(3*[R.Float('single')]),
        craft_velocity_j2000=R.List(3*[R.Float('single')]),
        craft_velocity_vbf85=R.List(3*[R.Float('single')]),
        craft_acceleration_j2000=R.List(3*[R.Float('single')]),
        craft_acceleration_vbf85=R.List(3*[R.Float('single')]),
        q1=R.Float('single'),
        q2=R.Float('single'),
        q3=R.Float('single'),
        q4=R.Float('single'),
        delta_q1=R.Float('single'),
        delta_q2=R.Float('single'),
        delta_q3=R.Float('single'),
        delta_q4=R.Float('single'),
        boresight_orientation_vme85=R.List(3*[R.Float('single')]),
        boresight_orientation_vbf85=R.List(3*[R.Float('single')]),
        # Parameter 42/300
        look_angle=R.Float('single'),
        done_for_now=R._FigureOutLater(1148 - 180),
        blanks=R.PlainBytes(1280 - 1148),
    )
}

# Multi-look image data, not single-look. I haven't found a
# single-look image yet.
# Done manually for speed.
def image_data_block(source, root_record, current):
    info = root_record['secondary_header']['annotation_block']['label']
    num_lines = info['line_count'].value
    line_length = info['line_length'].value
    lines = []
    rest = source

    for i in range(num_lines):
        line = rest[:line_length]
        rest = rest[line_length:]
        lines.append({
            'offset_to_first' : R.Integer(2)(line[:2])[0],
            'pointer_to_last' : R.Integer(2)(line[2:4])[0],
            'line' : bytearray(line[4:]),
        })

    return lines, rest

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

def count_logical_recs(source):
    start = 0
    records = 0
    prefix_length = 9
    primary_label_length = 12
    while start < len(source):
        check = source.startswith(b'NJPL1I000', start, start+12)
        if not check:
            break
        label_offset = start + primary_label_length
        length_bytes = source[label_offset:label_offset+8]
        length = R.AsciiInteger(8)(length_bytes)[0]
        start += 20 + length
        records += 1

    return records

def rearrange_logical_record(record):
    """Places the important information in easy-to-reach places."""
    new = { 
        '_' : record, 
        'data' : record['data_block'],
        'type' : record['secondary_header']['annotation_block']['data_class'],
    }
    new.update(record['secondary_header']['annotation_block']['label'])
    new.update(orbit_number=record['secondary_header']['orbit_number'])
    return new

def read_logical_records(source, number=None):
    """
    - source is a bytes object, or a filepath as string.
    - number is the number of records to read. If omitted, read as
      many records as possible.
    - This is not a record function. Think of it as a front-end to
      this whole file.
    """
    if isinstance(source, str):
        with open(source, 'rb') as f:
            contents = f.read()
            rest = memoryview(contents)
        max_records = count_logical_recs(contents)
    else:
        rest = memoryview(source)
        max_records = count_logical_recs(source)

    records = []
    to_read = (max_records if number is None 
                else min(number, max_records))

    new_start = 0
    for i in range(to_read):
        value, rest, new_start = logical_record(rest, start=new_start)
        records.append(value)

    records = [tree_to_values(r) for r in records]
    records = [rearrange_logical_record(r) for r in records]
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
#       - This went away after I re-did the attrs_structs work. They
#         all seem sensible now.
# - Do we interpret offset and pointer for left and right pointing
#   images diffrently?
#       - Yup. There's an example on page 51. 
#           - Left looking images: For a left looking image, the
#             offset is offset from the first pixel to the first valid
#             pixel. The pointer is the offset from the first pixel to
#             the last valid pixel (exclusive end).
#           - Right looking images: The same as left looking image but
#             with 4 added to both offset and pointer.
