from pathlib import Path

from jsonargparse.typing import register_type

RPath = Path
RPath.__doc__ = """
Type hint for jsonargparse to obtain a path that is `resolve`d during parsing (relative to cwd if not absolute).
This type does NOT tell jsonargparse to check the existence of the specified path, 
nor does it tell jsonargparse to create the path if it does not exist.
"""


register_type(
    RPath,
    deserializer=lambda v: Path(v).resolve(),
    serializer=lambda v: str(v),
    uniqueness_key=(Path, "ResolvedPath"),
)
