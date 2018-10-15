from collections import OrderedDict
from itertools import zip_longest


class Pluto_ini(OrderedDict):
    """Parser for Plutocode initialization file pluto.ini"""

    class Section(OrderedDict):
        def __init__(self, name):
            super().__init__()
            self.name = name

        def _align(self):
            length = []
            for key, value in self.items():
                if isinstance(value, str):
                    length.append((len(key), len(value)))
                else:
                    length.append((len(key), *[len(v) for v in value]))
            return [max(i) for i in zip_longest(*length, fillvalue=0)]

        def __str__(self):
            colwidth = self._align()
            out = "[{}]\n".format(self.name)
            for key, value in self.items():
                out += "{}{}\n".format(rpad([key], colwidth), lpad(value, colwidth[1:]))
            return out


    def __init__(self, path):
        super().__init__()
        self.path = path

        self.parse()

    def parse(self, txt=None):
        if txt is None:
            with open(self.path, 'r') as f:
                lines = [l.strip() for l in f.readlines()]
        else:
            lines = [l.strip() for l in txt.split("\n")]

        section = None
        for line in lines:
            if not line:
                continue
            elif line[0] == '[' and line[-1] == ']':
                section = line[1:-1]
                self[section] = self.Section(section)
            else:
                segments = line.split()
                if len(segments) > 2:
                    self[section][segments[0]] = segments[1:]
                else:
                    self[section][segments[0]] = segments[1]

    def __str__(self):
        out = ""
        for section in self.values():
            out += str(section) + "\n\n"
        return out

    def write(self, path=None):
        if path is None:
            path = self.path

        with open(path, 'w') as f:
            f.write(str(self))


def rpad(text, colwidth):
    if isinstance(text, str):
        text = [text]
    out = ""
    for txt, col in zip(text, colwidth):
        pad = col - len(txt) + 1
        out += txt + " " * pad
    return out

def lpad(text, colwidth, spacer=2):
    if isinstance(text, str):
        text = [text]
    out = ""
    for txt, col in zip(text, colwidth):
        pad = col - len(txt) + spacer
        out += " " * pad + txt
    return out
