from setuptools import setup
import versioneer

setup(
    name="plutoplot",
    packages=['plutoplot'],
    install_requires=[
        'numpy',
        'matplotlib'
    ],
    entry_points={
        'console_scripts': [
            'pluto-format-ini = plutoplot.scripts:format_ini'
        ]
    },
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),

)
