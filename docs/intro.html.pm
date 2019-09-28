#lang pollen

[This
presentation](https://drive.google.com/open?id=1JvPmGv5QkmYR3dWunUkGzPd2EFIvhrY0)
has an introduction to our work and a little bit about how far we've
come.

The following will build on what's in the above presentation.

# What are we doing?

We're trying to create an elevation map for the planet of Venus. An
elevation map is just like a regular map, except for every latitude
and longitude, we will know the height of the land. Mountains will be
high, valleys will be low, plains will generally be in the middle.

We'd like to create a picture of the Venusian surface that can be
referenced by latitude and longitude; stored at the latitude and
longtitude will be a number which states how high the surface is at
that location.

# Why Hasn't this been done already / Background

Before we continue, let's look at some background of this mission.
People produce elevations maps all the time of Earth. Of buildings,
cities, and the whole globe. It's common. The challenges of this
project lie in what makes this job different from others; what makes
existing tools incompatible with the information available.

People have been looking at Venus since they've had telescopes.  There
were prior attempts to image Venus' surface. Chapter 1 of the Magellan
Guide speaks more about this; early attempts gave scientists just
enough detail of the terrain for them to know they needed even more
detail. Enough detail to raise questions about Venus' terrain. So the
Magellan mission was organized. The missions right before Magellan
were the Soviet Veneras 15 and 16 which obtained radar images of 25%
of Venus' surface with resolution ◊${1km} or better.

◊doc-draft{
- A little background 
- What's done on other missions that try to get height maps.  What
  preparations did they make to get a DEM? Some example things to
  research:
    - Did they outfit it with a particular sensor? 
    - Did the sensor have to have a min quality/resolution? 
    - Did they put more than one to always have more than one
      perspective of a location in a very standard way?
    - Did the planet have fewer obstacles, like did it not have thick
      methane clouds or something like that? Was that even a problem
      for Venus?
    - Did the techniques they use apply only to optical images while
      we have radar images?
- Why that doesn't apply to the magellan mission: how are the things
  you researched different for the magellan mission?
- Get a better explanation of stereogrammetry with visuals. It doesn't
  have to be in-depth. Give enough info to explain both what we're
  trying to do with the pictures, why the pictures have to be accurate
  (why lighting artifats are risky business for us introdced by
  mosaics), and why we have to resort to using the pictures rather
  than other methods.

- Why do we need higher resolution data? Who cares? Is it just so that
  the pictures are prettier? Somewhat. For visitors of the AMNH space
  shows, sure.  but other scientists need it for their study of Venus'
  terrain as well ◊paper['mgn-guide 8]. Many think that studying
  peculiar land formations on Venus can help us understand more about
  how Earth's surface came to be the way that it is. ◊todo{source}

- ◊paper['mgn-guide 9]: Venus has thick cloud cover. In mgn radar
  sensor section.
- A footprint is the area that the satellite covers when it shoots
  radiation at it. ◊paper['mgn-guide 9] picture here explains more.


Here are some links that look okay for stereo/photogrammetry

<https://github.com/john-davies/Photogrammetry-examples>
A github repo with some guy with a blog. Talks about his
photogrammetry work. Could help to get the basic idea across of what
photogrammetry it. However, I didn't find blog good for an intro.
Maybe if you're curious and already know. Has good pictures, though.

<https://grindgis.com/blog/basics-photogrammetry>

This looks shitty, but has had some good info. Tells the difference
between vertical and oblique images. Oblique really does just mean
"tilted". Terms it explains:

- Oblique: tilted
- Nadir: line from camera image to the ground. like if the camera shot
  out a laser, where the laser would hit the ground.
- parallax, tho don't fully get it yet. search for parallaxis on the
  page. I think they say a little more when they talk about stereopair
  parallax method. "Requires two overlapping images on the same flight
  line, height of the aircraft, and the average photo base length."
  *the* avg photo baseln not *their* average photo baseln. You just
  need to know it about the pair of photos, it's not a characteristic
  from a single photo.

◊paper['mgn-guide 13] noodle dimensions 
}

The Magellan satellite was launched on May 4, 1989 and arrived at
Venus August 10, 1990. Mapping operations started September 15, 1990
and ended around September 1992 ◊paper['mgn-guide 4]. 

What did the magellan mission achieve?

- Image data of 98% of venus' surface, many areas imaged more than
  once with different imaging geometries and/or directions of
  illumination.
- Altimeter data---basically the thing we're trying to get with this
  project. Rather than take pictures, ◊ns{radiation was used to
  measure the distance of the satellite from the ground}.
- Some other measurements.

Magellan carried an altimeter on board, but the resolution of the
height data is very large---on the order of 10km in between each
sample, and is not always reliable. In mountainous regions, errors in
altitude can be as large as a kilometer ◊paper['radar-venus-1991 1].
The point of this project is to get elevation measurements of better
resolution.

There is another possiblity, though. We have elevation maps and 3D
models of the Earth, cities, and buildings. We tend to use
photogrammetry for that; we figure out how tall things are by taking
pictures from different perspectives under similar lighting
conditions. This is called ◊term{stereogrammetry}. Applying
stereogrammetry to optical photos is called ◊term{photogrammetry,} and
applying stereogrammetry to radar images is called
◊term{radargrammetry}. This works somewhat like how we percieve depth;
by seeing something from two different perspectives (our two
eyeballs), differences in the locations of the object clue us into how
large and far away the object is.

Many space missions have used stereogrammetry to study the altimetry
of different planets. The mission happened before later tools for
stereogrammetry (getting elevation data from a pair of images from
different perspectives of the same region) were developed. So the data
isn't immediately usable with known tools for performing
stereogrammetry. Common stereogrammetry tools aren't compatible with
it for futher reasons: this is radar data, not optical data and must
be handled a little differently; and most tools can't handle planetary
data.  
◊todo{Explain this a little better; is it the scale of
planetary data that's the problem? What's the difference briefly b/w
photogrammetry and radargrammetry? Real brief.}

## Key Sources

- Data from the Magellan mission is available
  [here](http://pds-geosciences.wustl.edu/mgn/mgn-v-rdrs-5-bidr-full-res-v1/)
- The Magellan Software Interface Specification (SIS) for the F-BIDR
  files located in ◊paper{MGN-FBIDR-SIS-SDPS-101-RevE.pdf}.
  Each F-BIDR is a collection of 20 files (and some extra metadata
  files, whose extension is `.lbl`) which contain both image data and
  metadata about the image and spacecraft. This document describes the
  binary format of some of the files in detail (Files 12-19), and also
  describes the meaning of the information, but is not sufficient
  alone for interpretation. From here on in, will be called just *FBIDR SIS*.
- The Guide to Magellan Image Interpretation located in
  ◊paper{19940013181.pdf}. This is broader in scope and
  less terse than the F-BIDR SIS. It goes over details of the mission,
  contains a lot of definitions for important terms and concepts in
  the way that satellites function, and the way that the radar on the
  satellite functions as well. For actual image interpretation,
  Chapters 2 and 5 of this document are valuable.
  From here on, will be called just *Magellan Guide*.
  The guide is also [available
  here](https://history.nasa.gov/JPL-93-24/jpl_93-24.htm)

## Problems: what are we trying to overcome?

Lastly, the actual images are not optical images; they are not created
by reflected visible light from a surface. This was done for different
reasons, but one of them being thick clouds that cover Venus.
Radiation that could penetrate the clouds had to be used.

So for an accurate map of elevation for Venus, techniques that rely on
images of the surface have to be used, because that's what's
available, could produce results more accurate and at higher
resolutions than the on-board altimeter.

## What do the pictures mean, and where are they in the data?

There's supposed to be image data of Venus' surface. Where?

Each F-BIDR is a collection of 20 files, much of which is metadata.
Files 12-19, as specified in the FBIDR SIS are comprised of pieces
called *logical records*. Files 13 and 15 have logical records which
contain both satellite metadata and image data from the radar. The
satellite metadata helps us understand which part of Venus' surface
the image corresponds to, so that the pieces can be joined together
into larger pictures which represent a whole orbit, or multiple
orbits.

Each pixel represents ◊${75m^2} of Venus' surface. They're 75m wide and
tall. A radar on Magellan emitted radiation from a small dish and
captured some of the radiation back a small amount of time later. The
intensity of the pixel is the intensity of the reflected radiation.
What precisely this means we can't quite say yet. More reading to do.
It's easier to start off with what it *isn't*.

- It's not brightness of the surface. The radiation isn't visible and
  the radar wasn't affected by visible light (we assume).
- It has nothing to do with color of the surface (we assume).

What the intensities tell us is how capable a given patch of land was
at reflecting the radiation back toward the satellite. Chapter 5 of
the Magellan Guide goes into more detail about this, but here's a
summary. First, an image describing various terms on satellite
orientation toward the surface. The *SAR* is the radar dish on the
magellan satellite. If I talk about satellite orientation, I'm really
talking about the orientation of this dish.

◊img["satellite-info.png"]{Demonstration of satellite orientation
terms. Caption from original figure: Geometry of radar image
acquisition. The depression angle is complementary to the look angle;
the incidence angle may be affected by planetary curvature. Local
incidence angle may be affected by local topography.}

A note: incidence angle and look angle are *not* the same. On the
radar swath in the image (the shaded grey bar on the surface) is a
thin black line that crosses the swath, along with a squiggly. The
line represents an assumed reference surface, and the squiggly is the
actual surface. The reference surface is flat in the picture, but it
doesn't have to be. Actual surfaces often aren't flat. The
picture-in-picture insert describes this well: there's the *local*
incidence angle, which is the actual incidence angle the radiation
makes with the actual (squiggly) ground.

There's a few things that affect how capable a patch of land is at
reflecting radiation: the *incidence angle* (the angle between the
radiation and the surface struck by it), the roughness of the ground,
and the patch having very reflective materials. If a patch has more
reflective materials, then generally the intensity of the pixel
representing that patch will be greater. For the other two parameters,
the explanation is less straightforward; incidence angle and roughness
have an interplay, as shown in the following 2 figures:

◊img["incidence-angle-land-demo.png"]{Demonstration of reflectivity of 2 different
surfaces}

In the very top image, the surface is flat so it acts like a mirror.
Radiation hits it and then bounces away. If the incidence angle is
small, then the radiation will probably bounce back toward the radar
causing very bright intensity (radar-bright); if the incidence angle
is large, then the flat ground will show up dark (radar-dark).

The more rough the ground, the less intensity will shoot right back at
the radar in any one direction because the radiation will be spread
out in different directions; however regardless of the incidence
angle, radiation is more likely to go back to the radar than miss it. The
following graph shows this in more detail. Higher radar backscatter
means higher pixel intensity.

◊img["incidence-angle-reflection-graph.png"]{Backscatter vs incidence
angle for different surfaces}

Notice that the graph for rough ground changes less with incidence
angle while the graph for flat ground changes a lot with incidence
angle.

Here's two radar images of some mountains in California which display
the difference between different incidence angles. They're of the same
region; the dark bottom of the top image is not the night sky (we
thought it was for a moment), but *flat ground* from a high incidence
angle (◊deg{50}). There are bright dots in the dark region of the top
photo; look for them in the bottom photo to be able to compare the two
regions. The pictures are basically the same scale and width and
height.

◊img["incidence-angle-land-effects.png"]{Comparison of incidence angle
effects at California Mountains}
