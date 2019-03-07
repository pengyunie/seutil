from pathlib import Path
import numpy as np
import random
import subprocess
from typing import *

from .IOUtils import IOUtils


class Stream:
    """
    Streams help manipulate sequences of objects.
    """
    def __init__(self):
        self.items = list()
        return

    @classmethod
    def of(cls, one_or_more_items):
        """
        Get a new stream from the item / items.
        :param one_or_more_items: is converted to list with builtin `list` function.
        """
        stream = Stream()
        if one_or_more_items is not None:
            stream.items = list(one_or_more_items)
        # end if, if
        return stream

    @classmethod
    def of_files(cls, dir_path: Union[str, Path]):
        """
        Get a stream of the files under the directory.
        """
        with IOUtils.cd(dir_path):
            cmd_find = "find -mindepth 1 -maxdepth 1 -type f"
            files = subprocess.run(["bash","-c",cmd_find], stdout=subprocess.PIPE).stdout.decode("utf-8").split("\n")[:-1]
        # end with
        files = [file[2:] for file in files]
        stream = cls.of(files)
        stream.sorted()
        return stream

    @classmethod
    def of_dirs(cls, dir_path: Union[str, Path]):
        """
        Get a stream of the sub-directories under the directory.
        """
        with IOUtils.cd(dir_path):
            cmd_find = "find -mindepth 1 -maxdepth 1 -type d"
            dirs = subprocess.run(["bash","-c",cmd_find], stdout=subprocess.PIPE).stdout.decode("utf-8").split("\n")[:-1]
        # end with
        dirs = [dir[2:] for dir in dirs]
        stream = cls.of(dirs)
        stream.sorted()
        return stream

    def filter(self, predicate_func: Callable[[object], bool]):
        """
        Returns a stream consisting of the elements of this stream that match the given predicate.
        """
        return Stream.of(item for item in self.items if predicate_func(item))

    def count(self):
        return sum(self.items)

    def reduce(self, count_func: Callable[[str], float] = lambda x: 1):
        return sum([count_func(f) for f in self.items])

    def sorted(self, key: Callable[[str], object] = lambda f: f,
               reverse: bool = False):
        """
        Sorts the list of files in the dataset.
        """
        list.sort(self.items, key=key, reverse=reverse)
        return self

    def map(self, map_func: Callable[[str], object],
            errors: str = "raise", default: object = ""):
        def new_items_generator():
            for item in self.items:
                try:
                    new_item = map_func(item)
                except:
                    if errors == "ignore":
                        yield default
                    else:
                        raise
                else:
                    yield new_item
            # end for
        # end def
        return Stream.of(new_items_generator())

    def peak(self, peak_func: Callable[[str], None],
             errors: str = "ignore"):
        for item in self.items:
            try:
                peak_func(item)
            except:
                if errors == "ignore":
                    continue
                else:
                    raise
        # end for
        return self

    def split(self, fraction_list: List[float],
              count_func: Callable[[str], float] = lambda x: 1):
        """
        Splits the dataset as each part specified by the fractions (assumed to sum up to 1).
        Splitting is done by finding the cutting points. If randomization is needed, call shuffle first.
        :param count_func: customize the number of data counts in each file.
        """
        if self.is_empty():
            return tuple(Stream() for i in range(len(fraction_list)))

        count_list = [count_func(f) for f in self.items]
        cum_count_list = np.cumsum(count_list)
        cum_expected_count_list = [f * cum_count_list[-1] for f in np.cumsum(fraction_list)]
        cut_index_list = []
        last_i = 0
        for i, cum_count in enumerate(cum_count_list):
            if cum_count >= cum_expected_count_list[len(cut_index_list)]:
                last_i = i+1
                cut_index_list.append(i+1)
                if len(cut_index_list) >= len(cum_expected_count_list):
                    break
                # end if
        # end for if
        if last_i != len(cum_count_list):
            cut_index_list.append(len(cum_count_list))
        # end if
        cut_index_list.insert(0,0)
        return tuple(Stream.of(self.items[cut_index_list[i]:cut_index_list[i + 1]]) for i in range(len(cut_index_list) - 1))

    def shuffle(self, seed=None):
        """
        Shuffles the list of files in the dataset.
        """
        random.seed(seed)
        random.shuffle(self.items)
        return self

    def get(self, index: int):
        return self.items[index]

    def is_empty(self):
        return len(self.items) == 0

    def __getitem__(self, item):
        new_items = self.items.__getitem__(item)
        if not isinstance(item, slice):
            new_items = [new_items]
        return Stream.of(new_items)

    def __setitem__(self, key, value):
        return self.items.__setitem__(key, value)

    def __delitem__(self, key):
        return self.items.__delitem__(key)

    def __iter__(self):
        return self.items.__iter__()

    def __len__(self):
        return self.items.__len__()

    def __str__(self):
        return "Stream with {} items".format(len(self.items))

    def __repr__(self):
        return self.__str__()

    def __add__(self, other):
        if isinstance(other, Stream):
            return Stream.of(self.items+other.items)
        else:
            raise NotImplementedError
