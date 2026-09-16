Backend for https://github.com/ProzorroUKR/openprocurement.documentservice/ for uploading documents to Open Stack Swift storage

Requires Python 3.13 and [uv](https://docs.astral.sh/uv/).

Install:

    uv sync

`documentservice` is pulled from git over SSH, so you need access to
`git.prozorro.gov.ua`.

Run the tests:

    uv run pytest

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
