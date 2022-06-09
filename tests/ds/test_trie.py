import copy

import pytest
import seutil as su


def test_set():
    trie = su.ds.trie.Trie()
    trie.set("key1")
    assert "key1" in trie
    assert trie["key1"] is True

    trie["another"] = 123
    assert trie["another"] == 123

    trie.set("efg", 456)
    assert trie["efg"] == 456


def test_set_exist_ok():
    trie = su.ds.trie.Trie()
    trie.set("key1")
    trie.set("key1", exist_ok=True)
    assert "key1" in trie

    with pytest.raises(KeyError):
        trie.set("key1", exist_ok=False)


def test_get():
    trie = su.ds.trie.Trie()
    trie["key1"] = 123
    assert trie.get("key1") == 123
    assert trie["key1"] == 123


def test_get_missing():
    trie = su.ds.trie.Trie()
    assert trie.get("key1") is None

    with pytest.raises(KeyError):
        trie["key1"]

    with pytest.raises(KeyError):
        trie[""]


def test_get_default():
    trie = su.ds.trie.Trie()
    trie["key1"] = 123
    assert trie.get("key1", default=456) == 123
    assert trie.get("key2", default=456) == 456


def test_compute_add():
    trie = su.ds.trie.Trie()
    trie.compute("key1", lambda v: 123)
    assert trie["key1"] == 123


def test_compute_remove():
    trie = su.ds.trie.Trie()
    trie["key1"] = 123
    trie.compute("key1", lambda v: su.ds.trie.Trie.MISSING)
    assert "key1" not in trie


def test_compute_update():
    trie = su.ds.trie.Trie()
    trie["key1"] = 123
    trie.compute("key1", lambda v: 456)
    assert trie["key1"] == 456


def test_remove():
    trie = su.ds.trie.Trie()
    trie["key1"] = 123
    del trie["key1"]
    assert "key1" not in trie


def test_remove_missing():
    trie = su.ds.trie.Trie()
    with pytest.raises(KeyError):
        del trie["key1"]

    with pytest.raises(KeyError):
        del trie[""]


def test_has_key():
    trie = su.ds.trie.Trie()
    trie["key1"] = 123
    assert "key1" in trie
    assert "key2" not in trie


def test_has_prefix():
    trie = su.ds.trie.Trie()
    trie["key1"] = 123
    assert trie.has_prefix("ke")
    assert not trie.has_prefix("what")


def test_copy():
    trie = su.ds.trie.Trie()
    trie["key1"] = 123
    trie["mutable1"] = [4, 5, 6]
    trie_copy = copy.copy(trie)
    assert trie_copy["key1"] == 123
    assert trie_copy["mutable1"] == [4, 5, 6]

    trie["key2"] = 456
    assert "key2" not in trie_copy

    trie["mutable1"].append(7)
    assert trie_copy["mutable1"] == [4, 5, 6, 7]


def test_deepcopy():
    trie = su.ds.trie.Trie()
    trie["key1"] = 123
    trie["mutable1"] = [4, 5, 6]
    trie_copy = copy.deepcopy(trie)
    assert trie_copy["key1"] == 123
    assert trie_copy["mutable1"] == [4, 5, 6]

    trie["key2"] = 456
    assert "key2" not in trie_copy

    trie["mutable1"].append(7)
    assert trie_copy["mutable1"] == [4, 5, 6]


def test_get_subtrie():
    trie = su.ds.trie.Trie()
    trie["key1"] = 123
    trie["key2"] = 456

    subtrie = trie.get_subtrie("key")
    assert subtrie["1"] == 123
    assert subtrie["2"] == 456


def test_get_subtrie_mismatch():
    trie = su.ds.trie.Trie()
    trie["key1"] = 123
    trie["key2"] = 456

    subtrie = trie.get_subtrie("whatever")
    assert len(subtrie) == 0


