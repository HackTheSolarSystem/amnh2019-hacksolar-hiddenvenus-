#lang pollen

Our project addressed [The Hidden Face of
Venus](https://github.com/amnh/HackTheSolarSystem/wiki/The-Hidden-Face-of-Venus)

# Team Members

- Jennifer Shin 
    - <https://www.linkedin.com/in/jennshin>
    - <https://github.com/jennshin>
- Adam Ibrahim 
    - <https://www.linkedin.com/in/adam-ibrahim/>
    - <https://github.com/beelzebielsk>

# Links

- [Our Repository](https://github.com/HackTheSolarSystem/amnh2019-hacksolar-hiddenvenus-)

# What are we doing?

We're trying to create a ◊term{Digital Elevation Map} (DEM) for the
planet of Venus. An elevation map is just like a regular map, except
that for every latitude and longitude, we will know the height of the
land. Roughly speaking, mountains will be high, valleys will be low,
plains will generally be in the middle.

# Why are we doing it?

- Because it's cool.
- Because it's fun.
- Because we were asked to.
- It is an interesting trip through time as we work with programs and
  data from the early 90s.
- The results are beautiful, and they will be even more beautiful when
  paired with AMNH's OpenSpace program.

# Status Report

The magellan satellite orbited around Venus many times, taking
pictures of the land that it passsed over using radiation, rather than
visible light. These pictures were stored in an old format created by
NASA that is not in use anymore. We can read the image data from these
old files and write them as `PNG` files. It is possible to write them
in other image formats, too. We can read in the binary data from a
single orbit from the Magellan Mission and view it as greyscale
images. 

Since each of these files is the result of scanning Venus' surface
during one orbit, the image data contained corresponds to a very long
and narrow strip; thus they are commonly called ◊term{noodles}. These
images are very wide and very tall with a lot of black space because
each noodle tends to "sweep" eastward on the planet toward the end.
Below is a comparison between a strip that's been reduced to 1% of its
original size, alongside a small section at the top of the strip that
is at full scale. The original size of the noddle is 3456 ◊by 115528 (3456
pixels wide ◊by 115528 pixels tall). The scaled-down version has
dimensions 35 ◊by 1155; you can see a small red rectangle on the
scaled-down version on the left which indicates the region that the
larger picture corresponds to. The rectangle is hard to see; that is
how small of a piece the right side is when taken from the left side.

◊todo{
Make this work.

- I know the two images are the same height.
- I want the two images to be scaled by the same factor, so that they
keep the same relative scale to each other.
- I want them to fit within the confines of their bounding div.
- I want whitespace to be between the two elements.
}

<div id="orbit-side-by-side"
    style="width: 100%; height: 1020px; position: relative;
    ◊;{display: flex; justify-content:
    space-between;}">
    <img
        id="small"
        style="height: 1020px; position: absolute;"
        src="◊(image-path "1-per-scale-strip-indicator.png")"
        alt="Scaled down noodle image"/>
    <div style="width:5%; height: 100%; display: inline;"></div>
    <img
        id="big"
        style="height: 1020px; position: absolute; left: 100%; transform:
        translateX(-100%)"
        src="◊(image-path "strip-long-cropped.png")"
        alt="Full-scale piece of same noodle image"/>
</div>

We're currently researching leads on what to do next. There are
existing tools for generating DEMs, but would not be directly
compatible with the Magellan data. There's also existing work on the
Magellan data we could improve on. Finally, there are tools to create
DEMs used for later planetary missions; perhaps we could make use of
those by making them compatible with magellan data.

Things Coming Soon!

- Project Introduction
    - What is a DEM? (done)
- Details
    - Map coordinate system: 0-360 long which goes eastward, 90 to 90
    lat with goes north to south.
    - Composition of a noodle. This is important to the noodle
    creation process, and to explaining any graphs of the image
    records.
        - reference pixel: what is it, where is it in each snapshot?
        - Consists of individual logical records each holding small
        snapshot
        - Explain how the noodle image (not stitching) is generated.
        - Explain the naming of the BIDRs: orbit no and version, so
        you can reference them as such later on.
    - Magellan Data particulars
        - Cycles, what was gained from each cycle.
        - Binary format of the data.
        - The format of the files, at least. And their role. I could
        at least point them to a good page in the FBIDR SIS.
    - Explanation of image metadata, important pieces. Explanation of
    the different coordinate systems (sinusoidal pixel/line and
    spherical lat/lon).
    - Maybe the behavior of the satllite? How it spun around the
    planet, how it recorded radar data. A diagram of the orbit
    inclincation angle could help, and the rotation direction of
    Venus. I drew one of those already. This could extend into a
    discussion on doppler/range because that may be important to the
    work anyway. (WIP)
    - Validation
        - Producing pictures from other research papers
        - Studying the data to see if it corresponds with how we think
        the satellite would've moved around Venus.
        - libvaxdata's VAX floating point test cases for VAX
        conversion.
