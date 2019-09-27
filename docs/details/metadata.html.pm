#lang pollen

This will go over the particulars of the F-BIDR file format. The main
source of information on this format is The FBIDR-SIS, which is stored in
◊paper{MGN-FBIDR-SIS-SDPS-101-RevE.pdf}. We got all of our information
from here. Though there are a few locations where the FBIDR-SIS was
wrong, had to find that out the hard way.

# Getting the F-BIDR files

The F-BIDR files can be downloaded from
[here](http://pds-geosciences.wustl.edu/mgn/mgn-v-rdrs-5-bidr-full-res-v1/).

This is a mirror hosting all the different F-BIDR files. Here's a
small part of the directory tree from the mirror:

- ◊path{MG_4001}
    - ◊path{F0376_3}
        - ◊path{FILE_01}
        - ◊path{FILE_02}
        - ◊path{FILE_03}
        - ◊path{FILE_04}
        - ◊path{...}
    - ◊path{F0377_3}
    - ◊path{F0378_3}
    - ◊path{F0379_3}
    - ◊path{F0380_3} 

The Magellan data was originally stored and distributed on CD-ROMs.
Folders like ◊path{MG_4001} are the contents of one of those CD-ROMs;
we will call these ◊term{Magellan Volumes}.  Folders like
◊path{F0376_3} are the F-BIDRs; they consist of 20 files (at least)
all of the form ◊path{FILE_01}, ◊path{FILE_02}. These 20 files should
be present in every F-BIDR, have the same name in each F-BIDR, and
each file stores the same sort of information for each F-BIDR. For
example, files 13 and 15 are image data in a special format.

Each magellan volume has an ◊path{AAREADME.TXT} file and some have
◊path{ERRATA.TXT}. The ◊path{AAREADME.TXT}  is the same for all of the
volumes; it just describes the different files contained in each
F-BIDR and has some other information. While it is worth a read, much
of the same information can be found in the FBIDR-SIS.

# Contents of Each F-BIDR

Each F-BIDR contains data which corresponds to one pass of the
Magellan satellite around Venus. So the naming scheme of the F-BIDR is

    "F" orbit-number "_" version-number

For instance, the orbit number and version number for ◊path{F0376_3}
are "376" and "3" respectively.

The following applies to Files 12 to 19 of each F-BIDR
◊paper['fbidr-sis '3-11]. These are binary files---you won't be able
to read them as raw text---similar to a photo or a music file. This is
in contrast to text data formats like XML or JSON which did not exist
at the time. Each of these files is comprised of ◊term{logical
records}. Some files are just one logical record, they tend to be
smaller. Other files---especially thsoe that contain image data---have
more logical records.

# Overview of the Image Data

Important info in for the image data in an F-BIDR. ◊path{FILE_13} and
◊path{FILE_15} are the image data in an F-BIDR.  As an example
file_15, let's use ◊path{MG_4001/F0376_3/FILE_15}.

This file, like the rest, is comprised of logical records. Many of
them. Our example file has *5187* logical records.

Each of these logical records contains a single image. Metadata in the
logical record states how tall and wide the image is. We can interpret
these images as greyscale images, but be *careful*. The intensities
are not indicative of the visual intensities of the landscape. The
landscape is not being illuminated by optical light of any kind in
these photos; the SAR on Magellan recorded reflected radiation that
Magellan itself shot at the land. See the
◊page-link["/docs/intro.html"]{intro} for more details.

There is location metadata recording in each logical record as well to
state what location on Venus the contained image corresponds to. The
location metadata is relative to a ◊term{reference point}.

Each of these logical records has the following metadata:

- Image Line Count: How tall the contained image is.
- Image Line Length: How wide the contained image is.
- Reference point latitude: The latitude of the reference point of the
contained image.
- Reference point longitude: The longitude of the reference point of
the contained image.

Each pixel of the image is 75m ◊by 75m large. That means one intensity
value represents the reflected radiation for a 75m ◊by 75m section of
Venus' surface. The center of the first pixel of the first line is the
reference point of the contained image.

◊under-construction 

◊todo{fix this up}

Let's take a short break to sum this all up using our example F-BIDR.

    ◊todo{re-do this after transforming how images are represented
    into numpy arrays, because this is needlessly inconvenient to
    read. I think it would make tutorials difficult.}

    from f_bidr import read_logical_records
    from f_bidr_data import get_orbit_file_path as orbit

    orb376FilePath = orbit(376, 'file_15', 3)
    orb376 = read_logical_records(orb376FilePath)
    # orb376[0] is the first logical record
    print(orb376[0]['reference_lat']) # 89.3893814086914
    print(orb376[0]['reference_lon']) # 317.643310546875
    # orb376[0]['data'] is the image data
    # orb376[0]['data'][0]['line'] is the first line of pixels
    print(orb376[0]['data'][0]['line'][0]) # 0

The reference latitude of the first logical record of our example
"file_15" is ◊deg{89.39}, and the reference longitude is
◊deg{317.64}. This is the location of the center of the first
pixel of the first line of this logical record. On this orbit, the
Magellan satellite started recording image data at
◊deg{89.39} latitude and ◊deg{317.64} longitude.

- projection origin latitude: Always ◊deg{0}.
- projection origin longitude: The longitude where Magellan crossed
over the equator of Venus during this orbit.

# Too Much Detail

The rest of this document is for understanding the binary
format of the F-BIDR files. This information is not at all necessary
if you just want to work with the F-BIDR files. The ◊path{f_bidr.py}
program can read any of files 12 through 19 from an F-BIDR, and you
can manipulate the data programmatically, and inspect the values of
all data and metadata from within python.

Each logical record has a common structure:

- The first 20 bytes are some metadata, which I have not found
particularly important (except for writing a program to read F-BIDR
files).
- The secondary header, which also contains metadata. 
    - The orbit number (which orbit the F-BIDR corresponds to).
    - It states the type of the record
    given t
- The data block, which contains the 'meat' of the logical record, the
main data that the logical record has.

talk about valid/non-valid pixels, they have value 0, not all pixels
with value 0 are invalid, what the different versions of an orbit are.
Go figure that out.
