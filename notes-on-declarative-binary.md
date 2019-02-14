It would be nice to digitize these binary formats.

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

I guess what I'm going for here is something like the `attrs`
interface, but for binary data.

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
