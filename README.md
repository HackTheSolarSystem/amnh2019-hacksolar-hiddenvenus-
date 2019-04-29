## Lotta Research

### Adressing [The Hidden Face of Venus](https://github.com/amnh/HackTheSolarSystem/wiki/The-Hidden-Face-of-Venus)

### Created By Team Team

- Jennifer Shin <https://github.com/jennshin>
- Adam Ibrahim <https://github.com/beelzebielsk>

We're working on reading in the binary data from the magellan mission
(complete) and interpreting it as grayscale images (WIP). At the same
time, we'll be taking a look at the Ames Stereo Pipeline to see how
we'd work with it.k
For the moment there's just a presentation, and the presentation is
fairly soft. We got as far as wading through a sea of information,
much of it quite old, not all of it relevant. Summarizing that was
difficult. A better description of the challenge and problem follows.
If any information in this readme conflicts with information from the
presentation, trust the readme. It reflects a little extra work after
the haze of the hackathon and nonsleep.

### Solution Description

We did not reach a solution, yet. There's a lot of research yet to be
done. Most of the work in the repository is dedicated to reading the
Magellan Mission Data.

The file `example.py` is a demo of the F-BIDR file reading work, and
can extract a grayscale image from Magellan Mission data, if some is
placed in the repostiory root directory.

# Progress

Rather than describe future work, it makes more sense to describe
what's currently known about this project. The start is a lot of
research, as well as working with old data from the 90s. Future work
grows right out of the remaining questions in our progress.

## Key Sources

