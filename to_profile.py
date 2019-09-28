from f_bidr import read_logical_records
from f_bidr_data import get_orbit_file_path as orbit
import imageio
import numpy as np
from attrs_structs import RecordTypes as R


orbit_paths = [
    orbit(376, 'file_15', 3),
    orbit(377, 'file_15', 3),
    orbit(378, 'file_15', 3),
    orbit(379, 'file_15', 3),
    orbit(380, 'file_15', 3),
    orbit(381, 'file_15', 3),
    orbit(382, 'file_15', 4),
    orbit(383, 'file_15', 3),
    orbit(384, 'file_15', 3),
    orbit(385, 'file_15', 4),
]
"""
orbits = [read_logical_records(p, 200) for p in orbit_paths]
"""
read_logical_records(orbit_paths[0])

# From orbits 514 to 537 is an unbroken chain of downloaded orbits all
# at version 1.
