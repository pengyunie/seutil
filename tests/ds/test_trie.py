import pytest
import seutil as su


def test_trie_set():
    trie = su.ds.trie.Trie()
    trie.set("key1")
    assert "key1" in trie
    assert trie["key1"] is True

    trie["another"] = 123
    assert trie["another"] == 123

    trie.set("efg", 456)
    assert trie["efg"] == 456


def test_trie_set_exist_ok():
    trie = su.ds.trie.Trie()
    trie.set("key1")
    trie.set("key1", exist_ok=True)
    assert "key1" in trie

    with pytest.raises(KeyError):
        trie.set("key1", exist_ok=False)


def test_trie_get():
    trie = su.ds.trie.Trie()
    trie.set("key1", 123)
    assert trie.get("key1") == 123
    assert trie["key1"] == 123


def test_trie_get_missing():
    trie = su.ds.trie.Trie()
    assert trie.get("key1") is None

    with pytest.raises(KeyError):
        trie["key1"]


def test_trie_get_default():
    trie = su.ds.trie.Trie()
    trie.set("key1", 123)
    assert trie.get("key1", default=456) == 123
    assert trie.get("key2", default=456) == 456
