# install with: pip install -e /path/to/repository
# to make an editable pip install from a cloned git repository
from setuptools import setup, find_packages

setup(name='pysonnet',
      version='0.0.1',
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
