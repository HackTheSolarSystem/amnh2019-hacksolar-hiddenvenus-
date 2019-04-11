import urllib.request
import urllib.error
import os.path
import os
import shutil

# I don't wanna think about the version. If I request an orbit, I
# should get the latest version of the orbit, unless I specify
# otherwise.
#
# I don't wanna think about paths or downloads. I want python to
# detect if a file or orbit is not there and download the information
# for me.
with open('record-order') as f:
    orbits = {}
    for line in f:
        path = line[:-1]
        name = path.split('/')[-1]
        number = int(name[1:5])
        version = int(name.split('_')[-1])
        if number in orbits:
            orbits[number].append(path)
        else:
            orbits[number] = [path]

f_bidr_root = "http://pds-geosciences.wustl.edu/mgn/mgn-v-rdrs-5-bidr-full-res-v1/"
project_root = os.path.dirname(os.path.abspath(__file__))
data_root = os.path.join(project_root, 'data')

def gen_url(number, version, filename):
    return f'{f_bidr_root}{orbits[number][version - 1]}/{filename.upper()}'

def gen_local_path(number, version, filename):
    return os.path.join(data_root, orbits[number][version - 1], filename.upper())

def file_exists(number, version, filename):
    return os.path.exists(gen_local_path(number, version, filename))

def download_orbit_file(number, version, filename):
    """Fetch particular file from internet mirror."""
    url = gen_url(number, version, filename)
    path = gen_local_path(number, version, filename)
    try:
        local_file, headers = urllib.request.urlretrieve(url)
    except urllib.error.URLError as e:
        print("Something likely wrong with internet connection.")
        raise e
    shutil.move(local_file, path)

def get_orbit_file_path(number, filename, version=None):
    """Download file if need be and return file's path on local machine."""
    # Use latest version if none given
    if version is None:
        version = len(orbits[number])
    local_path = gen_local_path(number, version, filename)
    orbit_dir = os.path.dirname(local_path)
    header = None
    if not os.path.exists(orbit_dir):
        os.makedirs(orbit_dir)
    if not file_exists(number, version, filename):
        download_orbit_file(number, version, filename)
    return local_path
