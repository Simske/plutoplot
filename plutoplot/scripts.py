import argparse


def format_ini() -> None:
    from .io import Pluto_ini

    parser = argparse.ArgumentParser(description="Fix indentation in pluto.ini")
    parser.add_argument('filename')
    args = parser.parse_args()

    Pluto_ini(args.filename).write()
