Backend for https://github.com/openprocurement/openprocurement.documentservice/ for uploading documents to Open Stack Swift storage


Install package

    pip install git+http://git.mm.local:8085/openprocurement/openprocurement.storage.swift.git#egg=storage_swift

Add next settings to development.ini:
```
[app:main]
storage = swift
swift.auth_token = test_auth_token123456789
swift.storage_url = https://test.storage_url/v1/AUTH_ab12
swift.container = test_container_name
```