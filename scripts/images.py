from f_bidr import logical_record, count_logical_recs, read_logical_records

import matplotlib.pyplot as plt
import matplotlib
import numpy as np

# NOTE: File 15 has more than one logical record. It's a series of
# logical records.
with open("sample-data/FILE_15", 'rb') as f:
    contents = f.read()
    #records = read_logical_records(contents, 1000)
    records = read_logical_records(contents)

gray = matplotlib.cm.get_cmap('gray')

def image_shift(image, shift, total_width, most_negative):
    # 0 pixel offset means no shifting.
    # For now we'll say that a positive offset is a right shift
    # and a negative offset is a left shift.
    # What's a right shift by i pixels? image[0,0] -> image[0,i]
    # What gets inserted in the missing pixels? Black.
    height, width = image.shape
    picture_left = shift - most_negative
    black = np.zeros((height, total_width))
    black[:, picture_left:picture_left + width] = image
    return black

def image_stitch(records, sort_by, pixel_shift=True):
    # The final picture should be wide enough to fit any piece at
    # any of the offsets for those pieces. At minimum, that's a width
    # of the range of offsets (max_offset - min_offset), because a
    # picture's left-most pixel can go anywhere in that range. Then,
    # the picture whose offset is the max will have 512 pixels to the
    # right.
    #records.sort(key=lambda r: r[sort_by], reverse=True)
    pixel_offsets = [r['reference_offset_pixels'] for r in records]
    most_neg_offset = min(pixel_offsets)
    min_offset, max_offset = min(pixel_offsets), max(pixel_offsets)
    max_width = max_offset - min_offset + 512
    # Index 0 in the final image will be the most negative offset
    # pixel.
    # For now, assume that each picture should directly touch previous
    # picture.
    image_data = [[x['line'] for x in r['data']] for r in records]
    images = [np.array(x) for x in image_data]
    #shifted_images = []
    for i in range(len(images)):
        images[i] = image_shift(
            images[i], pixel_offsets[i],
            max_width, most_neg_offset)
    large_image = np.concatenate(images, axis=0)
    plt.imsave('/tmp/long-strip.png', large_image, cmap=gray)
    return large_image

#for i, image in enumerate(images):
    #plt.imsave(f'sample-images/{i:02}.png', image, cmap=gray)

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
