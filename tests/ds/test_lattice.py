import pytest
import seutil as su


def test_lattice_add():
    lattice = su.ds.lattice.Lattice()
    n0 = lattice.add_node()
    n1 = lattice.add_node(parents=[n0])
    n2 = lattice.add_node(parents=[n0])
    n3 = lattice.add_node(parents=[n1, n2])
    assert lattice.ncount() == 4
    assert lattice.ecount() == 4


def test_lattice_acyclic():
    lattice = su.ds.lattice.Lattice()
    n0 = lattice.add_node()
    n1 = lattice.add_node(parents=[n0])
    n2 = lattice.add_node(parents=[n0])
    with pytest.raises(su.ds.InvariantError):
        n3 = lattice.add_node(parents=[n1, n2], children=[n0])


def test_lattice_connected():
    lattice = su.ds.lattice.Lattice(connected=True)
    n0 = lattice.add_node()
    with pytest.raises(su.ds.InvariantError):
        n1 = lattice.add_node()


def test_lattice_connected_is_by_default_off():
    lattice = su.ds.lattice.Lattice()
    n0 = lattice.add_node()
    n1 = lattice.add_node()
    assert lattice.ncount() == 2
    assert lattice.ecount() == 0


def test_lattice_entry_exit_nodes():
    lattice = su.ds.lattice.Lattice()
    n0 = lattice.add_node()
    n1 = lattice.add_node(parents=[n0])
    n2 = lattice.add_node(parents=[n0])
    n3 = lattice.add_node(parents=[n1, n2])
    assert lattice.entry_nodes == {n0}
    assert lattice.exit_nodes == {n3}
