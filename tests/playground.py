"""
Testing random stuff, before they're added into the library.
"""

import dataclasses
from jsonargparse import CLI


@dataclasses.dataclass
class Entry:
    key: str
    value: str


def test_dataclass():
    entry = Entry("aaa", "bbb")
    print(f"{entry=}")
    print(f"{[(f.name, f.type) for f in dataclasses.fields(Entry)]=}")
    print(f"{dataclasses.asdict(entry)=}")

    print(f"{Entry(**dataclasses.asdict(entry))=}")


class RandomClass():

    @classmethod
    def deserialize(cls, data):
        return cls()


def test_io():
    clz = RandomClass
    print(f"{hasattr(clz, 'deserialize')=}")
    print(f"{getattr(clz, 'deserialize')(123)=}")


def test_pbar():
    import time
    # from tqdm import tqdm
    from seutil.pbar import tqdm

    for i in tqdm(range(10)):
        for j in tqdm(range(10)):
            # print(f"{(i, j)=}")
            time.sleep(0.4)

        for j in tqdm(enumerate(range(10))):
            # print(f"{(i, j)=}")
            time.sleep(0.4)


if __name__ == "__main__":
    CLI(as_positional=False)
