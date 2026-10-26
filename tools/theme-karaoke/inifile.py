"""Minimal ordered reader/writer for USDX theme .ini files."""

import re
from collections import OrderedDict


class Ini:
    """Section names are case-insensitive, like in the game."""

    def __init__(self):
        self.sections = OrderedDict()
        self._names = {}           # lower-case name -> name as stored

    def _name(self, name):
        return self._names.get(name.lower(), name)

    @classmethod
    def read(cls, path):
        ini = cls()
        cur = None
        with open(path, encoding="utf-8", errors="replace") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith((";", "#", "/", "*")):
                    continue
                m = re.match(r"^\[([^\]]+)\]$", line)
                if m:
                    name = ini._name(m.group(1))
                    ini._names[name.lower()] = name
                    cur = ini.sections.setdefault(name, OrderedDict())
                    continue
                if cur is None or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                cur[k.strip()] = v.strip()
        return ini

    def __contains__(self, name):
        return self._name(name) in self.sections

    def get(self, name):
        return self.sections.get(self._name(name))

    def set(self, name, values=None, replace=True):
        """Set a section. With replace=False the keys are merged in."""
        values = OrderedDict(values or {})
        name = self._name(name)
        self._names[name.lower()] = name
        if replace or name not in self.sections:
            self.sections[name] = values
        else:
            self.sections[name].update(values)
        return self.sections[name]

    def remove(self, name):
        name = self._name(name)
        self.sections.pop(name, None)
        self._names.pop(name.lower(), None)

    def remove_prefix(self, prefix, keep=()):
        for name in list(self.sections):
            if name.lower().startswith(prefix.lower()) and name not in keep:
                del self.sections[name]
                self._names.pop(name.lower(), None)

    def write(self, path, header=""):
        out = [header] if header else []
        for name, kv in self.sections.items():
            out.append("[%s]" % name)
            for k, v in kv.items():
                out.append("%s = %s" % (k, v))
            out.append("")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(out))
