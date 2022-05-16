from .graph_common import GraphLikeADT, Node
from typing import List, Optional, Set


class Lattice(GraphLikeADT):
    """
    Lattice: directed, acyclic, potentially connected graph.
    """

    def __init__(self, connected: bool = False):
        super().__init__(directed=True)
        self.connected = connected
        self.entry_nodes: Set[Node] = set()
        self.exit_nodes: Set[Node] = set()

    def check_invariants(self) -> bool:
        if self.g.vcount() == 0:
            return True
        return self.g.is_dag() and ((not self.connected) or self.g.is_connected("weak"))

    def add_node(
        self,
        parents: Optional[List[Node]] = None,
        children: Optional[List[Node]] = None,
    ) -> Node:
        node = super().add_node(parents, children)
        if parents is None:
            self.entry_nodes.add(node)
        else:
            for n in parents:
                if n in self.exit_nodes:
                    self.exit_nodes.remove(n)
        if children is None:
            self.exit_nodes.add(node)
        else:
            for n in children:
                if n in self.entry_nodes:
                    self.entry_nodes.remove(n)
        return node
