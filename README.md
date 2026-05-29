# Flint is a simple python client around Google's [Firebase](https://web.app) Hosting API: Deploy to the web with almost zero setup.
Made using Google's Firebase hosting [API documentation](https://firebase.google.com/docs/hosting/api-deploy).


## Usage
You will need to generate a new private keyfile for the Firebase Admin SDK service account in your firebase project by clicking [here](https://console.firebase.google.com/u/0/project/_/settings/serviceaccounts).  See [this](https://firebase.google.com/docs/hosting/api-deploy#access-token) for more information.

```py
from flint import Flint, Credentials

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

example_site = Flint(credentials)
example_site.deploy("./public", filters=[
    *Flint.DEFAULT_FILTERS, 
    # ignore directory `data-archive`
    lambda path: path.is_dir() and path.name == "data-archive",
    # ignore all non-minified files except index.html
    lambda path: path.is_file() \
      and not path.stem.endswith(".min") \
      and path.name != "index.html"
])
```

The above snippet will create a new app version, add all files in the `./public` directory (recursively, filtering by `filters`) to that version, and deploy it. Logs are printed to the console like so:
```
[flint/deploy: version_created] sites/example-site/versions/39a3bf0b3fe052a9
[flint/file_specifier] ignoring .DS_Store (matches ignore patterns)
[flint/file_specifier] ignoring .gitignore (matches ignore patterns)
[flint/file_specifier] ignoring static/data-archive (matches ignore patterns)
[flint/file_specifier] ignoring static/data.json (matches ignore patterns)
[flint/file_specifier] ignoring static/style.css (matches ignore patterns)
[flint/file_specifier] ignoring scripts/.DS_Store (matches ignore patterns)
[flint/file_specifier] ignoring scripts/render.js (matches ignore patterns)
[flint/file_specifier] ignoring scripts/metadata.js (matches ignore patterns)
[flint/file_specifier] ignoring scripts/main.js (matches ignore patterns)
[flint/file_specifier] ignoring .git (matches ignore patterns)
[flint/deploy: file_specifier_created] from path: "public" <FileSpecifier count=7, paths={
 /index.html: e2473562285733bddd6b92f0bc713b6de52d8d1fa680e5862018214f3a486a6e,
 /static/style.min.css: a83d16553b4c700c32e4532f2a0400e1060c29349ff9a1ed81c67998de50be81,
 /static/data.min.json: 1cc48ca7d5662b6f7ea566a37de0301b5265a379aa6559568d87609ffea47b0b,
 /scripts/render.min.js: 68a45378a98ff45272172639cc09011330c114e10dd872f9fcec771e260085db,
 /scripts/main.min.js: b78db4f46476093f3c01202433eeb32fc6d49208aec07f5135e0c45aa0ce2c14,
 /scripts/lib/firebase.min.js: 2beaa7edc6b9e83cf6612a5c59417daae0ccf308b0fca27201bdc048468d2de1,
 /scripts/metadata.min.js: 222ee0ceca80194a5ad855e346ff1246e7b0f5a47ce1a5c1caab54c7d8f04dd8
}>
[flint/deploy: version_files_populated] <FileUploadSpecifier count=3, paths={
 /static/data.min.json: 1cc48ca7d5662b6f7ea566a37de0301b5265a379aa6559568d87609ffea47b0b,
 /scripts/render.min.js: 68a45378a98ff45272172639cc09011330c114e10dd872f9fcec771e260085db,
 /scripts/main.min.js: b78db4f46476093f3c01202433eeb32fc6d49208aec07f5135e0c45aa0ce2c14
} upload_url=https://upload-firebasehosting.googleapis.com/upload/sites/example-site/versions/39a3bf0b3fe052a9/files>
[flint/upload_files: uploaded_file] [1 / 3] /static/data.min.json
[flint/upload_files: uploaded_file] [2 / 3] /scripts/render.min.js
[flint/upload_files: uploaded_file] [3 / 3] /scripts/main.min.js
[flint/deploy: version_finalized] sites/example-site/versions/39a3bf0b3fe052a9
[flint/deploy: version_released] sites/example-site/releases/1779840916813000
```
In the above example; Flint found 7 files in the `./public` directory (after filtering), but only 3 of them were modified and were required to be uploaded to firebase.

NOTE:
  1. Flint uses [PEP 695](https://peps.python.org/pep-0695/) (Type Parameter Syntax) for type-annotated decorators, which requires Python 3.12 or newer.
  2. Flint is not yet available as a package, so you need to manually download and include it in your project, and you must install the `google-api-python-client`, `google-auth` python packages.
