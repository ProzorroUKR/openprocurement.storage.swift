from hashlib import md5, sha256
from urllib.parse import quote, urlparse
from uuid import UUID, uuid4

from documentservice.rfc6266 import build_header
from documentservice.storage import (
    HashInvalid,
    KeyNotFound,
    StorageRedirect,
    StorageUploadError,
    get_filename,
)
from requests import RequestException
from swiftclient import ClientException
from swiftclient.client import Connection
from swiftclient.utils import generate_temp_url
from urllib3.exceptions import HTTPError


def compute_hash(fp, buf_size=8192):
    hash_obj = md5()
    spos = fp.tell()
    s = fp.read(buf_size)
    while s:
        if not isinstance(s, bytes):
            s = s.encode("utf-8")
        hash_obj.update(s)
        s = fp.read(buf_size)
    hex_digest = hash_obj.hexdigest()
    fp.seek(spos)
    return hex_digest


def content_disposition(filename):
    # build_header() returns iso-8859-1 bytes; swiftclient wants a str header value
    header = build_header(filename, filename_compat=quote(filename.encode("utf-8")))
    return header.decode("iso-8859-1")


def catch_swift_error(fn):
    def wrapped(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except (ClientException, RequestException, HTTPError) as e:
            raise StorageUploadError from e

    return wrapped


class SwiftStorage:
    connection = None
    container = None

    def __init__(
        self,
        auth_url,
        auth_version,
        username,
        password,
        project_name,
        project_domain_name,
        user_domain_name,
        container,
        proxy_host,
        temp_url_key,
        insecure=False,
    ):
        self.container = container
        os_options = {
            "user_domain_name": user_domain_name,
            "project_domain_name": project_domain_name,
            "project_name": project_name,
        }
        self.connection = Connection(
            authurl=auth_url,
            auth_version=auth_version,
            user=username,
            key=password,
            os_options=os_options,
            insecure=insecure,
        )
        storage_url, _ = self.connection.get_auth()
        self.url_prefix = urlparse(storage_url).path + "/" + self.container
        self.temp_url_key = temp_url_key
        self.proxy_host = proxy_host

    @staticmethod
    def _uuid_to_path(uuid):
        return "/".join([format(i, "x") for i in UUID(uuid).fields])

    @staticmethod
    def _sha256_uuid(in_file):
        spos = in_file.tell()
        uuid = sha256(in_file.read()).hexdigest()[:32]
        in_file.seek(spos)
        return uuid
    

    @catch_swift_error
    def register(self, md5_, sha=None):
        uuid = sha.split(":", 1)[-1][:32] if sha else uuid4().hex
        path = self._uuid_to_path(uuid)
        try:
            etag = self.connection.put_object(
                self.container, path, contents="",
                headers={
                    "X-Object-Meta-hash": md5_, 
                    "If-None-Match": "*", 
                    "Expect": "100-Continue"
                },
            )
            if not etag:
                raise StorageUploadError("register failed: invalid etag for " + uuid)
        except ClientException as e:
            if e.http_status != 412:
                raise
        return uuid

    @catch_swift_error
    def upload(self, post_file, uuid=None):
        filename = get_filename(post_file.filename)
        content_type = post_file.type
        in_file = post_file.file
        uuid_provided = uuid is not None
        if uuid is None:
            uuid = self._sha256_uuid(in_file)

        try:
            path = "/".join([format(i, "x") for i in UUID(uuid).fields])
        except ValueError:
            raise KeyNotFound(uuid)

        try:
            key = self.connection.get_object(self.container, path)[0]

            hash_ = key["x-object-meta-hash"]
            if compute_hash(in_file) != hash_[4:]:
                raise HashInvalid(hash_)

            if key["content-length"] != "0":
                return uuid, "md5:" + key["etag"], content_type, filename

        except ClientException:
            if uuid_provided:
                raise KeyNotFound(uuid)

        etag = self.connection.put_object(
            self.container,
            path,
            contents=in_file,
            content_type=content_type,
            headers={"content_disposition": content_disposition(filename)},
        )
        if not etag:
            raise StorageUploadError("upload failed: invalid etag for " + uuid)
        return uuid, "md5:" + etag, content_type, filename

    def get(self, uuid):
        if "/" in uuid:
            path = uuid
        else:
            try:
                path = self._uuid_to_path(uuid)
            except ValueError:
                raise KeyNotFound(uuid)
        full_path = self.url_prefix + "/" + path
        url = str(generate_temp_url(full_path, 300, self.temp_url_key, "GET", absolute=False))
        raise StorageRedirect("/".join([self.proxy_host] + url.split("/")[4:]))
