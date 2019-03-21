from setuptools import setup
from plutoplot import __version__

setup(
    name="plutoplot",
    version=__version__,
    packages=['plutoplot'],
    install_requires=[
        'numpy',
        'matplotlib'
    ],
    entry_points={
        'console_scripts': [
            'pluto-format-ini = plutoplot.scripts:format_ini'
        ]
    }
)
