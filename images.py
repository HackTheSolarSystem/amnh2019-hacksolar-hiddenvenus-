import numpy as np
import numpy.ma as ma
import imageio
import itertools
import math

from f_bidr import read_logical_records
import f_bidr
from f_bidr_data import get_orbit_file_path as orbit


f_bidr.build_mask = True

# NOTE: File 15 has more than one logical record. It's a series of
# logical records.
selected_orbits = [376, 382, 384, 386, 390]
selected_orbits = [orbit(i, "file_15") for i in selected_orbits]

def multiple_orbits(pixel_offsets):
    #selected_orbits = [orbit(i, 'file_15') 
                       #for i in [376, 382, 384, 386, 390]]
    #selected_orbits = [orbit(i, 'file_15') 
                       #for i in [382, 384, 386, 390]]
    selected_orbits = [orbit(i, 'file_15') for i in [382, 384]]
    data = [read_logical_records(o, 100) for o in selected_orbits]
    origin_lons = [o[0]['proj_origin_lon'] for o in data]
    #origin_pixels = [math.pi / 180 * l * 6051.8 for l in origin_lons]
    #least_pixels = min(origin_pixels)
    #pixel_offsets = [0, 20, 40, 60]
    #pixel_offsets = [round(p - least_pixels) for p in origin_pixels]
    #least_lon = min(origin_lons)
    #pixel_offsets = [round((l - least_lon) / 7.1016e-4) 
                     #for l in origin_lons]
    #pixel_offsets = [0, 100]
    print(origin_lons)
    #print(pixel_offsets)
    for image_data, offset in zip(data, pixel_offsets):
        for record in image_data:
            record['reference_offset_pixels'] += offset

    records = list(itertools.chain.from_iterable(data))

    biggun = image_stitch(records, None, None)
    #pieces = slice_image(biggun, 10)
    #for i, piece in enumerate(pieces):
        #imageio.imwrite(f'{i}-mult-orbit-test-{pixel_offsets[1]}.png', piece)
    imageio.imwrite(f'mult-orbit-test-{pixel_offsets[1]}.png', biggun)

    return biggun, records

def slice_image(image, slices=3):
    height = image.shape[0]
    divide_into = slices
    start = 0
    count = 0
    piece_size = height // divide_into
    pieces = []
    while start < height:
        end = start + piece_size
        pieces.append(image[start:end])
        start = end
        count += 1

    return pieces

def process_file(filepath, savepath, slices=3):
    with open(filepath, 'rb') as f:
        contents = f.read()
        #records = read_logical_records(contents, 250)
        records = read_logical_records(contents)

    #biggun = image_stitch(records, None, None)
    #imageio.imwrite(savepath, biggun)

    biggun = image_stitch(records, None, None)
    height = biggun.shape[0]
    divide_into = slices
    start = 0
    count = 0
    piece_size = height // divide_into
    while start < height:
        end = start + piece_size
        imageio.imwrite(f'{count}-{savepath}', biggun[start:end])
        start = end
        count += 1

# TODO: Don't think this works for right-look images. The pointer and
# offset are relative to the east-most pixel for those.
def make_mask(offset, pointer, length):
    return np.array([True]*offset + [False]*(pointer - offset) + 
            [True]*(length - pointer))

# TODO: Some files, such as MG_4002/F0382_4/FILE_13, start from a low
# line offset and proceed to a larger one. The final product shows
# slices that are out of order. The image "top" (it's a slice with
# rounded end suggesting the edge of the planet), is at the least line
# offset, which is negative.

