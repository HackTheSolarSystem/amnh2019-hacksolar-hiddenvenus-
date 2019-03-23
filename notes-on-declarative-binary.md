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

Later Notes (3/15/19)
=====================

Another oversight: any compound record may contain another compound
record, and so they all need access to the same information. They all
need access to the whole root record and the ability to navigate it.
Ifs need to refer to values in the root record as it's being made, and
this was okay because Series had those root records, and Ifs were used
in Series. I put the burden on the Series `__call__` method to handle
retrieval, though. So If records never got access to the root record
themselves, but what if an If record contained a series record? How
does that contained series record get access to the root dictionary?
What if an If contains an If?

One possibility is to give all the compound records the root record
and have any other compound record be able to grab that root record
from the containing compound record.

A second possibility just occurred to me: the If records the primary
fly in my soup right now. If I could take the record function an If
returns and then process that as if it were part of the original
series of records to process, then I may be fine. 

A third possibility would dramatically speed up development time: give
all records the root record. All record functions take a source and
optional root record, if they want to use it. All other arguments come
afterward and are part of that record's specifically call signature.
This way, I can write in functions for records I haven't fully worked
out yet in my scheme, and I can work them out later. Works before
perfect is something I can live with. Shit, celebrate even.

### Possibility One

> So, `If` records will have to calculate the record value themselves
> from the dictionary handed down to them.

Records may not have to know their own name... but with the changes
introduced it won't kill anyone. I'm already handing each compound
record more of a role in how they produce their values, rather than
leaving the bulk of that knowledge specified in the Series.__call__
method. This would remove the need for the "to_fill" dictionary, which
reduces how much I need to pass into each record function. Cleans up
the connections between them.

At the same time, if I want looking through sibling records and 'prior
records' to all happen with paths, then it's valuable to have the
dictionary from a Series record already "installed" in the parent
record, and have the Series record just modify that dictionary. (prior
records are records that were already interpreted, which are any
descendant record, and any sibling of a descendant record that exists
at the time the record is being interpreted)

> Series records return dicts. List records return lists. Those dicts
> and lists may contain any value that any other record function could
> produce, simple or compound. Other compound records can return
> anything that any other record can return, simple or compound.

> Using string paths forces you to be aware of different record types
> and their interactions ahead of time. You have to create a notation
> that will support each new thing you add. It may be better to
> replace the path (a stand-in for a future value) with another lambda
> (a stand-in for a future value!). This way the user can do whatever
> they want as long as it works in python.