- Data from the Magellan mission is available
  [here](http://pds-geosciences.wustl.edu/mgn/mgn-v-rdrs-5-bidr-full-res-v1/)
- The Magellan Software Interface Specification (SIS) for the F-BIDR
  files located in `papers+documents/MGN-FBIDR-SIS-SDPS-101-RevE.pdf`.
  Each F-BIDR is a collection of 20 files (and some extra metadata
  files, whose extension is `.lbl`) which contain both image data and
  metadata about the image and spacecraft. This document describes the
  binary format of some of the files in detail (Files 12-19), and also
  describes the meaning of the information, but is not sufficient
  alone for interpretation. From here on in, will be called just *FBIDR SIS*.
- The Guide to Magellan Image Interpretation located in
  `papers+documents/19940013181.pdf`. This is broader in scope and
  less terse than the F-BIDR SIS. It goes over details of the mission,
  contains a lot of definitions for important terms and concepts in
  the way that satellites function, and the way that the radar on the
  satellite functions as well. For actual image interpretation,
  Chapters 2 and 5 of this document are valuable.
  From here on, will be called just *Magellan Guide*.
- The data from the mission is quite old and is incompatible with the
  standard tools that NASA uses for this task: the Ames Stereo Piepline
  (ASP).

## Problems: what are we trying to overcome?

The Magellan data was collected between about 1991 and 1993. The
mission happened before later tools for sterogrammetry (getting
elevation data from a pair of images from different perspectives of
the same region) were developed. So the data isn't immediately usable
with known tools for performing stereogrammetry.

Magellan carried an altimeter on board, but the resolution of the
height data is very large (on the order of 10km in between each
sample), and is not always reliable. In mountainous regions, errors in
altitude can be as large as a kilometer.

Lastly, the actual images are not optical images; they are not created
by reflected visible light from a surface. This was done for different
reasons, but one of them being thick clouds that cover Venus.
Radiation that could penetrate the clouds had to be used.

So for an accurate map of elevation for Venus, techniques that rely on
images of the surface have to be used, because that's what's
available, could produce results more accurate and at higher
resolutions than the on-board altimeter.

## What do the pictures mean, and where are they in the data?

Each F-BIDR is a collection of 20 files, much of which is metadata.
Files 12-19, as specified in the FBIDR SIS are comprised of pieces
called *logical records*. Files 13 and 15 have logical records which
contain both satellite metadata and image data from the radar. The
satellite metadata helps us understand which part of Venus' surface
the image corresponds to, so that the pieces can be joined together
into larger pictures which represent a whole orbit, or multiple
orbits.

Each pixel represents $75m^2$ of Venus' surface. They're 75m wide and
tall. A radar on Magellan emitted radiation from a small dish and
captured some of the radiation back a small amount of time later. The
intensity of the pixel is the intensity of the reflected radiation.
What precisely this means I can't quite say. It's easier to start off
with what it *isn't*.

- It's not brightness of the surface. The radiation isn't visible and
  the radar wasn't affected by visible light (I assume).
- It has nothing to do with color of the surface (I assume).

What the intensities tell us is how capable a given patch of land was
at reflecting the radiation back toward the satellite. Chapter 5 of
the Magellan Guide goes into more detail about this, but here's a
summary. 

![Demonstration of satellite orientation terms](readme-images/satellite-info.png)

There's a few things that affect how capable a patch of land is at
reflecting radiation: the Incidence Angle (the angle between the
radiation and the surface struck by it), the roughness of the ground,
and the patch having very reflective materials. If a patch has more
reflective materials, then generally the intensity of the pixel
representing that patch will be greater. For the other two parameters,
the explanation is less straightforward; incidence angle and roughness
have an interplay, as shown in the following 2 figures:

![Demonstration of reflectivity of 2 different
surfaces](readme-images/incidence-angle-land-demo.png)

In the very top image, the surface is flat so it acts like a mirror.
Radiation hits it and then bounces away. If the incidence angle is
small, then the radiation will probably bounce back toward the radar
causing very bright intensity (radar-bright); if the incidence angle
is large, then the flat ground will show up dark (radar-dark).

The more rough the ground, the less intensity will shoot right back at
the radar in any one direction because the radiation will be spread
out in different directions; however regardless of the incidence
angle, light is more likely to go back to the radar than miss it. The
following graph shows this in more detail. Higher radar backscatter
means higher pixel intensity.

![Backscatter vs incidence angle for different
surfaces](readme-images/incidence-angle-reflection-graph.png)

Notice that the graph for rough ground changes less with incidence
angle while the graph for flat ground changes a lot with incidence
angle.

Here's two radar images of some mountains in California which display
the difference between different incidence angles. They're of the same
region; the dark bottom of the top image is not the night sky (I
thought it was), but *flat ground* from a high incidence angle
($50\deg$).

![Comparison of incidence angle effects at California
Mountains](readme-images/incidence-angle-land-effects.png)

- The F-BIDR is an orbit. It's the collection of 20 files plus labels
  and shit. There's **5933** F-BIDRs for the magellan mission, total.
  Total dataset is actually kinda big. Each F-BIDR contains ~100MB in
  image data alone, plus other stuff, and there's around ~6000 F-BIDR,
  meaning at least 600GB in data, possibly up to around 1TB. Total,
  all files, all F-BIDRs. I think I can see why there was so much
  writing involved. This was big data by today's standards, and they
  did it back in the 90s.
- BIDR Data files: longer descriptions of each F-BIDR file.
- Applicable Documents: References. References to other documents
  refer to here.

- The Magellan Spacecraft took images by blasting radio waves at the
surface and recording the reflected waves.
- There is a repository of the magellan data [available
  online](http://pds-geosciences.wustl.edu/mgn/mgn-v-rdrs-5-bidr-full-res-v1/).
  I found it... odd. There's tons of directions, and lots of
  repetition for a thing I've never seen before. It's precision seems
  self-defeating. Anyhow, this directory is full of folders of the
  form `MG_nnnn`.
    - Each of these folders represents the contents of a CD of
      magellan satellite data. A real physical disk, it seems. It also
      seems that each of these volumes is an `F-BIDR`: a
      Full-Resolution Basic Image Data Record. This was a little
      counterintuitive for us, since there's a lot more data in an
      F-BIDR than an image. We base this conclusion on the paper
      `./papers+documents/MGN-FBIDR-SIS-SDPS-101-RevE.pdf`.
    - In the root directory of each `F-BIDR` is a readme. They're all
      the same readme, character-for-character. Just read one.
    - There are also several folders of the form `Fnnnn_v`. The `nnnn`
      represents the orbit number, and `v` the version. I assume this
      means that, for instance, the folder `F0376_3` represents data
      collected from the 376th orbit, 3rd version (why there's more
      than one version is unclear to me). We'll call these folders
      **orbits**.
    - Each orbit contains files named "FILE_13" and "FILE_15". These
      are radar image data files. Every file in this folder is
      accompanied by a file of name `name.LBL`. This contains some
      metadata about the original file, including a *description of
      the contents*.
    - Page 3-5 refers to the contents of FILE_01 in each orbit. I did
      not understand that at first, I thought this was the description
      of the image data itself.
    - All of the orbits in each of these volumes are F-BIDRs.
    - Section 3.4 of the F-BIDR format paper specifies what the images
      will look like, in terms of their binary format.
        - The first 12 bytes are an NJPL Primary Label Type. Not sure
          why this matters.

### File Formats

We'll use `data/MG_4001/F0376_3/FILE_13` as an example. According to
section 3.4 of the F-BIDR pdf, and some guessing, each physical file
(such as FILE_13, a file on a filesystem) consists of several logical
records. Not clear why. The length of every physical file is multiple
of 32,500 bytes. For instance, our example file is 8612500 bytes long,
which is 265 * 32500.

This file conists of several logical records. Section 3.4 explains
what a logical record looks like. The first 12 bytes are the
ASCII characters:

    NJPL1I000nnn

where the `nnn` at the end is a placeholder for some numbers. In FILE
13, the `nnn` is `104`. Unless otherwise specified everything we're
talking about is ascii characters, and any ascii characters that spell
out a number spell out a *decimal* number.

Bytes 12-19 are the length of the logical record. In FILE_13, the
length bytes are `00031032` (remember, ASCII characters are in the
file, not the number itself!)

From byte 20 up to  `20 + logical record length` (exclusive end) is
the data of the logical record. So, for example, if the length bytes
spelled out the number 1, then the logical record would consist of
only the 20th byte of the file.

Thus byte `20 + 31032 = 31052` is the first byte that doesn't belong
to this logical record. In FILE 13, it's the start of the next record.

Let's double-check these findings with a hexdump of our example file,
obtained using `$ xxd FILE_13`:

    00000000: 4e4a 504c 3149 3030 3031 3034 3030 3033  NJPL1I0001040003
    00000010: 3130 3332 0200 4400 7801 4240 3c00 0402  1032..D.x.B@<...

Quickly, the format of a line from a hexdump is: the first number is
the address of the 1st byte in the line. The first byte is the
leftmost byte after the address (`4e`, in this case). Every byte has
an address. The 1st byte in the file has address `0x00000000`, the
next has `0x00000001` and so on.

Each line displays 16 bytes (0x00000010 is 16 in hexadecimal).

    00000000: 4e4a 504c 3149 3030 3031 3034 3030 3033  NJPL1I0001040003
                                                       ------------    
The underlined section is the NJPL label.

    00000000: 4e4a 504c 3149 3030 3031 3034 3030 3033  NJPL1I0001040003
                                                                   ----
    00000010: 3130 3332 0200 4400 7801 4240 3c00 0402  1032..D.x.B@<...
                                                       ----            

The underlined section, which crosses from the end of the first line
to the start of the second line, is the logical record length of
`00031032`, which is 31032 bytes.

And if we go all the way down to the end of the logical record, which
is byte 31052 (0x794c):


    00007940: 515d 5e59 4d5e 676e 645e 5a69 4e4a 504c  Q]^YM^gnd^ZiNJPL
    00007950: 3149 3030 3031 3034 3030 3033 3130 3332  1I00010400031032

Byte `0x794c`, the 12th byte in this line, (`4e`) is the first byte
that's not in our logical record. Lo and behold, it's the start of a
new logical record. So the numbers check out.

### Image Format

To help discussion, when we talk about the "end" of a field containing
bytes, we mean the byte after the field ends. For instance, if a field
is a 16-bit integer (2 bytes) at the start of a file (meaning the
integer is bytes 0 and 1 of the file), then the end of this field is
byte 2.

The format of the data of an image file (like `FILE_13`) consists of a
secondary header, followed by stuff TODO: What stuff?

The secondary header starts at the beginning of the data section of a
logical record, so byte 20. Section 3.4.1 in the BIDR PDF states what
a secondary header looks like. The first field in the secondary header
is a two-byte integer. According to Appendix B of the BIDR PDF, it's
little-endian (least significant byte of the number has lowest address
in memory---ie is the starting byte of the number).

    00000010: 3130 3332 0200 4400 7801 4240 3c00 0402  1032..D.x.B@<...
                        ----

The underlined bytes are bytes 20-21 of the file, and it's the number
`0x2` which is decimal 2. This means image data, as stated in page
3-13 of the BIDR PDF.

The next two bytes are the secondary header length, an unsigned 16-bit 
integer.

    00000010: 3130 3332 0200 4400 7801 4240 3c00 0402  1032..D.x.B@<...
                             ----

It's the number `0x0044`, which is 68 in decimal. According to 3-13 in
BIDR PDF, this means that the secondary header has an exclusive end 68
bytes after the end of the secondary header length. So byte $22 + 68 =
90$ is the end of the secondary header. The secondary header length
for image files is always 68 bytes.

The rest of the secondary header contains an orbit number as unsigned
16-bit integer:

    00000010: 3130 3332 0200 4400 7801 4240 3c00 0402  1032..D.x.B@<...
                                  ----

`0x0178` = 376, which matches the number in the folder containing
`FILE_13`: `data/MG_4001/F0376_3/FILE_13`, since that's an orbit
number.

The next 8-bit integer is the data class:

    00000010: 3130 3332 0200 4400 7801 4240 3c00 0402  1032..D.x.B@<...
                                       --

`0x42` = 66, which represents image data in oblique sinusoidal
projection.
