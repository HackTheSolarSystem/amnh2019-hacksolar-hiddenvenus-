Basic Idea
==========

I'd like to read these files in a way that the code for reading the
binary data describes the binary data as well.

Sounds like this would be accomplished by something similar to
[attrs](https://github.com/python-attrs/attrs), but for binary data
rather than classes.

There's some characteristics that would make this nice and comfy to
use:

- Some binary formats are used in more than one place, and they
  described relative to something else (ie the 0th byte of this binary
  record is contained within some larger binary record).
- The length of some fields is dependent on prior fields read in the
  record.
- Each number has an interpretation, either as an ascii character, or
  little-endian integer, or as an enumeration for other things. It
  would be nice to just explain in terms of the bytes identified, and
  how to interpret them. For instance:

If I refer to page numbers "a report", I'm referring to
`papers+documents/MGN-FBIDR-SIS-SDPS-101-RevE.pdf`, the paper
describing the binary format of F-BIDRs.

I'm prioritizing readability over speed. Readability in the sense that
reading the code tells you what the binary data looks like. Basically,
just by reading the format of the binary data, you could figure out
how to parse it by hand, without having to look at any how-to code.

Examples, discussion, problems
==============================

What could this declarative binary file descriptor/reader look like?

```
records(
    record(desc='Logical Record', readAtLeastBytes=20,
           bytes=record(desc='Logical Record Length', bytes=[11,19],
                        interpretation=decimalAsASCIISting)
                        )
    record(desc='NJPL Primary Label Type', bytes=[0,11],
           interpreter=interpFunc)

...
```

and I can already start re-writing this a bit, using some predefined
records functions:

```
records(
    record(desc='Logical Record', readAtLeastBytes=20,
           bytes=records.ascii_number(bytes=[11,19], desc='Logical Record Length')
                        )
    record(desc='NJPL Primary Label Type', bytes=[0,11],
           interpreter=interpFunc)

...
```

Nesting records and relative locations presents some difficulty: what
is a location relative to? If I say "the previous record", that
presents some ambiguity:

```
records(
    desc=record(bytes=[0,10])
    bytes=record(bytes=[0,10], relative=True))
```

What bytes are the record in for the `bytes` keyword parameter
referring to? Are they relative to the bytes starting at `records`
(which means relative to 0) or relative to the bytes after the record
for `desc` (which means relative to byte 11, the byte after byte 10).

A class would be nicer to write, I think:

```
class Logical_record:
    NJPL_primary_label_type = records(start=0, length=12, interp=NJPLFunc)
    length = records.ascii_decimal(length=8)
    header = Secondary_header

# Maybe use built-in python enumeration instead of a dict.
class Secondary_header:
    BIDR_type = records(start=0, length=2, 
                    interp=[records.int(bytes=2),
                    records.enum({ 1 : 'per-orbit parameter record',
                                   2 : 'image data record',
                                   4 : 'processing parameter/monitor records',
                                   8 : 'processed radiometer records'})])
    remaining_len = records.int(length=2)
```

I dunno how to make this work, though. So let's stick to functions.
Let's try to write out the records from the book in this declarative
style:

a record should basically be an extension of these interpretations.
records returns a function that can interpret a source into one or
more fields, each field being some kinda interpretation.

```
# file is one or more logical records
annotation_block = records(
    record_start=0,
    data_class=record(
        record_length=1,
        interpretation=Interpretations.enumeration({
            1 : "Per Orbit Parameters",
            2 : "Image Data, sinusoidal projection, multi-look",
            34 : "Image Data, sinusoidal projection, single-look",
            66 : "Image Data, oblique sinusoidal projection, multi-look",
            98 : "Image Data, oblique sinusoidal projection, single-look",
            4 : "Processing Parameters, sinusoidal projection",
            68 : "Processing Parameters, oblique sinusoidal projection",
            8 : "Processed Radiometer data",
            40 : "Cold Sky Calibration data",
            16 : "Processing Monitor Records",
        })),
    remaining_record_length=record(
        record_length=1,
        interpretation=Interpretations.integer),
    annotation_label=record(
        record_length=None (means just take the rest),
        interpretation=Interpretations.plain))

secondary_header = records(
        record_start=0,
        BIDR_type=record(
            record_length=2,
            interpretation=Interpretations.enumeration({
                1 : 'per-orbit parameter record',
                2 : 'image data record',
                4 : 'processing parameter/monitor records',
                8 : 'processed radiometer records'
            })),
        remaining_record_length=record(
            record_length=2,
            interpretation=Interpretations.integer),
        orbit_number=record(
            record_length=2,
            interpretation=Interpretations.integer),
        annotations=annotation_block)
logical_record = records(
        record_start=0,
        NJPL_label=record(
            record_length=12,
            interpretation=Interpretations.ascii_string),
        remaining_record_length=record(
            record_length=8,
            interpretation=Interpretations.ascii_decimal),
        header=secondary_header,
        data=record(
            record_length=None,
            interpretation=plain))
```

I'm pretty satisfied with this. There are common records, though.
Particularly for integers and strings. Interpretations might be good
to have, but not to write. Because it's much easier to write
`Interpretations.integer(length=1)` than whatever I was writing. Or
`Interpretations.plain()`.

In fact, it may be better to make interpretations into basic records.
And say that a record is any one of the predefined ones, or a series
of named records.

A record's length is:

- value of record_length parameter, if provided.
    - If a remaining_record_length parameter is given otherwise, then
      it's the sum of the lengths of all the records given before
      remaining_record_length, plus remaining_record_length.
- sum of length of all records otherwise.

some rules:

- A record is a function that takes a bytes object and returns two
  values: the interpretation of consumed bytes, and the remaining
  unconsumed bytes, or `None` if no bytes were unconsumed.
- A when referring to a record's record_length, it refers to any of
  the above ways to get a record's length.
- If a record has no record_length, then it is as long as the source
  it will consume. We'll call such a record's length *unknown*.
- If a record has a record as it's record_length, then it's length is
  *in-record*.
- Records of unknown length or in-record length must come after a
  record_length or remaining_record_length parameter.
- The record_length or remaining_record_length parameters may be
  themselves records, but must be of known length.
- A record may only contain one record of unknown length (nope, I have
  to work around this).
    - A record my only contain one record of unknown length which is
      not bounded in some way by an in-record or known length. Nah,
      this is still foggy.

I think my problem with the more complicated ideas I'm having is that
one of my assumptions is false: composition of records is not just a
blind combination of simpler records. The nature of later records may
depend on earlier records, whether they determine how long later
records are, or even the binary format of those records.

Some records are simple. Combination of some records can stay simple.

One thing to do is to just wrap all of the complicated stuff in custom
record functions, and keep the method of composition simple. This
could lead to overdeep nesting of attributes in dicts resulting from
composed records. Er... actually, no. This is false. Some records may
just be a level deeper than needed, but I think max depth would remain
the same. Because what I'm picturing in my head is just moving all
records that are interdependent on one another into one custom record
function which would return a dict of attributes and interpreted
values.

Problems
========

The actual record to use later on can depend on earlier records. An
example is the secondary header on page 3-12 of the report. The header
contains, among other things, the following records:

- BIDR secondary label type
- data annotation label

Both the length and format of the data annotation label depend on the
type of the label: is this image data, radiometer data, etc?

I'm not missing something, one of my basic assumptions about this task
is wrong: that composing records together is just a matter of
describing the correct order of records and their lengths, and that
this can be done in a way where composed records are independent of
one another. That's now how these binary formats work. Later records
depend on the interpreted values of earlier records.

- Contiguous series of records is one form of dependence. The
  composition function should understand how many bytes each record
  consumes, so that it knows where the next record should start,
  assuming there's no blank space.
- Having the total length of a record be based on the binary data it
  will read is another (page 3-11 is an example: logical records in an
  F-BIDR file have a length that's written in the logical record
  itself).
- Having the way to interpret binary data be based on some of the
  binary data that's read (page 3-12 is an example: the length and
  format of the data annotation label is dependent on the type of the
  data, which is given in the secondary header).

