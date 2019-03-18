from attrs_structs import RecordTypes as R

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

def file_12(source, root_record):
    pass

def file_13(source, root_record):
    pass

# absolute pathing is a bitch. Perhaps some relative pathing would be
# really helpful. I could give both the root record and the sibling
# record and include a parent reference as '..'.
def file_15(source, root_record=None):
    def rest_bytes(source, root_record):
        return R.PlainBytes(
                root_record['remaining_length'])(source, root_record)

    basic_logical_record = R.Series(
            record_type=R.PlainBytes(12),
            remaining_length=R.AsciiInteger(8),
            the_rest=rest_bytes)

    def data_block(source, root_record):
        info = root_record.root['secondary_header']['annotation_block']['annotation_label']
        num_lines = info['line_count']
        line_length = info['line_length']
        single_line = R.PlainBytes(line_length)
        length = num_lines * line_length
        #data, rest = R.PlainBytes(length)(source)
        data, rest = R.List(num_lines*[single_line])(source)

        # page 51 of F-BIDR document has more information. left/right
        # looking matters, because it determines interpretation of the
        # offset and pointer.
        def clean_line(source, root_record=None):
            offset_to_first = root_record.root['offset_to_first']
            pointer_to_last = root_record.root['pointer_to_last']
            return list(source[offset_to_first:pointer_to_last]), bytes()

        line = R.Series(
            offset_to_first = R.Integer(2),
            pointer_to_last = R.Integer(2),
            line=clean_line
        )

        lines = [line(data[i])[0] for i in range(num_lines)]
        #lines = [line(data[i : i + line_length])[0]
                #for i in range(num_lines)]
        return lines, rest

    lrec = R.Series(
        primary_type=R.FixedLengthString(12),
        remaining_length=R.AsciiInteger(8),
        secondary_header=R.Series(
            secondary_type=R.Integer(2),
            remaining_length=R.Integer(2),
            orbit_number=R.Integer(2),
            annotation_block=R.Series(
                data_class=R.Integer(1),
                remaining_length=R.Integer(1),
                annotation_label=R.Series(
                    line_count=R.Integer(2),
                    line_length=R.Integer(2),
                    the_rest=R._FigureOutLater(
                    lambda r, c: c['..']['remaining_length'] - 4),
                ),
            ),
        ),
        data_block=data_block,
    )


    # There's more than 32 million logical records in file_15.
    def count_logical_recs(source):
        start = 0
        records = 0
        while start < len(source):
            label_offset = start = 12
            length_bytes = source[label_offset:label_offset+8]
            length = R.AsciiInteger(8)(length_bytes)[0]
            print(f'record {records}')
            start = start + length
            records += 1

    # There's more than 32 million logical records in file_15.
    def slow_count_logical_recs(source):
        records = 0
        remaining_source = source
        while len(remaining_source) > 0:
            _, remaining_source = basic_logical_record(remaining_source)
            print(f'record {records}')
            records += 1





    #first_record = basic_logical_record(
    return lrec(source)

with open("FILE_15", 'rb') as f:
    contents = f.read()
    records = []
    rest = memoryview(contents)
    for i in range(5000):
        value, rest = file_15(rest)
        records.append(value)

#file_16 = R.Series(

# NOTE: File 15 has more than one logical record. It's a series of
# logical records.

# TODO:
# - Where to find the orientation of an image?
#   - found it in per-orbit parameters. See if you can find another
#     source that's in FILE_15 instead of reaching for another file.
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
