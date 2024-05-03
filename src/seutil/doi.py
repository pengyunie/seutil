import requests
import bibtexparser

# According to its document, instead of running `pip install bibtexparser`, users are suggested to run `pip install bibtexparser --pre`, which installs the  bibtexparser v2.
from bibtexparser.middlewares import BlockMiddleware
from bibtexparser.middlewares import RemoveEnclosingMiddleware
from typing import Tuple, Union
from bibtexparser.model import Entry, Field
from titlecase import titlecase


class AddDOIMiddleware(BlockMiddleware):
    def transform_entry(self, entry, library):
        """Add DOI to the entry if it is missing."""
        if entry.entry_type == "online":
            return entry
        if "title" in entry.fields_dict and "doi" not in entry.fields_dict:
            title = entry.get("title", None)
            author = entry.get("author", None)
            title_str = title.value
            if title_str.startswith("{") and title_str.endswith("}"):
                title_str = title_str[1:-1]
            # add doi to the entry
            entry.set_field(Field("doi", self.find_doi(title_str, author.value.lower() if author else None)))
        else:
            entry.set_field(Field("doi", "No title found"))
        # Return the transformed entry
        return entry

    def find_doi(self, title_str: str, author_str: str):
        # Replace spaces with + for URL encoding
        query = "+".join(title_str.split())
        url = f"https://api.crossref.org/works?query.title={query}"

        try:
            response = requests.get(url)
            response.raise_for_status()  # Raises an HTTPError for bad responses

            # Parse the JSON response
            data = response.json()
            items = data["message"]["items"]
            if items:
                # Assuming the first result is the most relevant
                doi = items[0]["DOI"]
                # Verify author
                if author_str:
                    same_author = True
                    if "author" in items[0]:
                        authors = items[0]["author"]
                        if authors:
                            for author in authors:
                                # Check family name
                                # Note: do not check given name as it may be abbreviated
                                for key in ["family"]:
                                    if key in author:
                                        if author[key].lower() not in author_str:
                                            same_author = False
                                            break
                    if not same_author:
                        return "No DOI found"
                return f"https://doi.org/{doi}"
            else:
                return "No DOI found"
        except requests.exceptions.RequestException as e:
            return f"An error occurred: {str(e)}"


class TitleCaseMiddleware(BlockMiddleware):
    """Title case the title field."""

    def transform_entry(self, entry, library):
        """Title case the title field."""
        if "title" in entry.fields_dict:
            title_str = entry.fields_dict["title"].value
            entry.fields_dict["title"].value = titlecase(title_str)
        return entry


REMOVED_ENCLOSING_KEY = "removed_enclosing"

class CleanFieldMiddleware(BlockMiddleware):
    """Clean the field
    1. Remove enclosing characters from values such as field.
    2. Remove organization, publisher, and address fields if they exist.

    This middleware removes enclosing characters from a field value.
    It is useful when the field value is enclosed in braces or quotes
    (which is the case for the vast majority of values).

    Note: If you want to interpolate strings, you should do so
    before removing any enclosing.
    """

    def __init__(self, allow_inplace_modification: bool = True):
        super().__init__(
            allow_inplace_modification=allow_inplace_modification,
            allow_parallel_execution=True,
        )

    # docstr-coverage: inherited
    @classmethod
    def metadata_key(cls) -> str:
        return REMOVED_ENCLOSING_KEY

    @staticmethod
    def _strip_enclosing(value: str) -> Tuple[str, Union[str, None]]:
        value = value.strip()
        if value.startswith("{") and value.endswith("}"):
            return value[1:-1], "{"
        return value, "no-enclosing"

    # docstr-coverage: inherited
    def transform_entry(self, entry: Entry, library: "Library") -> Entry:
        field: Field
        metadata = dict()
        for field in entry.fields:
            # Remove enclosing characters from the field value
            # Otherwise, the enclosing characters will be included in the value, like author = {{Erik Lundsten}}
            stripped, enclosing = self._strip_enclosing(field.value)
            field.value = stripped
            metadata[field.key] = enclosing
        entry.parser_metadata[self.metadata_key()] = metadata
        
        # Remove organization, publisher, and address fields if they exist
        fields_to_remove = ["organization", "publisher", "address"]
        for field_key in fields_to_remove:
            if field_key in entry.fields_dict:
                entry.fields.remove(entry.fields_dict[field_key])
        return entry


def load_and_update_bib(input_path, output_path):
    bib_database = bibtexparser.parse_file(
        input_path, parse_stack=[CleanFieldMiddleware(), AddDOIMiddleware(), TitleCaseMiddleware()]
    )
    # dump the updated bibtex string to a file
    bibtexparser.write_file(output_path, bib_database)


def main(bib_path: str):
    load_and_update_bib(bib_path, bib_path.replace(".bib", "_updated.bib"))


if __name__ == "__main__":
    main("bib.bib")
