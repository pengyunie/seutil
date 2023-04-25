from random import shuffle
from typing import *

"""
Miscellaneous utility functions.
"""

T = TypeVar("T")


def shuffle_data(items: Sequence[T]) -> Sequence[T]:
    """
    Randomly shuffles the data.
    """
    ran = list(range(len(items)))
    shuffle(ran)
    return [items[i] for i in ran]


def get_num_params(vocab_size, num_layers, num_neurons):
    """
    Returns the number of trainable parameters of an LSTM.

    Args:
        vocab_size (int): The vocabulary size
        num_layers (int): The number of layers in the LSTM
        num_neurons (int): The number of neurons / units per layer

    Returns:
        int: The number of trainable parameters
    """
    num_first_layer = 4 * (num_neurons * (vocab_size + num_neurons) + num_neurons)
    num_other_layer = 4 * (num_neurons * 2 * num_neurons + num_neurons)
    num_softmax = vocab_size * num_neurons + vocab_size

    return num_first_layer + (num_layers - 1) * num_other_layer + num_softmax


def iter_len(iterator: Iterable) -> int:
    """
    Counts the length with the iterator.
    """
    return sum(1 for _ in iterator)


# Human-readable numbers

POWERS = [10 ** x for x in (3, 6, 9, 12, 15, 18, 21, 24)]
HUMAN_READABLE_POWERS = ('K', 'M', 'B', 'T', 'Qa', 'Qi', 'Sx', 'Sp')


def itos_human_readable(value: int, precision: int = 1) -> str:
    """
    Converts a large integer to a human-readable string representation.
    :return the human-readable string representation of the int.
    :raises TypeError if the value passed was unable to be coaxed into int.
    """
    try:
        value = int(value)
    except (TypeError, ValueError) as e:
        raise TypeError("Value can not be converted to int: {}".format(value))

    if value < POWERS[0]:
        return str(value)
    for ordinal, power in enumerate(POWERS[1:], 1):
        if value < power:
            chopped = value / float(POWERS[ordinal - 1])
            fmt = "{0:." + str(precision) + "f}"

            formatted = fmt.format(chopped)
            if "." in formatted:
                formatted = formatted.rstrip("0").rstrip(".")
            # end if
            return formatted + HUMAN_READABLE_POWERS[ordinal - 1]
    return str(value)


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


# Class Property

class ClassPropertyDescriptor(object):

    def __init__(self, fget, fset=None):
        self.fget = fget
        self.fset = fset

    def __get__(self, obj, klass=None):
        if klass is None:
            klass = type(obj)
        return self.fget.__get__(obj, klass)()

    def __set__(self, obj, value):
        if not self.fset:
            raise AttributeError("can't set attribute")
        type_ = type(obj)
        return self.fset.__get__(obj, type_)(value)

    def setter(self, func):
        if not isinstance(func, (classmethod, staticmethod)):
            func = classmethod(func)
        self.fset = func
        return self

def classproperty(func):
    if not isinstance(func, (classmethod, staticmethod)):
        func = classmethod(func)

    return ClassPropertyDescriptor(func)