def test_get_subtrie_prefix_of():
    trie = su.ds.trie.Trie()
    trie["abc"] = 123
    trie["abcd"] = 456
    trie["abcdef"] = 789
    trie["def"] = 999

    subtrie = trie.get_subtrie_prefix_of("abcdef")
    assert subtrie["abc"] == 123
    assert subtrie["abcd"] == 456
    assert subtrie["abcdef"] == 789
    assert "def" not in subtrie


def test_get_subtrie_using_elems():
    trie = su.ds.trie.Trie()
    trie["abc"] = 1
    trie["abcd"] = 2
    trie["abcabc"] = 3
    trie["def"] = 4

    subtrie = trie.get_subtrie_using_elems("abc")
    assert subtrie["abc"] == 1
    assert subtrie["abcabc"] == 3
    assert "abcd" not in subtrie
    assert "def" not in subtrie


def test_subtries():
    trie = su.ds.trie.Trie()
    trie["a1"] = 1
    trie["a2"] = 2
    trie["b3"] = 3
    trie["c4"] = 4

    e2subtrie = {k: v for k, v in trie.subtries()}
    assert len(e2subtrie) == 3
    assert len(e2subtrie["a"]) == 2
    assert len(e2subtrie["b"]) == 1
    assert len(e2subtrie["c"]) == 1


def test_items():
    trie = su.ds.trie.Trie()
    trie["a1"] = 1
    trie["a2"] = 2
    trie["b3"] = 3
    trie["c4"] = 4

    e2v = {k: v for k, v in trie.items()}
    assert len(e2v) == 4
    assert e2v["a1"] == 1
    assert e2v["a2"] == 2
    assert e2v["b3"] == 3
    assert e2v["c4"] == 4


def test_keys():
    trie = su.ds.trie.Trie()
    trie["a1"] = 1
    trie["a2"] = 2
    trie["b3"] = 3
    trie["c4"] = 4

    keys = list(trie.keys())
    assert len(keys) == 4
    assert "a1" in keys
    assert "a2" in keys
    assert "b3" in keys
    assert "c4" in keys


def test_values():
    trie = su.ds.trie.Trie()
    trie["a1"] = 1
    trie["a2"] = 2
    trie["b3"] = 3
    trie["c4"] = 4

    values = list(trie.values())
    assert len(values) == 4
    assert 1 in values
    assert 2 in values
    assert 3 in values
    assert 4 in values


def test_overlaps_with():
    trie1 = su.ds.trie.Trie()
    trie1["abc"] = 1
    trie1["def"] = 2

    trie2 = su.ds.trie.Trie()
    trie2["ab"] = 3
    trie2["defg"] = 4

    e2overlaps = {k: (t1, t2) for k, t1, t2 in trie1.overlaps_with(trie2)}
    assert set(e2overlaps.keys()) == {"", "a", "ab", "d", "de", "def"}


def test_overlaps_with_self_has_value():
    trie1 = su.ds.trie.Trie()
    trie1["alpha"] = 1
    trie1["beta"] = 2
    trie1["gamma"] = 3

    trie2 = su.ds.trie.Trie()
    trie2["alphaXXX"] = 1
    trie2["betaXXX"] = 1

    e2overlaps = {
        k: (t1, t2) for k, t1, t2 in trie1.overlaps_with(trie2, self_has_value=True)
    }
    assert len(e2overlaps) == 2
    assert e2overlaps["alpha"][0][""] == 1
    assert "" not in e2overlaps["alpha"][1]
    assert e2overlaps["beta"][0][""] == 2
    assert "" not in e2overlaps["beta"][1]


def test_overlaps_with_other_has_value():
    trie1 = su.ds.trie.Trie()
    trie1["alpha"] = 1
    trie1["beta"] = 2
    trie1["gamma"] = 3

    trie2 = su.ds.trie.Trie()
    trie2["aaa"] = 4
    trie2["b"] = 5

    e2overlaps = {
        k: (t1, t2) for k, t1, t2 in trie1.overlaps_with(trie2, other_has_value=True)
    }
    assert len(e2overlaps) == 1
    assert e2overlaps["b"][1][""] == 5
    assert "" not in e2overlaps["b"][0]
