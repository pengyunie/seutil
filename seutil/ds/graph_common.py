import abc
from typing import Iterable, List, Optional

import igraph

"""
Base classes for graph-like data types (including trees and constrained graphs).

Currently we use igraph as the underlying graph library, but we add a level of abstraction to make it better fits our needs, and also make it possible to switch to other libraries in the future.
"""


class EdgeExistedError(ValueError):
    """Used to indicate that adding an edge failed because the edge already existed."""

    pass


class NodeIndexError(IndexError):
    """Used to indicate that a node index is out of range."""

    pass


class InvariantError(ValueError):
    """Used to indicate that a data structure invariant is violated."""

    pass


class Node:
    """
    Wraps an igraph.Vertex, but routes back all modification operations to the container class for checking the invariants.
    """

    def __init__(self, vertex: igraph.Vertex, container: "GraphLikeADT"):
        self.vertex = vertex
        self.container = container

    def __getitem__(self, key):
        if key == "name":
            raise IndexError("'name' attribute is reserved for internal use.")
        return self.vertex[key]

    def __setitem__(self, key, value):
        if key == "name":
            raise IndexError("'name' attribute is reserved for internal use.")
        self.vertex[key] = value

    def delete(self):
        self.container.delete_node(self.vertex["name"])

    @property
    def key(self):
        return self.vertex["name"]


class Edge:
    """
    Wraps an igraph.Edge, but routes back all modification operations to the container class for checking the invariants.
    """

    def __init__(self, edge: igraph.Edge, container: "GraphLikeADT"):
        self.edge = edge
        self.container = container


class GraphLikeADT:
    """
    Base class of a graph-like ADT.

    This wraps a igraph.Graph, but with several differences:
    * uses a unique string key to access the nodes that will *NOT* be affected by the removal of other nodes;
    * checks invariants to ensure the validity of the data structure when modifying the nodes and edges;
    * all modification operations called on nodes and edges will also be routed back to the container class for checking the invariants.

    "Modification" means adding or removing nodes and edges. It does not include changing the properties of nodes or edges.
    """

    def __init__(self, directed: bool = True):
        self.g: igraph.Graph = igraph.Graph(directed=directed)
        self.next_id: int = 0

    @abc.abstractmethod
    def check_invariants(self) -> bool:
        """
        Checks if the data structure is in a valid state.
        Default implementation checks nothing, which allows any graph. Subclasses should override this method to implement the specific invariants.
        """
        return True

    @abc.abstractmethod
    def check_invariants_before_adding_node(
        self,
        parents: Optional[List[Node]] = None,
        children: Optional[List[Node]] = None,
    ) -> bool:
        """
        Checks if adding a node with the given parents and children is valid, *before* adding the node.
        Default implementation does nothing here and defers the invariants checking to after adding the node. Subclasses can override this method to perform incremental checks of invariants.
        """
        return True

    @abc.abstractmethod
    def check_invariants_after_adding_node(
        self,
        node: Node,
        parents: Optional[List[Node]] = None,
        children: Optional[List[Node]] = None,
    ) -> bool:
        """
        Checks if adding a node with the given parents and children is valid, *after* adding the node.
        Default implementation calls check_invariants to check the entire data structure. Subclasses can override this method to perform incremental checks of invariants, either here or before adding the node.
        """
        return self.check_invariants()

    def add_node(
        self,
        parents: Optional[List[Node]] = None,
        children: Optional[List[Node]] = None,
    ) -> Node:
        if not self.check_invariants_before_adding_node(parents, children):
            raise InvariantError("Adding a node failed due to invariant violation.")
        node = self._add_node()
        if parents is not None:
            for other in parents:
                self._add_edge(other.key, node.key)
        if children is not None:
            for other in children:
                self._add_edge(node.key, other.key)
        if not self.check_invariants_after_adding_node(node, parents, children):
            raise InvariantError("Adding a node failed due to invariant violation.")
        return node

    # TODO: delete_node, add_edge, and delete_edge

    def _add_node(self) -> Node:
        key = f"n{self.next_id}"
        self.next_id += 1
        return Node(self.g.add_vertex(name=key), self)

    def _delete_node(self, key: str) -> None:
        self.g.delete_vertices(key)

    def _add_edge(self, src: str, tgt: str) -> Edge:
        return Edge(self.g.add_edge(src, tgt), self)

    def _delete_edge(self, src: str, tgt: str):
        self.g.delete_edges([(src, tgt)])

    def get_node(self, key: str) -> Node:
        return Node(self.g.vs.find(name=key), self)

    def get_edge(self, from_key: str, to_key: str) -> Edge:
        return Edge(self.g.es.find(from_key=from_key, to_key=to_key), self)

    def ncount(self) -> int:
        return self.g.vcount()

    def ecount(self) -> int:
        return self.g.ecount()

    def __str__(self):
        return self.g.__str__()

    def __repr__(self):
        return self.g.__repr__()

    def nodes(self) -> Iterable[Node]:
        return [Node(v, self) for v in self.g.vs]

    def edges(self) -> Iterable[Edge]:
        return [Edge(e, self) for e in self.g.es]