To keep things totally declarative, I need to be able to declare these
relationships between records. That's a bit troblesome, because these
means that later records have to be able to refer to the future value
(once a file is read) of an earlier record in order to even start
making these relationships declarative.

- Produce some actual form of future/promise to use in the program?
  This sounds like a bad idea, given the format I'm using. Somehow, a
  future has to pop out of something, somewhere, and be used later. I
  don't have access to assignment, here.
- Use some naming convention such that the name refers to the value of
  the record. For example:

```
secondary_header = records(
    BIDR_secondary_label_type=RecordTypes.enumeration({
        1 : 'per-orbit parameter record',
        2 : 'image data record',
        4 : 'processing parameter/monitor records',
        8 : 'processed radiometer records'
    }),
    remaining_record_length=RecordTypes.integer(2),
    orbit_number=RecordTypes.integer(2),
    annotations=RecordTypes.case(
        case_value='./BIDR_secondary_label_type',
        cases={
            'per-orbit parameter record' : orbit_data_label,           
            'image data record' : image_data_label,                    
            'processing parameter/monitor records' :
                processing_parameter_label, 
            'processed radiometer records' : radiometer_data_label,
        }
    )
)
```

I can't see anything wrong with this. The composition function will
have to be able to lift the `case_value` metadata about the case type
record, find the right record and value, pull out that value, and then
run it against the cases.

