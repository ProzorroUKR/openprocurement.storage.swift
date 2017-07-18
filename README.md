Backend for https://github.com/openprocurement/openprocurement.documentservice/ for uploading documents to Open Stack Swift storage


Install package

    pip install git+https://git.prozorro.gov.ua/mk/openprocurement.storage.swift.git#egg=storage_swift

Add next settings to service.ini:
```
[app:docservice]
storage = swift
swift.auth_url = https://auth_url/v3
swift.auth_version = 3
swift.username = username
swift.password = password
swift.project_name = project_name
swift.project_domain_name = default
swift.user_domain_name = default
swift.container = name_container
```
