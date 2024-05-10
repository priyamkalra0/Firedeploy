# Firedeploy: Quickly and easily deploy static websites to [Firebase](https://web.app)
## Usage
The `firebase-admin` and `requests` packages must be installed beforehand.    
The tool is not yet available as a package, so you need to manually download and include it in your project, after that it can be used as such:

```py
from firedeploy import Firebase, Certificate
certificate = Certificate({
    "type": "service_account",
    "token_uri": "https://oauth2.googleapis.com/token",
    "private_key": "-----BEGIN PRIVATE KEY-----\n[EXAMPLE]\n-----END PRIVATE KEY-----\n",
    "client_email": "example@example.iam.gserviceaccount.com",
})

firebase = Firebase("example", certificate)
firebase.deploy("./public")
```

The above snippet will create a new version, add all files in the ./public directory to that version, and deploy it.
It will also print progress to the console like so:
```
Access token: ya29XXXXXXX
Version: 2af6c788210327b6

[1/11 file_uploaded] 740f15c1e0c93dbebbd2bced77809730a3c3051729bf5252df2ec61b385e79c1
[2/11 file_uploaded] 698d38d849d0e46360063fad5fede42b999b352f3a9ef353e6b5f6a326f42795
[3/11 file_uploaded] a19d1b0bd36cfb13a555c77b546fd23e951dfb3ea422541de59b38ca1024ba48
[4/11 file_uploaded] 30a30fcafedc56a5000a20d395e78085f14fa2c8ce25b6e1c92140d90b0bafdf
[5/11 file_uploaded] 33fcca0ce5f7e8fb247bd2ce58e0ea8f23a9e363e556040ff93ac227809cfc2b
[6/11 file_uploaded] 5e29c454088f5d62b5a86a15b40378b1c1ff88f8f1f400e801e88f1de2ede75b
[7/11 file_uploaded] 6b0c55382da80dd05f7217b44b694fd4231cb86f1358427cf62cf5e32baa082f
[8/11 file_uploaded] 667828539fb77932acca074cec0a85ac1d2a867866540ce0bb5912782d71e5e9
[9/11 file_uploaded] ef59d5ab21ef1d54761757984ae4184b886182ba3ec20c2229a82529779c953a
[10/11 file_uploaded] 00836c009cc12619399d9ac893a2bde2da9b2d58e3b92309fac7f8d21aaa657b
[11/11 file_uploaded] 176dc7450a577b7917e4b5e84249dc0351f953e42759e78ee5154721d85d44ba
[success] Deployed to example.web.app
```
