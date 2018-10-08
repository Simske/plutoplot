from setuptools import setup
from plutoplot import __version__

setup(
    name="plutoplot",
    version=__version__,
    packages=['plutoplot'],
    install_requires=[
        'numpy',
        'matplotlib'
    ]
)
