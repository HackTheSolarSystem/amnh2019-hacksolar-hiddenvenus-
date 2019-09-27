#lang pollen

An overview of each F-BIDR, or "noodle".

F-BIDR is a collection of 20 files all written in a binary format that
NASA created. There were programs to read these files a long time ago,
but they are not currently available for a typical computer today. As
far as we know, they were all built for a ◊ns{different processor
architecture DEC/VAX}

Each file name is of the form "file_01", "file_02" and they all
contain different data. The two files from each F-BIDR that we care
about the most are files "file_13" and "file_15"; however the tools
from ◊path{images.py} are only written to work with contents in
"file_15" of an F-BIDR.

For the most part, when we say "noodle" we're really referring to the
image data in "file_15". There will soon be another page that goes
deeper into the particulars of the data format, ◊todo{Write this page}
but here is what matters the most:

- Each "file_15" is actually a series of smaller pictures from the
orbit. Think of the satellite as having taken many single photos as
the satellite travelled along its orbit. I will call each of these
smaller photos a *snapshot* for now.
- Each pixel from these smaller images is ◊${75m x 75m}.
- Each of these smaller pieces comes packaged with some metadata.
There is a longitude and latitude for each snapshot which describes
the longitude and latitude where the snapshot was taken. Precisely,  
each of these smaller pieces has a "reference pixel". This is the
  top-left pixel in the image 
  ◊todo{Make sure that's true for all images} 
  and any latitude/longitude information about where the photo was
  taken actually corresponds to the location in latitude/longitude on
  Venus of the center of this pixel.
- Each snapshot is a sequence of rows, each of which is a sequence of
pixels. Each pixel is given a value between 0 and 251. The value 0 may
mean that a pixel is "invalid" meaning that there was not enough
information on that location to say what value the pixel should have.
All invalid pixels have a value of 0, though not all pixels with a
value of 0 are invalid. It is possible for valid data to have a value
of 0 if that is just what was recorded ◊paper['fbidr-sis 50].
- Rows that come earlier in the snapshot are North of rows that come
later in the snapshot. Pixels that come earlier in the row are West of
pixels that come later in the row.  Earlier and later means how far
they are in the file (how many bytes you have to read to get to that
row/pixel).


And a small overview of how we produce the full noodle picture is
helpful, too:

- Each snapshot comes with both the latitude and longitude of the
  reference pixel, but also a "pixel offset" and "line offset" into
  the noodle picture. The folks at NASA calculated this ahead of time
  it seems---at least for a single noodle; I've had no luck making
  these numbers work when trying to piece together more noodles.
- We create one very large image: one that should be tall enough fit
  all of the snapshots together when they're all in the correct place.
  Let's call this large image a ◊em{canvas}. The Northmost snapshot's
  1st line is the 1st line of the photo, the Southmost snapshot's last
  line is the last line of the photo. The westmost snapshot's westmost
  pixel is the westmost pixel of the image, and the eastmost
  snapshot's eastmost pixel is the eastmost pixel of the image.
- We find the correct location for the reference pixel of each snapshot
  in the canvas according to the metadata of the snapshot and write
  all of the pixels of the snapshot to the image. Every pixel adjacent
  in the snapshot is adjacent in the image.
