"""Collection of entrypoints"""
import argparse


def format_ini() -> None:
    """Entrypoint to format `pluto.ini` file"""
    from .metadata import Pluto_ini

    parser = argparse.ArgumentParser(description="Fix indentation in pluto.ini")
    parser.add_argument("filename")
    args = parser.parse_args()

    Pluto_ini(args.filename).write()
