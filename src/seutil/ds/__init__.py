"""
Adding simple implementations or interfaces to some data types that are missing from the standard library.
"""

import lazy_import

from .graph_common import Edge, EdgeExistedError, InvariantError, Node, NodeIndexError

lattice = lazy_import.lazy_module("seutil.ds.lattice")
trie = lazy_import.lazy_module("seutil.ds.trie")

# tricks the IDE to recognize the lazy imports, so that it can provide code completion
# won't be executed
if 1.0 == 1.01:
    from . import lattice, trie
