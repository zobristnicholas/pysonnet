# install with: pip install -e /path/to/repository
# to make an editable pip install from a cloned git repository
from setuptools import setup, find_packages


def get_version(path):
    with open(path, "r") as f:
        for line in f.readlines():
            if line.startswith('__version__'):
                sep = '"' if '"' in line else "'"
                return line.split(sep)[1]
        else:
            raise RuntimeError("Unable to find version string.")


setup(name='pysonnet',
      version=get_version('pysonnet/projects.py'),
      description='Python tools for working with Sonnet E&M',
      url='http://github.com/zobristnicholas/pysonnet',
      author='Nicholas Zobrist',
      license='GNU GPLv3',
      packages=find_packages(),
      install_requires=['numpy', 'scipy', 'matplotlib', 'pytest', 'pyyaml',
                        'psutil'],
      zip_safe=False,
      include_package_data=True,
      package_data={'': ['*.yaml']},)
