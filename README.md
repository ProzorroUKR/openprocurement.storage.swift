Backend for https://github.com/openprocurement/openprocurement.documentservice/ for uploading documents to Open Stack Swift storage

Add next settings to development.ini:
```
[app:main]
storage = swift
swift.auth_token = test_auth_token123456789
swift.storage_url = https://test.storage_url/v1/AUTH_ab12
swift.container = test_container_name
```