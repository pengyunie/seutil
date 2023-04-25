import copy
from typing import Any, Callable, Generic, Iterable, Optional, Tuple, TypeVar

TElem = TypeVar("TElem")
TValue = TypeVar("TValue")


class Trie(Generic[TElem, TValue]):
    """
    A Trie tree stores the mapping from sequences to values. Each item in the sequence is stored as a node in the tree, and sequences with the same prefix share the same node, to speed up the lookup.

    The tree is implemented recursively using dict, where each node is a dict of current node to its children. A special key `empty_elem` (by default empty string) is used to indicate a node has value.

    The value can be any object; the default `True` value is ok if the value is not important and only containment checking is needed.

    Using the default parameters of `empty_elem`, `join_func`, and `value` results in a classical trie tree for words.

    :param empty_elem: the empty element of this trie; by default empty string.
    :param join_func: the function to join a sequence of elements to a thing, used when reporting the sequence during traversing the trie; by default `"".join`.
    """

    MISSING = object()  # used to distinguish between None and missing values

    def __init__(
        self,
        empty_elem: TElem = "",
        join_func: Optional[Callable[[Iterable[TElem]], Any]] = lambda x: "".join(x),
    ):
        if join_func is None:
            join_func = lambda x: x
        self.empty_elem = empty_elem
        self.data = {}
        self.join_func = join_func

    def to_tree(self):
        """
        TODO: Converts the trie to a `seutil.ds.tree.Tree` (to be added).
        """
        raise NotImplementedError()

    def get(
        self, key: Iterable[TElem], default: Optional[TValue] = None
    ) -> Optional[TValue]:
        """
        Gets the value of the given key, or the default value if the key does not exist.
        """
        try:
            return self[key]
        except KeyError:
            return default

    def __getitem__(self, key: Iterable[TElem]) -> TValue:
        """
        Gets the value of the given key.
        :raises KeyError: if the key does not exist in the trie.
        """
        cur = self.data
        for c in key:
            if c not in cur:
                raise KeyError(f"Key {key} does not exist in the trie")
            cur = cur[c]
        if self.empty_elem not in cur:
            raise KeyError(f"Key {key} does not exist in the trie")
        return cur[self.empty_elem]

    def set(
        self, key: Iterable[TElem], value: TValue = True, exist_ok: bool = True
    ) -> TValue:
        """
        Sets the value of the given key.
        :param key: the key to set.
        :param value: the value to set, by default `True` if the value is not important.
        :param exist_ok: if the key already exists, whether to overwrite the value.
        :raises KeyError: if the key already exists and `exist_ok` is False.
        :return: the old value of the key, or `Trie.MISSING` if there was no old value.
        """
        cur = self.data
        for c in key:
            if c not in cur:
                cur[c] = {}
            cur = cur[c]
        if not exist_ok and self.empty_elem in cur:
            raise KeyError(f"Key {key} already exists in the trie")
        else:
            old_value = cur.get(self.empty_elem, self.MISSING)
            cur[self.empty_elem] = value
            return old_value

    def __setitem__(self, key: Iterable[TElem], value: TValue):
        self.set(key, value, exist_ok=True)

    def compute(
        self, key: Iterable[TElem], update_func: Callable[[Optional[TValue]], TValue]
    ) -> TValue:
        """
        Computes the value of the given key (potentially add/remove a key-value pair).
        Faster than get+set by avoiding searching for the key twice.
        :param key: the key to update.
        :param update_func: the function to update the value, which takes as input the old value (or `Trie.MISSING` if there was no old value), and returns the new value (or `Trie.MISSING` to indicate removing the key from trie).
        :return: the old value of the key, or `Trie.MISSING` if there was no old value.
        """
        cur = self.data
        for c in key:
            cur.setdefault(c, {})
            cur = cur[c]
        old_value = cur.get(self.empty_elem, None)
        cur[self.empty_elem] = update_func(old_value)
        if cur[self.empty_elem] == self.MISSING:
            del cur[self.empty_elem]
            self.prune()
        return old_value

    def remove(self, key: Iterable[TElem]) -> TValue:
        """
        Removes the key from the trie.
        :param key: the key to remove.
        :return: the old value of the key.
        :raises KeyError: if the key does not exist in the trie.
        """
        cur = self.data
        for c in key:
            if c not in cur:
                raise KeyError(f"Key {key} does not exist in the trie")
            cur = cur[c]
        if self.empty_elem not in cur:
            raise KeyError(f"Key {key} does not exist in the trie")
        value = cur[self.empty_elem]
        del cur[self.empty_elem]
        self.prune()
        return value

    def __delitem__(self, key: Iterable[TElem]):
        self.remove(key)

    def has_key(self, key: Iterable[TElem]) -> bool:
        """
        Checks if the key exists in the trie.
        """
        cur = self.data
        for c in key:
            if c not in cur:
                return False
            cur = cur[c]
        return self.empty_elem in cur

    def __contains__(self, key: Iterable[TElem]) -> bool:
        return self.has_key(key)

    def has_prefix(self, prefix: Iterable[TElem]) -> bool:
        """
        Checks if the prefix exists in the trie.
        """
        cur = self.data
        for c in prefix:
            if c not in cur:
                return False
            cur = cur[c]
        return True

    def __copy__(self):
        """
        Returns a shallow copy of the trie.
        """
        new_trie = Trie(self.empty_elem, self.join_func)

        def _copy(cur):
            new_cur = {}
            for k, v in cur.items():
                if k == self.empty_elem:
                    new_cur[k] = v
                else:
                    new_cur[k] = _copy(v)
            return new_cur

        new_trie.data = _copy(self.data)
        return new_trie

    def __deepcopy__(self, memo={}):
        """
        Returns a deep copy of the trie.
        """
        new_trie = Trie(self.empty_elem, self.join_func)
        new_trie.data = copy.deepcopy(self.data, memo)
        return new_trie

    def prune(self):
        """
        Prunes prefix nodes that lead to no value, usually after removal of a key.
        """

        def _prune(cur) -> Tuple[bool, list]:
            should_prune = True
            to_prune = []
            for c in cur:
                if c == self.empty_elem:
                    should_prune = False
                else:
                    should_prune_c, to_prune_c = _prune(cur[c])
                    if should_prune_c:
                        to_prune.append((cur, c))
                    else:
                        should_prune = False
                        to_prune += to_prune_c
            if should_prune:
                return True, []
            else:
                return False, to_prune

        _, to_prune = _prune(self.data)
        for cur, c in to_prune:
            del cur[c]

    def get_subtrie(self, prefix: Iterable[TElem]) -> "Trie[TElem, TValue]":
        """
        Gets the subtrie starting at the given prefix, with respect to this trie.
        If the prefix does not exist in this subtrie, an empty trie is returned.
        :param prefix: the prefix that the subtrie should start at.
        :return: the subtrie, which shares storage with the original trie (use `__copy__` or `__deepcopy__` to get a copy).
        """
        cur = self.data
        for c in prefix:
            if c not in cur:
                return Trie(self.empty_elem, self.join_func)
            cur = cur[c]
        new_trie = Trie(self.empty_elem, self.join_func)
        new_trie.data = cur
        return new_trie

    def get_subtrie_prefix_of(self, key: Iterable[TElem]) -> "Trie[TElem, TValue]":
        """
        Gets the subtrie that is bounded by the given key: all keys in the returned subtrie are prefix of the given key.
        If no prefix of the key exists in this subtrie, an empty trie is returned.
        :param key: the key that the subtrie should be bounded to.
        :return: the subtrie, which does not share structure, but shares values with the original trie (use `__deepcopy__` to get a deep copy).
        """
        cur = self.data
        new_trie = Trie(self.empty_elem, self.join_func)
        new_cur = new_trie.data
        for c in key:
            if self.empty_elem in cur:
                new_cur[self.empty_elem] = cur[self.empty_elem]

            if c not in cur:
                break
            else:
                new_cur[c] = {}
                new_cur = new_cur[c]
                cur = cur[c]

        if self.empty_elem in cur:
            new_cur[self.empty_elem] = cur[self.empty_elem]

        new_trie.prune()
        return new_trie

    def get_subtrie_using_elems(self, elems: Iterable[TElem]) -> "Trie[TElem, TValue]":
        """
        Gets the subtrie whose keys only use the given elements.
        :param elems: the elements that the subtrie can use.
        :return: the subtrie, which does not share structure, but shares values with the original trie (use `__deepcopy__` to get a deep copy).
        """
        new_trie = Trie(self.empty_elem, self.join_func)
        queue = [(self.data, new_trie.data)]
        while len(queue) > 0:
            cur, new_cur = queue.pop(0)
            if self.empty_elem in cur:
                new_cur[self.empty_elem] = cur[self.empty_elem]

            for c in elems:
                if c in cur:
                    new_cur[c] = {}
                    queue.append((cur[c], new_cur[c]))
        new_trie.prune()
        return new_trie

    def subtries(self) -> Iterable[Tuple[TElem, "Trie[TElem, TValue]"]]:
        """
        Iterates over all level-1 subtries of this trie.
        The returned subtrie shares storage with the original trie (use `__copy__` or `__deepcopy__` to get a copy).
        """
        for k, v in self.data.items():
            if k != self.empty_elem:
                subtrie = Trie(self.empty_elem, self.join_func)
                subtrie.data = v
                yield k, subtrie

    def items(self) -> Iterable[Tuple[Iterable[TElem], TValue]]:
        queue = [([], self.data)]
        while len(queue) > 0:
            prefix, cur = queue.pop()
            for k, v in cur.items():
                if k == self.empty_elem:
                    yield (self.join_func(prefix), v)
                else:
                    queue.append((prefix + [k], v))

    def keys(self) -> Iterable[Iterable[TElem]]:
        queue = [([], self.data)]
        while len(queue) > 0:
            prefix, cur = queue.pop()
            for k, v in cur.items():
                if k == self.empty_elem:
                    yield self.join_func(prefix)
                else:
                    queue.append((prefix + [k], v))

    def __iter__(self):
        return self.keys()

    def values(self) -> Iterable[TValue]:
        queue = [([], self.data)]
        while len(queue) > 0:
            prefix, cur = queue.pop()
            for k, v in cur.items():
                if k == self.empty_elem:
                    yield v
                else:
                    queue.append((prefix + [k], v))

    def __len__(self) -> int:
        return sum(1 for _ in self.values())

    def __str__(self):
        return f"Trie with {len(self)} elements"

    def __repr__(self) -> str:
        return f"Trie(empty_value={self.empty_elem}, data={self.data})"

    def overlaps_with(
        self, other: "Trie", self_has_value: bool = False, other_has_value: bool = False
    ) -> Iterable[Tuple[Iterable[TElem], "Trie", "Trie"]]:
        """
        Finds all subtries that overlap with the other trie (including the root subtries).
        :param other: the other trie to compare with.
        :param self_has_value: whether to only output overlaps where the self subtrie has a value.
        :param other_has_value: whether to only output overlaps where the other subtrie has a value.
        """
        queue = [(self.data, other.data, [])]
        while len(queue) > 0:
            self_node, other_node, prefix = queue.pop(0)

            # check if we should output this overlap
            if ((not self_has_value) or (self.empty_elem in self_node)) and (
                (not other_has_value) or (other.empty_elem in other_node)
            ):
                self_subtrie = Trie(self.empty_elem, self.join_func)
                self_subtrie.data = self_node
                other_subtrie = Trie(other.empty_elem, other.join_func)
                other_subtrie.data = other_node
                yield self.join_func(prefix), self_subtrie, other_subtrie

            # find all overlapping children
            for k, v in self_node.items():
                if k == self.empty_elem:
                    continue
                if k in other_node:
                    queue.append((v, other_node[k], prefix + [k]))
