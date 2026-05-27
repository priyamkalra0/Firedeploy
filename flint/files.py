# stdlib
from typing import Callable, Iterable
from pathlib import Path
import json, gzip, hashlib

from .log import log # local

type StringFilterType = Callable[[str], bool]
type PathFilterType = Callable[[Path], bool]
DEFAULT_FILTERS = (lambda p: p.stem.startswith('.'),) # ignore hidden files and directories by default

# https://firebase.google.com/docs/hosting/api-deploy#specify-files
class FileSpecifier():
    @property
    def path_to_hash(self) -> dict[str, str]:
        return self.m_path_to_hash

    @property
    def hash_to_data(self) -> dict[str, bytes]:
        return self.m_hash_to_data
    
    @property
    def count(self) -> int:
        return len(self.m_path_to_hash)

    def __init__(self, filters: Iterable[PathFilterType] = DEFAULT_FILTERS) -> None:
        self.m_path_to_hash: dict[str, str] = {} # (k: file path, v: file hash)
        self.m_hash_to_data: dict[str, bytes] = {} # (k: file hash, v: file data)
        self.m_filters = filters
    
    @classmethod
    def from_directory(cls, path: Path, filters: Iterable[PathFilterType] = DEFAULT_FILTERS) -> "FileSpecifier":
        specifier = cls(filters)
        specifier.add_directory(path)
        return specifier
    
    def add_directory(self, path: Path, root: Path | None = None) -> None:
        if root is None: root = path

        for node_path in path.iterdir():
            relpath = node_path.relative_to(root).as_posix()
            if self.is_node_ignored(node_path): 
                log("[flint/file_specifier]", f"ignoring {relpath} (matches ignore patterns)")
            elif node_path.is_dir(): self.add_directory(node_path, root)
            elif node_path.is_file(): self._add_file(relpath, node_path.read_bytes()) # skip check
            else: log("[flint/file_specifier]", f"skipping {relpath} (not a file or directory)")

    def add_file(self, path: Path, to_path: str | None = None) -> None:
        if self.is_node_ignored(path): 
            return log("[flint/file_specifier]", f"ignoring {path} (matches ignore patterns)")
        
        self._add_file(
            to_path or path.name,
            path.read_bytes() # add file to root if to_path not specified
        ) 
        
    def _add_file(self, relpath: str, data: bytes) -> None:
        compressed_bytes = gzip.compress(data, mtime=0)
        file_hash = hashlib.sha256(compressed_bytes).hexdigest()

        self.m_path_to_hash[f"/{relpath}"] = file_hash # leading slash required by firebase
        self.m_hash_to_data[file_hash] = compressed_bytes

    def is_node_ignored(self, path: Path) -> bool:
        return any(
            filter_func(path) for 
            filter_func in self.m_filters
        )
    
    """ Helper methods for copying/filtering the specifier. """

    def emplace_spec(self, other: "FileSpecifier") -> None:
        self.m_path_to_hash = other.m_path_to_hash.copy()
        self.m_hash_to_data = other.m_hash_to_data.copy() 
        self.m_filters = (*other.m_filters,) # copy

    def filter_by_hash(self, filter: StringFilterType) -> None:
        for file_path, file_hash in tuple(self.m_path_to_hash.items()):
            if not filter(file_hash): continue
            del self.m_path_to_hash[file_path]
            self.m_hash_to_data.pop(file_hash, None) # may already be deleted

    def __str__(self) -> str:
        return f"<{self.__class__.__name__} count={self.count}, paths={_get_mapping_as_string(self.path_to_hash)}>"
    
class FileUploadSpecifier(FileSpecifier):
    @property
    def upload_url(self) -> str:
        return self.m_upload_url
    
    def __init__(self, file_specifier: FileSpecifier, api_response: dict[str, str]):
        self.m_upload_url = api_response["uploadUrl"]
        required_files = {*api_response.get("uploadRequiredHashes", [])}

        self.emplace_spec(file_specifier)
        self.filter_by_hash(lambda h: h not in required_files)
        
    def __str__(self) -> str:
        return super().__str__().replace(">", f" upload_url={self.upload_url}>")

def _get_mapping_as_string(mapping: dict) -> str:
    # removes quotes around keys and values for readability
    return \
        json.dumps(
            obj=mapping, 
            indent=1
        ).replace('"', '')