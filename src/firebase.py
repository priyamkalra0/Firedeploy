import gzip
import hashlib
import requests
from firebase_admin.credentials \
    import Certificate as BaseCertificate
from dataclasses import dataclass, fields
from datetime import datetime
from pathlib import Path
import json

class Certificate(BaseCertificate):
    def __init__(self, cert: dict):
        super().__init__(cert)
        self.token_info = self.get_access_token()
    
    @property
    def token(self):
        if self.token_info.expiry < datetime.now():
            self.token_info = self.get_access_token()

        return self.token_info.access_token

# https://firebase.google.com/docs/hosting/api-deploy#specify-files
@dataclass
class Files():
    # (key: path [str], value: hash [str])
    path_to_hash: dict[str, str]

    # (key: hash [str], value: file [bytes])
    hash_to_bytes: dict[str, bytes]

    def populate_recv(self, path: Path):
        for f in path.iterdir():
            if f.is_dir():
                self.populate_recv(f)
                continue

            relpath = f.relative_to(path).as_posix()

            bytes_ = f.read_bytes()
            compressed_bytes = gzip.compress(bytes_)

            hash_ = hashlib.sha256(compressed_bytes)
            hex_ = hash_.hexdigest()

            self.path_to_hash[f"/{relpath}"] = hex_
            self.hash_to_bytes[hex_] = compressed_bytes

@dataclass
class FirebaseError():
    code: int
    message: str
    status: str

    def __str__(self) -> str:
        return f"[{self.code} {self.status}] {self.message}"

@dataclass
class Firebase():
    # This can be taken from a firebase URL:
    # site.web.app
    site: str

    # https://firebase.google.com/docs/hosting/api-deploy#access-token
    certificate: Certificate | None

    @property
    def headers(self):
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}",
        }

    @property
    def token(self) -> str:
        if isinstance(self.certificate, Certificate):
            return self.certificate.token
        
        return ""

    def is_valid(self) -> bool:
        return all(
            fields(self)
        )
    
    # https://firebase.google.com/docs/hosting/api-deploy
    def deploy(self, path: Path | str) -> None:
        if isinstance(path, str):
            path = Path(path)

        ## Step 1: Obtain access token from certificate
        # We already have the token set as a property
        # so we'll just log the first 4 chars to show that
        print(f"Access token: {self.token[:4]}XXXXXXX")

        ## Step 2: Prepare a new version for deployment
        resp = requests.post(
            f"https://firebasehosting.googleapis.com/v1beta1/sites/{self.site}/versions",
            headers=self.headers
        )
        content = json.loads(resp.content)

        if resp.status_code != 200:
            return print(f"[failed_to_create_version] {FirebaseError(**content['error'])}")

        version_id = content["name"].split("/")[-1] # type: str
        print(f"Version: {version_id}\n")

        ## Step 3: Populate files
        files = Files({}, {})
        files.populate_recv(path)

        resp = requests.post(
            f"https://firebasehosting.googleapis.com/v1beta1/sites/{self.site}/versions/{version_id}:populateFiles",
            headers=self.headers,
            json={"files": files.path_to_hash}
        )
        content = json.loads(resp.content)

        if resp.status_code != 200:
            return print(f"[failed_to_populate_files] {FirebaseError(**content['error'])}")

        ## Step 4: Upload files
        file_count = len(files.path_to_hash)
        current_file_idx = 0
        metadata = json.loads(resp.content)
        for hash in content["uploadRequiredHashes"]:
            resp = requests.post(
                metadata["uploadUrl"] + f"/{hash}",
                headers=self.headers,
                data=files.hash_to_bytes[hash]
            )

            # `or {}` because there is a possibily that
            # `resp.content` is an empty string which
            # will make `json.loads()` error out.
            content = json.loads(resp.content or "{}")

            if resp.status_code != 200:
                return print(f"[failed_to_upload_files] {FirebaseError(**content['error'])}")
            
            current_file_idx += 1
            print(f"[{current_file_idx}/{file_count} file_uploaded] {hash}")

        ## Step 5: Mark version as FINAL
        resp = requests.patch(
            f"https://firebasehosting.googleapis.com/v1beta1/sites/{self.site}/versions/{version_id}",
            headers=self.headers,
            params={"update_mask": "status"},
            json={"status": "FINALIZED"}
        )
        content = json.loads(resp.content)

        if resp.status_code != 200:
            return print(f"[failed_to_finalize_version] {FirebaseError(**content['error'])}")

        ## Step 6: Release the version for deployment
        resp = requests.post(
            f"https://firebasehosting.googleapis.com/v1beta1/sites/{self.site}/releases",
            headers=self.headers, 
            params={"versionName": f"sites/{self.site}/versions/{version_id}"}
        )
        content = json.loads(resp.content)

        if resp.status_code != 200:
            return print(f"[failed_to_deploy_version] {FirebaseError(**content['error'])}")
        
        domain = self.site + ".web.app"
        print(f"[success] Deployed to {domain}")