~~~
record = R.Series(
    nums=R.List(3*[R.Integer(4)]),
    record_type=R.If(
        lambda root: root['nums'][0], # value to refer to
        lambda value: R.Integer(4) if value == 0 else 
            R.Integer(4, signed=True)),
~~~

Is it worth splitting this up into two functions? One to specify the
value, and then one to act on the value and return a correct record
function? Part of me says 'hell no', why use two functions when you
can use one? The other part of me says "there's no other way to give
this record a name conveniently. Python lambdas are single
expressions. The only other way to give a name is to use a nested
lambda. Something I'm pretty sure most python users aren't used to,
and something that Scheme users replaced with the let form.

> Keep two lambda arguments.

Requiring an If to use a root record now makes them truly not make
sense outside of Series, unless you pass in a root record yourself.

> Make records aware of their names. Only really important for S

For now, we can assume that the root record is a Series, but
eventually they may be lists. Any compound record, really.

Is a pipe a compound record? I think not... but it kinda depends on
what records it contains. It's entirely dependent on which records it
contains.

### Possibility Two

So the Series `__call__` would become more like

```
class Series:
    def _process_record(self, record, root_dict, given_dict):
        # ...
        # the main logic of the loop body
        if isinstance(record, R.Series):
            # stuff
        elif isinstance(record, R.If):
            # stuff
        else:
            # stuff

    def __call__(self, root_dict, given_dict):
        # ...
        for name, func in self.records.items():
            result = _process_record(record, root_dict, given_dict)
            while isARecord(result):
                result = _process_record(result, root_dict, given_dict)
        
```

Ifs just decide on a record function. They don't have to have the
brains to process that record. I just currently have them processing
the record.

A downside of this is that this keeps the know-how of processing Ifs
inside of the Series record call method. Any later compound records
will likely fall suit.

### Possibility Three

With this, some of the If series functions could be done quickly as
hand functions. SOmething like:

~~~
def thisRecord(source, root_record):
    interesting_piece = root_record['logical_record']['2ndry_header']['type']
    if interesting_piece == 'orbit data':
        # use this particular record function.
    else:
        # use another record function.

F_BIDR = R.Series(
    # ...
    thing=thisRecord
    # ...
    )
~~~

It looks nothing at all like everything else, but the functions should
be a minority. Glue that connects things at "joints" where decisions
are made. With this, I no longer have to pull in all records to this
record function that would require the conditional... wait, I would.
Right now, record functions return a single value. I'd still have that
dictionary nesting problem. But at least the nesting problem is
possible now. It actually wasn't before.

This idea has become a cage. I liked it when it was a few flexible
pieces. Maybe I should drop work on it entirely, and just use the
useful pieces.

The series idea is still good. 

- Functions can return a single value, or a pair of key-value pairs to
  fill in more parts of a series. Or a callable as another record (not
  sure about keeping this, not necessary while there's other stuff
  around).
- Series now take a list of key-value pairs, instead of keyword
  arguments. keywords limit the useable names to python identifiers,
  and they allow for record functions to specify the names of the
  values that they return.

Later Notes (3/18/19)
=====================

I must leave copying/slicing the source as a model. It would be okay
for smaller files, but I'm coming face-to-face with how stonkingly
huge the largest image file is. I can stick with slices for now...

It's actually not that slow to read a logical record with the current
method. But it does take time, and there are so very many logical
records in the largest image data file.

I was able to get away with switching from working with bytes objects
to memoryviews of bytes objects. That gave me a lot of speed, but
still barely enough to work with files the size of FILE_15.

It's not just composition of Ifs and Series and present problems with
passing context. It's any user defined functions, too.

The things I've chosen to do at this point are:

- Restrict context to just the root record being passed everywhere.
- Give the root record the ability to keep track of the current record
  being processed, and the root record that kicked it all off.
- Keep If, Series, and List.
- Make Series and List "equal", in that they can both start off a
  record, because I've used that at least once, and because I think I
  can make it work pretty well.

Things I chose not to do:

- Have Series take key/value pairs instead of keyword arguments.
- Allow record functions to return a series of name/value pairs. The
  record functions are still returning one value, and the unprocessed
  data they haven't used.


Places where I'm having trouble:

- Reworking If. An If has no clue what record it will return, so it
  has no type for the parent record to be aware of, and so my
  type-specific approach for handling the processing of records falls
  apart at the If. I've got contradicting assumptions in this work,
  and they keep biting me.
    - The type of the parent and the type of the record being
      processed matter. The parent type dictates how the record being
      processed gets added to the parent. The child type dictates what
      data structure (DictRecord or ListRecord) gets used to store the
      created values. And I have this constraint because I want all
      members of root record to be available for reference as soon as
      they're known (it's possible for a list or series to store the
      interpreted values on the side until all records are
      interpreted, then add them to the root record all at once. This
      prevents sibling records from inspecting each other in the root
      record).
- Keeping the logic for processing records in one place.

Add `add` operation that takes care of the type details in adding
values to the root record could help. It can account for the type of
the current record, and the type of the record that was just
processed.

These constraints with trying to keep all the elements of the root
record accessible could leak into user-defined records, I thought.
On 2nd thought though, it's true but unimportant. Most users will
probably process some records and inspect their values
programmatically, not with If. I built what I built to capture common
patterns.

Later Notes (3/23/19)
=====================

Things have solidified. There are now record functions:

- A function which takes a memoryview and keyword arguments
  root_record and current (the main meta-record being parsed if there
  is one, and the current meta-record being parsed respectively).
- A callable whose `__call__` function has same signature as above and
  has a `.length` property. This allows meta-records to know their
  length before receiving input.

And meta-record functions. Meta-record functions just specify
relationships between basic records. They're not record functions
themselves, do not have to abide by those rules. There's a greater
degree of coupling allowed between the meta-records than there are
between metas and basic record functions.

Processing Series and Lists is done with `process_meta_record`. It's
come out a little weird, but it builds a tree iteratively rather than
recursively. One node at a time. This is done so that the root record
and current node are always available when we're processing the next
record.

There's a few things I haven't accounted for:

- Cooperation b/w custom record functions and meta-records. They work
  well with the pre-built record function callables, but not with
  things that can have arbitrary return values (like a Node, or a
  list, or a dict).
    - if a custom returns a Node, then it ought to overwrite the node
      getting processed rather than just get nested in it.
    - If a custom returns a dict or list, that's a bit problematic.
      Nodes whose values are lists or dicts are treated as
      meta-records, and that falls apart with custom records.
