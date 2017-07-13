from swiftclient import ClientException
from swiftclient.client import Connection
from openprocurement.documentservice.storage import HashInvalid, KeyNotFound, ContentUploaded, get_filename
from rfc6266 import build_header
from urllib import quote
from uuid import uuid4, UUID
from hashlib import md5


def compute_hash(fp, buf_size=8192):
    hash_obj = md5()
    spos = fp.tell()
    s = fp.read(buf_size)
    while s:
        if not isinstance(s, bytes):
            s = s.encode('utf-8')
        hash_obj.update(s)
        s = fp.read(buf_size)
    hex_digest = hash_obj.hexdigest()
    fp.seek(spos)
    return hex_digest


class SwiftStorage:
    connection = None
    container = None

    def __init__(self, auth_url, auth_version, username, password, project_name, project_domain_name,
                 user_domain_name, container):
        self.container = container
        os_options = {
            'user_domain_name': user_domain_name,
            'project_domain_name': project_domain_name,
            'project_name': project_name
        }
        self.connection = Connection(
            authurl=auth_url,
            auth_version=auth_version,
            user=username,
            key=password,
            os_options=os_options,
        )

    def register(self, md5):
        uuid = uuid4().hex
        path = '/'.join([format(i, 'x') for i in UUID(uuid).fields])
        self.connection.put_object(self.container, path, contents='', headers={"X-Object-Meta-hash": md5})
        return uuid

    def upload(self, post_file, uuid=None):
        filename = get_filename(post_file.filename)
        content_type = post_file.type
        in_file = post_file.file
        if uuid is None:
            uuid = uuid4().hex
            path = '/'.join([format(i, 'x') for i in UUID(uuid).fields])
        else:
            try:
                path = '/'.join([format(i, 'x') for i in UUID(uuid).fields])
            except ValueError:
                raise KeyNotFound(uuid)

            try:
                key = self.connection.get_object(self.container, path)[0]
            except ClientException:
                raise KeyNotFound(uuid)

            if key['content-length'] != '0':
                raise ContentUploaded(uuid)

            hash = key['x-object-meta-hash']
            if compute_hash(in_file) != hash[4:]:
                raise HashInvalid(hash)

        etag = self.connection.put_object(
            self.container,
            path,
            contents=in_file,
            content_type=content_type,
            headers={"content_disposition": build_header(filename, filename_compat=quote(filename.encode('utf-8')))}
        )
        return uuid, 'md5:' + etag, content_type, filename

    def get(self, uuid):
        if '/' in uuid:
            path = uuid
        else:
            try:
                UUID(uuid)
            except ValueError:
                raise KeyNotFound(uuid)
            path = '/'.join([format(i, 'x') for i in UUID(uuid).fields])

        try:
            object = self.connection.get_object(self.container, path)
        except ClientException:
            raise KeyNotFound(uuid)

        head = object[0]
        content = object[1]
        content_disposition = head.get('content-disposition')

        return {'Content-Type': str(head['content-type']),
                'Content-Disposition': content_disposition.encode('utf8') if content_disposition else None,
                'Content': content}