# Notes on array/image geometry:
# For a numpy array:
# - Earlier rows are the top of the image.
# - Earlier columns are the left of the image.
#
# For BIDR records:
# - pixels earlier in a data row have a smaller pixel offset.
# - pixels later in a logical record have a later pixel offset.
# - Earlier records have larger line offsets. (for file_15's)
# - Later records have smaller line offsets. (for file_15's)
#
# For file_15's, the satellite travels from north to south, and
# somewhat east over time. Higher line offsets mean north, lower
# offsets mean south.
# 
# - The image arrays are created from the pixel rows in the logical
#   records. Each individual image array contains rows in the order
#   that the logical record contains them.
# - When concatenating arrays, earlier arrays have lower indexes.  So
#   the 1st row of the 1st array is the top row of the image.  And
#   thus the 1st line of the 1st record is the top row of the image.
#   The last line of the last record is the bottom row of the image.
#   The image needs to be tall enough to accomodate:
#   - max of:
#       - height of 1st record
#       - offset range
#   - height of last picture, whose 1st row is on the row of smallest
#     offset.
def image_stitch(records, sort_by, save_path=None):
    pixel_offsets = [r['reference_offset_pixels'] for r in records]
    line_offsets = [r['reference_offset_lines'] for r in records]
    left_most = min(pixel_offsets)
    right_most = max([r['reference_offset_pixels'] + r['line_length'] for r in records])
    top_most = max(line_offsets)
    bottom_most = min([r['reference_offset_lines'] - r['line_count'] for r in records])
    min_pixels = left_most
    max_lines = top_most
    #min_pixels, max_pixels = min(pixel_offsets), max(pixel_offsets)
    #min_lines, max_lines = min(line_offsets), max(line_offsets)

    # Width of master picture:
    # - Lower pixel offsets are west (left in the logical records and
    #   master picture), higher pixel offsets are east (right).
    # - The left-most pixel of the master picture is the 1st pixel of
    #   the west-most logical record. Thus the offset of this pixel is
    #   the offset of the west-most logical record.
    # - The right-most pixel of the master picture is the last pixel
    #   of the logical record whose width + pixel offset is highest.
    #   For now, I've assumed a constant width of 512 (which has so
    #   far been true), which makes this operation simpler: the last
    #   pixel of the east-most logical record
    # TODO: 512 assumes constant width of each image piece. Otherwise
    # I'll have to do something similar for this as I did for the
    # max_height.
    #max_width = max_pixels - min_pixels + 512
    max_width = right_most - left_most 

    # Height of master picture:
    # - The following is true only for file_15s.
    # - The 1st (top) pixel in the master picture has the highest line
    #   offset. This is the 1st line of pixels of the top (north) most
    #   record.
    # - The last (bottom) row of pixels in the master picture is the
    #   last line from the record whose line offset + height is
    #   greatest. Height is not generally constant among records. But
    #   line offset monotonically decreases for file_15 records, and
    #   I've yet to see image overlaps. For an image that's not the
    #   last to have the lowest pixel, the height of the not-last
    #   image has to reach far enough down to pass down all other
    #   image records between this not-last record and the last one.
    #   line offset. So this should be the last image, plus that
    #   image's height.
    bottom_image = min(records, key=lambda r:r['reference_offset_lines'])
    bottom_image_lines = bottom_image['line_count']
    # I know ahead of time that the last image record should have the
    # largest line offset. I wanna know the size of image that would
    # appear at the highest offset.
    #max_height = max_lines - min_lines + bottom_image_lines
    max_height = top_most - bottom_most
    #max_lines = max_height
    print(f'Attempting shape: {max_height}x{max_width}')
    master_picture = np.zeros((max_height, max_width), dtype=np.uint8)
    record_num = 0
    for record in records:
        image = record['data']
        pixel_shift = record['reference_offset_pixels']
        line_shift = record['reference_offset_lines']
        # The 0th column is the pixel most to the left, thus
        # min_pixels should map to index 0
        height, width = image.shape
        left = pixel_shift - min_pixels
        # The 1st line in an image becomes the top of the image. Thus
        # the 1st line of these magellan records is their top. The 1st
        # (top) line will go in a smaller index, lower lines will go
        # in higher indexes.
        # Higher line offsets should be the top of the image. Highest
        # offset should map to row 0. Lower line offsets should map to
        # higher indexes. So I negated the shift (so that lower
        # offsets are now higher numbers) and to make the highest
        # line offset 0, I added max_lines.
        top = -line_shift + max_lines
        #master_picture[top:top + height, left:left + width] = image
        # Changing this a little so that if image pixels are 0 and the
        # master picture is non-zero in that location, I keep the
        # non-zero value.
        new0 = image == 0
        old_region = master_picture[top:top + height, left:left + width]
        master_picture[top:top + height, left:left + width] = old_region * new0 + image * (~new0)
    return master_picture

# Image questions:
# - What's the orientation of the image lines? I know that the first
#   pixel of each line is west-most. However, suppose that the
#   satellite is travelling from south to north, and the 1st image
#   line is the first series of pixels scanned (making them
#   south-most), and the last line is north-most. That makes the photo
#   kinda upside-down. I can't assume that just because the 1st pixel
#   is west most that it is also south-most. In fact, whether it is
#   south or north-most may depend on the orbit.
#       - Page 110 may have relevant info on this. Says how the
#         spacecraft moved during left-looking and right-looking
#         orbits. What are the ascending and descending swaths, and
#         how do we tell if we're in a descending or ascending swath?
#         Do I need to look at all the logical records and look at
#         their reference lat+lon to figure out the direction of the
#         movement?
#       - I looked at just the reference latitudes for the 1st 500
#         logical records of sample FILE_15. The latitudes seemed in
#         no particular order. I figured there'd be a steady increase
#         or decrease. I tried sorting them by latitutde. Really no
#         particular order. Not sure what to make of that. Perhaps one
#         orbit goes around the planet several times. Perhaps each
#         FILE_15 loops around the planet many times, and the readings
#         are timed so that a single location is focused upon? That
#         doesn't seem likely; it shounds like a bad idea, and the
#         range of lats is around 50 deg. That's kinda big for
#         focusing on a small area. 
# - How to get pixel values from single-look data? What does this
#   quote mean from page 52 of BIDR manual?
#   > (paraphrased) get single-look pixel vals by dividing the complex
#   rador cross section value (the result of the SAR processing before
#   detection) by the square-root of the corresponding value in the
#   backscatter coefficient model (defined in the MGN SDPS Functional
#   Requirements [reference 5]). The real and imaginary parts of this
#   ratio are expressed as single-precision floating-point numbers.
#
#   It sounds like it's saying that the division has already been done
#   and that's what's recorded in the single-look image data... except
#   those are complex numbers there, not suitable for pixel values at
#   all.

# > (Page 127) geometric rectification converts complex image pixels
# from the range-doppler coord system into one of the specified
# projection grid systems --- the sinusoidal projection or th eoblique
# sinusoidal projection.

# > (Page 128) first step in the overlay process is to take the square
# magnitude of all sample values in the framelet. the squared value of
# each sample is then added to the corresponding sample (same posn of
# the projection coord) in the overlay buffer. for every sample in the
# overlay buffer, the number of add operation need to be monitored
# during the process of adding framelets in order to know the number
# of looks acquired. the last step in the overlay process is to
# normalize the value of each cell by the acquired number of looks and
# to convert the resultant value to a number expressed in dB through a
# look-up table. It seems that the multi-look images are important.
# They're created through single look images. So perhaps we don't have
# to pay attention to single-looks, if we find them.

#if __name__ == "__main__":
    #process_file(orbit(479, 'file_15'), 'time.png', 8)
