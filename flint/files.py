# stdlib
from typing import Iterable
from pathlib import Path
import json, re, gzip, hashlib

from .log import log # local

DEFAULT_IGNORE_PATTERNS = (r"(^|/)\.",) # ignore hidden files and directories by default

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

    def __init__(self, ignore_regex: Iterable[str] = DEFAULT_IGNORE_PATTERNS) -> None:
        self.m_path_to_hash: dict[str, str] = {} # (k: file path, v: file hash)
        self.m_hash_to_data: dict[str, bytes] = {} # (k: file hash, v: file data)
        self.m_ignore_patterns = ignore_regex
    
    @classmethod
    def from_directory(cls, path: Path, ignore_regex: Iterable[str] = DEFAULT_IGNORE_PATTERNS) -> "FileSpecifier":
        specifier = cls(ignore_regex)
        specifier.add_directory(path)
        return specifier
    
    def add_directory(self, path: Path, force: bool = False, root: Path | None = None) -> None:
        if root is None: root = path

        for f in path.iterdir():
            relpath = f.relative_to(root).as_posix()
            if not force and self.is_node_ignored(relpath):
                log("[flint/file_specifier]", f"ignoring {relpath} (matches ignore patterns)")
                continue

            if f.is_dir(): self.add_directory(f, force, root)
            elif f.is_file(): self.add_file(relpath, f.read_bytes(), True) # we already did the check for this file
            else: log("[flint/file_specifier]", f"skipping {relpath} (not a file or directory)")

    def add_file(self, relpath: str, data: bytes, force: bool = False) -> None:
        if not force and self.is_node_ignored(relpath): 
            return log("[flint/file_specifier]", f"ignoring {relpath} (matches ignore patterns)")
        
        compressed_bytes = gzip.compress(data, mtime=0)
        file_hash = hashlib.sha256(compressed_bytes).hexdigest()

        self.m_path_to_hash[f"/{relpath}"] = file_hash # leading slash required by firebase
        self.m_hash_to_data[file_hash] = compressed_bytes

    def is_node_ignored(self, relpath: str) -> bool:
        return any(
            re.search(pattern, relpath) 
            for pattern in self.m_ignore_patterns
        )

    def emplace_spec(self, other: "FileSpecifier") -> None:
        self.m_path_to_hash = other.m_path_to_hash.copy()
        self.m_hash_to_data = other.m_hash_to_data.copy() 
        self.m_ignore_patterns = (*other.m_ignore_patterns,) # copy

    def filter_by_hash(self, keep_hashes: Iterable[str]) -> None:
        keep_hashes = set(keep_hashes) # for constant lookup

        self.m_path_to_hash = {
            p: h for p, h 
            in self.m_path_to_hash.items()
            if h in keep_hashes
        }

        self.m_hash_to_data = {
            h: self.m_hash_to_data[h]
            for h in keep_hashes
        }

    def __str__(self) -> str:
        return f"<{self.__class__.__name__} count={self.count}, paths={_get_mapping_as_string(self.path_to_hash)}>"
    
class FileUploadSpecifier(FileSpecifier):
    @property
    def upload_url(self) -> str:
        return self.m_upload_url
    
    def __init__(self, file_specifier: FileSpecifier, api_response: dict[str, str]):
        self.m_upload_url = api_response["uploadUrl"]
        required_files = api_response.get("uploadRequiredHashes", [])
        self.emplace_spec(file_specifier)
        self.filter_by_hash(required_files)
        
    def __str__(self) -> str:
        return super().__str__().replace(">", f" upload_url={self.upload_url}>")

def _get_mapping_as_string(mapping: dict) -> str:
    # removes quotes around keys and values for readability
    return \
        json.dumps(
            obj=mapping, 
            indent=1
        ).replace('"', '')