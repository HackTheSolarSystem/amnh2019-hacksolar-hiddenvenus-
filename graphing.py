import matplotlib.pyplot as plt
from f_bidr import *
from f_bidr_data import get_orbit_file_path as orbit
from images import *
import itertools

def get(records, *names):
    """For extracting per-record information from a list of orbits.
    Returns a list of data, or list of lists of data."""
    outputs = []
    for name in names:
        if callable(name):
            outputs.append([name(r) for r in records])
        else:
            outputs.append([r[name] for r in records])
            #return [r[name] for r in records]
    if len(names) == 1:
        return outputs[0]
    else:
        return outputs

# record_iter is an iterable of lists of records. For help with
# comparing different orbits.
def gets(record_iter, name):
    """Name here is limited to one name. Gets one field from multiple
    collections of records."""
    return [get(lst, name) for lst in record_iter]

def graph(records, *names, **axargs):
    stuff = get(records, *names)
    if len(names) == 1:
        plt.scatter(range(len(stuff)), stuff)
        ax = plt.gca()
        ax.set(xlabel='record #', ylabel=names[0])
    else:
        plt.scatter(stuff[0], stuff[1])
        ax = plt.gca()
        ax.set(xlabel=names[0], ylabel=names[1])
    if axargs:
        ax.set(**axargs)
    plt.show()

def find_first(lst, test):
    """Helpful for finding records within a particular lat/lon range."""
    for i in range(len(lst)):
        if test(lst[i]): 
            return i
