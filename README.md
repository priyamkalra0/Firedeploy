# Flint is a simple python client around Google's [Firebase](https://web.app) Hosting API: Deploy to the web with almost zero setup.
Made using Google's Firebase hosting [API documentation](https://firebase.google.com/docs/hosting/api-deploy).


## Usage
You will need to generate a new private keyfile for the Firebase Admin SDK service account in your firebase project by clicking [here](https://console.firebase.google.com/u/0/project/_/settings/serviceaccounts).  See [this](https://firebase.google.com/docs/hosting/api-deploy#access-token) for more information.

```py
from flint import Flint, Credentials, DEFAULT_IGNORE_PATTERNS

credentials = Credentials.from_service_account_info({
  "type": "service_account",
  "project_id": "example-site",
  "private_key_id": "EXAMPLE",
  "private_key": "-----BEGIN PRIVATE KEY-----[EXAMPLE]-----END PRIVATE KEY-----\n",
  "client_email": "example-site@example-site.iam.gserviceaccount.com",
  "client_id": "EXAMPLE",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40example-site.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
})

flint = Flint(credentials)
flint.deploy("./public", ignore_regex=[*DEFAULT_IGNORE_PATTERNS, "data-archive"])
```

The above snippet will create a new app version, add all files in the `./public` directory (recursively, filtering by `ignore_regex`) to that version, and deploy it. Logs are printed to the console like so:
```
[flint/deploy: version_created] sites/example-site/versions/5fe0860ba8caa67e
[flint/file_specifier] ignoring .DS_Store (matches ignore patterns)
[flint/file_specifier] ignoring .gitignore (matches ignore patterns)
[flint/file_specifier] ignoring .git (matches ignore patterns)
[flint/deploy: file_specifier_created] <FileSpecifier count=26, paths=('/index.html', '/index.min.html', '/static/style.min.css', '/scripts/main.js', ...)>
[flint/deploy: version_files_populated] <FileUploadSpecifier upload_url=https://upload-firebasehosting.googleapis.com/upload/sites/example-site/versions/5fe0860ba8caa67e/files, count=3, paths=('index.min.html', 'index.html', 'static/style.css')>
[flint/upload_files: uploaded_file] [1 / 3] index.min.html
[flint/upload_files: uploaded_file] [2 / 3] index.html
[flint/upload_files: uploaded_file] [3 / 3] static/style.css
[flint/deploy: version_finalized] sites/example-site/versions/5fe0860ba8caa67e
[flint/deploy: version_released] {'name': 'sites/example-site/releases/1779769450887000', 'version': ...}
```
In the above example; Flint found 26 files in the `./public` directory, but only 3 of them were modified and were required by firebase.

NOTE: Flint is not yet available as a package, so you need to manually download and include it in your project, and you must install the `google-api-python-client`, `google-auth` python packages.
