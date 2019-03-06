Backend for https://github.com/ProzorroUKR/openprocurement.documentservice/ for uploading documents to Open Stack Swift storage


Install package
```
pip install git+https://git.prozorro.gov.ua/cdb/openprocurement.storage.swift.git
```
    
Install package for development with documentservice
```
git clone git@git.prozorro.gov.ua:cdb/openprocurement.documentservice.git
cd openprocurement.documentservice
pip install -r requirements.txt
pip install -e .[test,docs]
git clone git@git.prozorro.gov.ua:cdb/openprocurement.storage.swift.git ./src/openprocurement.storage.swift
pip install -e src/openprocurement.storage.swift[test]
```

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
swift.proxy_host = http://some_proxy
swift.container = name_container
swift.temp_url_key = temp_url
```
