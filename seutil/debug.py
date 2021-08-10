import collections
from typing import Any, Dict, List, Optional

from varname import argname2


class Reporter:

    def __init__(self):
        self.history: Dict[str, List[Any]] = collections.defaultdict(list)

    def add_to_history(self, name, value):
        self.history[name].append(value)

    def generate_report(self) -> str:
        s = "===== Report =====\n"
        s += f"Inspected {len(self.history)} variables with {sum(len(x) for x in self.history.values())} values\n"
        for name, values in self.history.items():
            s += f"--- {name}\n"
            s += f"count: {len(values)}; unique count: {len(set(values))};\n"
        s += "==================\n"
        return s


default_reporter = Reporter()


def inspect(
        var: Any,
        name: Optional[str] = None,
        reporter: Reporter = default_reporter,
):
    if name is None:
        name = argname2("var", vars_only=False)
    reporter.add_to_history(name, var)


def report(
        reporter: Reporter = default_reporter,
):
    print(reporter.generate_report())
