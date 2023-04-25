import argparse
from typing import *

from .LoggingUtils import LoggingUtils


class Option:
    def __init__(self):
        self.name = str()
        self.type = "str"
        self.str_value = str()


class StoreInDict(argparse.Action):
    # def parse_values(self, values) -> Tuple[Sequence[Option], Sequence[str]]:
    #     i = 0
    #     length = len(values)
    #
    #     args = list()
    #     options = list()
    #     new_option = None
    #
    #     while i < length:
    #         cur_item = values[i]
    #         if cur_item.startswith("-"):
    #             if new_option is not None:
    #                 options.append(new_option)
    #             # end if
    #             new_option = Option()
    #             # Value
    #             if "=" in cur_item:
    #                 new_option.
    #     # end while
    #     if new_option is not None:
    #         options.append(new_option)
    #     # end if
    #     return options, args


    def __call__(self, parser, namespace, values, option_string=None):
        d = getattr(namespace, self.dest)
        types = dict()
        for opt in values:
            try:
                name, value = opt.split("=", 1)
            except:
                name = opt
                value = True
            # end try
            name = name.lstrip("-")
            if ":" in name:
                name, types[name] = name.split(":", 1)
            else:
                types[name] = ""
            if name in d:
                d[name].append(value)
            else:
                d[name] = [value]
        for name in d:
            if not types[name] == "list" and len(d[name]) == 1:
                d[name] = d[name][0]
            # end if
            if types[name] != "":
                d[name] = eval("{}(\"{}\")".format(types[name], d[name]))
                continue
            # end if
            try:
                intval = int(d[name])
            except:
                pass
            else:
                d[name] = intval
                continue
            # end try
            try:
                floatval = float(d[name])
            except:
                pass
            else:
                d[name] = floatval
                continue
            # end try
        setattr(namespace, self.dest, d)


def main(argv, actions: Dict[str, Callable], normalize_options: Callable[[Dict], Dict] = None):
    """
    Main function for command line option parsing, in the form of "THIS action options...",
    Where each option is in the form of "-name=value".
    :param argv: The command line inputs, without the name of the script (sys.argv[1:]).
    :param actions: The mapping from action name to action function.
    :param normalize_options: Optional function to normalize options, by default identical function.
    """
    logger = LoggingUtils.get_logger("CliUtils.main")
    logger.info("Starting")

    if normalize_options is None:
        normalize_options = lambda opts: opts

    if len(argv) == 0 or argv[0].startswith("-"):
        action = "default_action"
        cli_options = argv
    else:
        action = argv[0]
        cli_options = argv[1:]
    # end if

    # Prevent distinguish between positional arguments and optional arguments (HACK)
    p = argparse.ArgumentParser(prefix_chars=' ')
    p.add_argument("options", nargs="*", action=StoreInDict, default=dict())
    options = p.parse_args(cli_options).options

    # normalize options
    options = normalize_options(options)

    if action in actions:
        actions[action](**options)
    else:
        print("No such action {}".format(action))
        print("Available actions: {}".format(list(actions.keys())))
    # end if

    logger.info("Terminating")
    return