I may need something more general, which uses boolean expressions
rather than strict equality with some value. This is sounding closer
and closer to a programming language. Hm... not sure how I feel about
that. I want to keep this simple, not invent a new burdensome syntax
to learn. As soon as it becomes as complicated as writing custom
record functions, I've hit a problem. But I think it's worth trying
out.

The more general `if` form could be handled by single-argument
lambdas that will eventually receive the value of the referred-to
record.

That being said, the case/if could be replaced by a lambda, too. That
would make this simpler, and stick to the host language's syntax. I
like this better.

I think this is a good place to stop. Any more complicated, and I
think I've hit self-defeating.

Keep this simple: the referred to value must come from a sibling
record (within the same set of composed records), and cannot reach
upward into parent records (as the path notation suggests). Do away
with that entirely, just refer to a name, use a lambda, replace `case`
with the `if` form entirely, sticking to a lambda expression.

This will be one break from form for the record composition function,
which normally requires record functions. The result of `RecordTypes.If` 
will be a function which requires the value of the referred-to record,
which means the record composition function will have to look out for
this specifically.

Logical Record
    NJPL primary label type
    NJPL primary label length
    Secondary Header
        BIDR Secondary label type
        BIDR Secondary label length
        Orbit Number
        Annotation Block (format depends on BIDR Secondary label type)
            Data Class
            Data Annotation label length
            Data Annotation label (format depends on BIDR Secondary label type, but can also use Data Class to indirecty guess the former record's value)
    Data Block

Reaching into parent fields isn't impossible. I can give the records
composition function an optional argument to pass in record values
read so far. I'd just have to work out a way of traversing this dict
relative to a given attribute.

Coming back to this another day, I think it would be better to
implement this ability to reference parent records than to rely purely
on custom record functions. Because in order to use a custom function
to implement this functionality, all records involved in the
relationship would have to become involved in this function, and
chances are all the records scanned along the way would have to as
well. The custom record function would be just as complex as trying to
handle it generally, and I'll have to handle it generally over and
over again wherever that appears.

Another note: having the length of one record be based on another
record can be handled through something like `RecordTypes.if`.
