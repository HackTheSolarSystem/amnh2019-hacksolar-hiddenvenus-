#lang pollen

This is information about the Magellan satellite's orbit around Venus,
including when during each orbit the satellite took photos of Venus'
surface.

The two main sources for this page are

- [Wikipedia](https://en.wikipedia.org/wiki/Orbital_inclination) also
has a lot of good information, which I'll summarize and illustrate for
Venus here.
- ◊paper['mgn-guide 10] explains a lot about satellite orbit.

First, a picture:

◊img["orbit-diagram.jpg"]{A diagram of the Magellan's orbit on Venus}

When an artificial satellite orbits a body (like Magellan orbited
Venus), we describe the orbit with different things, one of them being
the ◊term{angle of inclination}. This angle describes how the
satellite orbits relative to the planet's equator and relative to the
planet's rotation. It's the angle made between the equator line and
the orbit line; for the Magellan mission it was ◊deg{85}.

If the angle is between ◊deg{0} and ◊deg{90}, then the orbit is in the
direction of the orbit. Notice how, if you were to follow the orbit
with your finger (in the direction of the arrow), it moves from east
to west in the same way that Venus rotates from east to west.
Satellite orbits that follow the planet's orbit are called
◊term{prograde}, and orbits that go against the planet's orbit are
called ◊term{retrograde}.

Venus is different from Earth in that it rotates ◊em{from east to
west}. So the sun ◊em{rises in the west} on Venus and ◊em{sets in the
east}, the exact opposite of how it is on Earth.

The actual photo taking (radar photos) was done as the satellite came
down from north to south on Venus, the dotted line orbit shown
"behind" Venus. ◊paper['mgn-guide 5] has a helpful image to display
this. 

◊img["full-orbit-time-diagram.png"]{The orbit displayed as a timeline
of various events which occurred during each orbit: from when the
satellite took radiation "pictures" of Venus' surface, to when the
satellite sent that data back to Earth. The top of the picture is
North, and the bottom is South.}

There's a lot going on here, and I want to concentrate on just how and
when the images of the surface were recorded, so I will remove all the
arrows and things not related to just that:

◊img["minimal-orbit-time-diagram.png"]{The orbit just displaying when
recording starts and stops.}

There are two regions of each orbit that the satellite could record:
the ◊term{immeidate region} and the ◊term{delayed region}. In the
immediate region, Magellan starts recording the surface as soon as it
starts going travelling Southward on its orbit; the immediate region
is the bar with lines going across it in the picture. In the delayed
region, Magellan waits a little bit before recording the surface; the
"waits a little bit" is shown by idle time in the delayed swath.

◊todo{Why did they have the two regions? I think the guide and fbidr
sis talk about it.}

Relevant quote from ◊paper['mgn-guide 3]:

> Because the area of new terrain observed by the sensor in
equatorial latitudes is much greater than at the poles, it is possible
to map high latitudes on alternating orbits with an acceptable margin
of overlap. In Cycle 1, this technique was used to reduce redundancy
and maximize areal coverage.  Mapping started at the north pole in
each alternate orbit and continued to about ◊deg{57}  latitude.
These swaths are termed "immediate." In the intervening orbits,
mapping started at about 70°N and extended to 74°S latitude. These
swaths are "delayed." An idle time of about 7 min occurred at the end
of each immediate swath and the beginning of each delayed swath
(Figure 1-3).

The actual data seems to support all these findings.
◊todo{Place the noodle explanation in a different section explaining
the noodles.}
Each noodle actually consists of a series of small pictures of Venus'
surface, with snapshots from earlier in the orbit (more North) coming
first and snapshots from later in the orbit (more South) coming later.
The latitude and longitude of the top-left pixel of each snapshot is
recorded as metadata with each snapshot. 
◊todo{Double check if
top-left, and I think whether it is top-left or top-right depends on
left-looking or right-looking!}
Each of these snapshot data + metadata pairs is called an ◊term{image
record}; below is a graph that plots the image record number (smaller
means earlier in orbit) versus the latitude of the top-left pixel of
the snapshot from a noodle I chose:

◊img["latitude-376-3.png"]

◊todo{Come back here make the fonts bigger for these graphs. Either
that or make support for clicking on an image to give you the
full-scale version of it as a popup.}

Graphing the longitude against the record number reveals somewhat
similar results, that the satellite generally sweeps from west to
east: increasing longitude. However it is not exactly as I would
expect based on the hand-drawn diagram from above.
◊todo{Maybe do figure references}
I am not sure why that happens.

◊img["longitude-376-3.png"]
