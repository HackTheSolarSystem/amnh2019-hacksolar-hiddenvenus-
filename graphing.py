import matplotlib.pyplot as plt
from f_bidr import *

def get(records, *names):
    outputs = []
    for name in names:
        if isinstance(name, (str, int)):
            outputs.append([r[name] for r in records])
            #return [r[name] for r in records]
        elif callable(name):
            outputs.append([name(r) for r in records])
            #return [name(r) for r in records]

    if len(names) == 1:
        return outputs[0]
    else:
        return outputs

def graph(records, *names, **axargs):
    stuff = get(records, *names)
    if len(names) == 1:
        plt.scatter(range(len(stuff)), stuff)
    else:
        plt.scatter(stuff[0], stuff[1])
    ax = plt.gca()
    if axargs:
        ax.set(**axargs)
    plt.show()
