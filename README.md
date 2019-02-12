For the moment there's just a presentation, and the presentation is
fairly soft. A better description of the challenge and problem:

Challenge
=========

In 1990, the Magellan Spacecraft was sent to Venus. Among other
things, it recorded data about the terrain of venus using radar waves.
More recent data from other space missions has used optical pictures
of a planet's surface to create a Digital Elevation Model (DEM), which
specifies how tall various parts of the surface are in relation to
each other.

AMNH uses a program, OpenSpace, for it's space shows. It's a data
visualization program which allows one to view the universe in it's
stellar scale and it's astronomical number of objects. And one of it's
finest touches is being able to zoom all the way in on a planet and
see what that planet actually looks like, based on data gathered from
space missions. From Earth debris left behind in prior missions to the
shape and color of the terrain, all the way down to the stones on the
ground. Not as an artist's rendition, but based on the photos taken by
spacecraft. This is what a DEM is all about.

The challenge is to try to use the data from the Magellan Spacecraft
to create a DEM for Venus. Part of what's difficult about this is:

- The data from the mission is quite old and is incompatible with the
  standard tools that NASA uses for this task: the Ames Stereo Piepline
  (ASP).

What this data actually means is yet unclear. In a conversation with
Carter Emmart, it was postulated that this means "roughness" of a
surface, though I'm not sure yet.

Information Gathered Thus Far
=============================

- The Magellan Spacecraft took images by blasting radio waves at the
surface and recording the reflected waves.
- I believe the format of these images is called Basic Image Data
  Record (BIDR).  TODO: Add a source detailing the format of BIDR.
- There is a repository of the magellan data [available
  online](http://pds-geosciences.wustl.edu/mgn/mgn-v-rdrs-5-bidr-full-res-v1/).
  I found it... odd. There's tons of directions, and lots of
  repetition for a thing I've never seen before. It's precision seems
  self-defeating. Anyhow, this directory is full of folders of the
  form `MG_nnnn`.
    - Each of these folders represents the contents of a CD of
      magellan satellite data. A real physical disk, it seems.
    - In the root directory of each is a readme. They're all the same
      readme, character-for-character. Just read one.
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

Questions
=========

- What does the recorded image data actually mean? How do I interpret
  it? Each pixel of a BIDR image is an 8-bit intensity, but what is
  that intensity analagous to? In a normal greyscale picture,
  intensity is analogous to intensity of light. But for the magellan
  spacecraft's BIDR images, intensity seems to be analogous to the
  intensity of the radio waves that were reflected back from the
  surface of Venus. What does this mean?
