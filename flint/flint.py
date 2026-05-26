# google
from google.oauth2.service_account import Credentials
from google_auth_httplib2 import AuthorizedHttp
from googleapiclient.discovery import build

# stdlib
from pathlib import Path
from typing import Iterable

# local
from .error import wrap_exceptions
from .files import FileSpecifier, FileUploadSpecifier, DEFAULT_IGNORE_PATTERNS

SCOPES = ["https://www.googleapis.com/auth/firebase"]

class Flint():
    # Wraps around the Firebase Hosting REST API to provide a
    # simple interface for deploying static sites to Firebase Hosting.
    # https://firebase.google.com/docs/hosting/api-deploy

    # The credentials to use for authentication, e.g. from a service account JSON file
    @property
    def credentials(self) -> Credentials:
        return self.m_credentials
    
    # The firebase web-hosting site id to deploy to, e.g. "my-site-id" for "my-site-id.web.app"
    # Optional; if not provided, Flint will attempt to use the project_id from the credentials as the default site_id
    @property
    def site_id(self) -> str | None:
        return self.m_site_id 

    def __init__(self, credentials: Credentials, site_id: str | None = None):
        self.m_site_id = site_id or credentials.project_id
        assert self.site_id, \
            "One of `Flint.site_id` or `Flint.Credentials.project_id` must be provided!"
        
        credentials = credentials.with_scopes(SCOPES)
        
        self.m_credentials = credentials
        self.m_http = AuthorizedHttp(credentials)
        self.m_service = build(
            "firebasehosting", "v1beta1",
            http=self.m_http
        )

    def deploy(self, path: Path | str, ignore_regex: Iterable[str] = DEFAULT_IGNORE_PATTERNS) -> None:
        if isinstance(path, str): path = Path(path)
        
        err, version_name = self.create_new_version()
        if version_name is None: return print("[flint/deploy: failed_to_create_version]", err)

        print("[flint/deploy: version_created]", version_name)
        
        err, f_spec = self.get_file_specifier(path, ignore_regex)
        if f_spec is None: return print("[flint/deploy: failed_to_get_file_specifier]", err)

        print("[flint/deploy: file_specifier_created]", f_spec)

        err, f_up_spec = self.populate_version_files(version_name, f_spec)
        if f_up_spec is None: return print("[flint/deploy: failed_to_populate_version_files]", err)

        print("[flint/deploy: version_files_populated]", f_up_spec)

        err, _ = self.upload_files(f_up_spec)
        if err: return print("[flint/deploy: failed_to_upload_files]", err)

        err, _ = self.finalize_version(version_name)
        if err: return print("[flint/deploy: failed_to_finalize_version]", err)

        print("[flint/deploy: version_finalized]", version_name)

        err, response = self.release_version(version_name)
        if response is None: return print("[flint/deploy: failed_to_release_version]", err)

        print("[flint/deploy: version_released]", response)

    """
    Below are methods corresponding to each step of the deployment process, as outlined in the Firebase Hosting REST API documentation. 
    Each method is wrapped with `wrap_exceptions` to convert any exceptions into `FlintError` objects for easier error handling.
    Signatures changes from `(...) -> T` to go-style `(...) -> tuple[FlintError | None, T | None]`, 
    where the first element of the returned tuple is a `FlintError` if an error occurred (or `None` if no error), 
    and the second element is the actual return value of the method if it succeeded (or `None` if an error occurred).

    use as such: ```python
    err, res = flint.some_method(...)
    if res is None: print("An error occurred:", err)
    ```
    """

    @wrap_exceptions
    def create_new_version(self) -> str:
        version =               \
            self.m_service      \
                .sites()        \
                .versions()     \
                .create(
                    parent=f"sites/{self.site_id}"
                ).execute()
        
        assert version["status"] == "CREATED", str(version)

        return version["name"]
    
    @wrap_exceptions
    def get_file_specifier(self, path: Path, ignore_regex: Iterable[str] = DEFAULT_IGNORE_PATTERNS) -> FileSpecifier:
        return FileSpecifier.from_directory(path, ignore_regex)
    
    @wrap_exceptions
    def populate_version_files(self, version_name: str, file_spec: FileSpecifier) -> FileUploadSpecifier:
        response =              \
            self.m_service      \
                .sites()        \
                .versions()     \
                .populateFiles(
                    parent=version_name,
                    body={"files": file_spec.path_to_hash}
                ).execute()
        
        return FileUploadSpecifier(file_spec, response)
    
    @wrap_exceptions
    def upload_file(self, upload_url: str, data: bytes) -> None:
        response, content = self.m_http.request( # no discovery doc for this, so we use the underlying http client
            uri=upload_url,
            method="POST",
            body=data,
            headers={"Content-Type": "application/octet-stream"}
        )

        assert response.status == 200, content.decode()

    @wrap_exceptions
    def upload_files(self, upload_spec: FileUploadSpecifier) -> None:
        for idx, file_hash in enumerate(upload_spec.hash_to_path):
            ctr = idx + 1
            err, _ = self.upload_file(
                f"{upload_spec.upload_url}/{file_hash}", 
                upload_spec.hash_to_data[file_hash]
            )
            file_path = upload_spec.hash_to_path[file_hash]

            assert err is None, f"[{ctr} / {upload_spec.count}] {file_path}; {err.message}"
            
            print("[flint/upload_files: uploaded_file]", f"[{ctr} / {upload_spec.count}] {file_path}")
    
    @wrap_exceptions
    def finalize_version(self, version_name: str) -> None:
        response =          \
            self.m_service  \
            .sites()        \
            .versions()     \
            .patch(
                name=version_name,
                body={"status": "FINALIZED"},
                updateMask="status"
            ).execute()
        
        assert response["status"] == "FINALIZED", str(response)
    
    @wrap_exceptions
    def release_version(self, version_name: str) -> dict:
        return               \
            self.m_service   \
            .sites()         \
            .releases()      \
            .create(
                parent=f"sites/{self.site_id}",
                versionName=version_name,
            ).execute()