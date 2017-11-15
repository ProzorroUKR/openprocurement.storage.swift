import mock
import unittest
from swiftclient import ClientException, Connection
from openprocurement.documentservice.storage import HashInvalid, KeyNotFound, ContentUploaded, StorageRedirect
from openprocurement.storage.swift.storage import SwiftStorage, InvalidEtagError


class Uuid4Mock(object):
    hex = '9a21e3cb7a4042edad9838ac4b19b358'

class PostFileMock(object):
    filename = 'file_name'
    type = 'text/plain'
    file = 'Test text'


class SwiftStorageTests(unittest.TestCase):
    def setUp(self):
        self.container = 'test_container_name'
        self.etag = '1234abcd'
        self.md5 = 'md5:{}'.format(self.etag)
        self.path = '9a21e3cb/7a40/42ed/ad/98/38ac4b19b358'
        Connection.get_auth = mock.MagicMock()
        Connection.get_auth.return_value = (u'https://some-swift-host.com/v1/AUTH_user_id', 'some_token')
        self.storage = SwiftStorage('auth_url', 'auth_version', 'username', 'password', 'project_name', 'project_domain_name', 'user_domain_name', self.container, 'https://swift-proxy-test.com', 'temp_url_key')
        self.storage.connection.put_object = mock.MagicMock()
        self.storage.connection.put_object.return_value = self.etag
        self.storage.connection.get_object = mock.MagicMock()
        self.storage.connection.get_object.return_value = [
            {'content-length': '3032',
             'content-disposition': 'content-disposition',
             'etag': self.etag,
             'content-type': PostFileMock.type},
            PostFileMock.file]

    def test_call_register(self):
        with mock.patch('openprocurement.storage.swift.storage.uuid4', return_value=Uuid4Mock):
            uuid = self.storage.register(self.md5)
            expected = [mock.call.put_object(self.container, self.path, contents='', headers={'X-Object-Meta-hash': self.md5})]

            self.assertEqual(self.storage.connection.put_object.mock_calls, expected)
            self.assertEqual(uuid, Uuid4Mock.hex)

    def test_call_upload_when_uuid_is_None(self):
        with mock.patch('openprocurement.storage.swift.storage.uuid4', return_value=Uuid4Mock):
            with mock.patch('openprocurement.storage.swift.storage.get_filename', return_value=PostFileMock.filename):
                with mock.patch('openprocurement.storage.swift.storage.build_header', return_value='content_disposition'):
                    uuid, md5, content_type, filename = self.storage.upload(PostFileMock)
                    expected = [mock.call.put_object(self.container,
                                                     self.path,
                                                     contents=PostFileMock.file,
                                                     content_type=PostFileMock.type,
                                                     headers={"content_disposition": 'content_disposition'})]

                    self.assertEqual(self.storage.connection.put_object.mock_calls, expected)
                    self.assertEqual(uuid, Uuid4Mock.hex)
                    self.assertEqual(md5, self.md5)
                    self.assertEqual(content_type, PostFileMock.type)
                    self.assertEqual(filename, PostFileMock.filename)

    def test_call_upload_when_uuid_is_not_None(self):
        with mock.patch('openprocurement.storage.swift.storage.get_filename', return_value=PostFileMock.filename):
            with mock.patch('openprocurement.storage.swift.storage.compute_hash', return_value=self.etag):
                with mock.patch('openprocurement.storage.swift.storage.build_header', return_value='content_disposition'):
                    self.storage.connection.get_object.return_value = [
                        {'content-length': '0',
                         'content-disposition': 'content-disposition',
                         'etag': self.etag,
                         'content-type': PostFileMock.type,
                         'x-object-meta-hash': self.md5},
                        '']
                    uuid, md5, content_type, filename = self.storage.upload(PostFileMock, Uuid4Mock.hex)
                    expected = [mock.call.put_object(self.container,
                                                     self.path,
                                                     contents=PostFileMock.file,
                                                     content_type=PostFileMock.type,
                                                     headers={"content_disposition": 'content_disposition'})]

                    self.assertEqual(self.storage.connection.put_object.mock_calls, expected)
                    self.assertEqual(uuid, Uuid4Mock.hex)
                    self.assertEqual(md5, self.md5)
                    self.assertEqual(content_type, PostFileMock.type)
                    self.assertEqual(filename, PostFileMock.filename)

    def test_call_upload_when_content_uploaded_for_this_uuid(self):
        with mock.patch('openprocurement.storage.swift.storage.get_filename', return_value=PostFileMock.filename):
            with self.assertRaises(ContentUploaded) as content_uploaded:
                self.storage.upload(PostFileMock, Uuid4Mock.hex)

            self.assertEqual(content_uploaded.exception.message, Uuid4Mock.hex)

    def test_call_upload_when_incorrect_hash(self):
        with mock.patch('openprocurement.storage.swift.storage.get_filename', return_value=PostFileMock.filename):
            with mock.patch('openprocurement.storage.swift.storage.compute_hash', return_value='other_hash'):
                with self.assertRaises(HashInvalid) as hash_invalid:
                    self.storage.connection.get_object.return_value = [
                        {'content-length': '0',
                         'content-disposition': 'content-disposition',
                         'etag': self.etag,
                         'content-type': PostFileMock.type,
                         'x-object-meta-hash': self.md5},
                        '']
                    self.storage.upload(PostFileMock, Uuid4Mock.hex)

                self.assertEqual(hash_invalid.exception.message, self.md5)

    def test_call_upload_when_incorrect_uuid(self):
        with mock.patch('openprocurement.storage.swift.storage.get_filename', return_value=PostFileMock.filename):
            with self.assertRaises(KeyNotFound) as key_not_found:
                self.storage.connection.get_object.side_effect = ClientException('exception')
                self.storage.upload(PostFileMock, Uuid4Mock.hex)

            self.assertEqual(key_not_found.exception.message, Uuid4Mock.hex)

    def test_call_get(self):
        with self.assertRaises(StorageRedirect) as storage_redirect:
            self.storage.get(Uuid4Mock.hex)
        url = 'https://swift-proxy-test.com/v1/AUTH_user_id/test_container_name/9a21e3cb/7a40/42ed/ad/98/38ac4b19b358'
        exception_url = storage_redirect.exception.url
        self.assertTrue(exception_url.startswith(url))
        self.assertTrue('temp_url_sig' in exception_url)
        self.assertTrue('temp_url_expires' in exception_url)

    def test_put_object_return_none(self):
        self.storage.connection.put_object.return_value = None

        with self.assertRaises(InvalidEtagError):
            self.storage.register(self.md5)

        with self.assertRaises(InvalidEtagError):
            self.storage.upload(PostFileMock)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(SwiftStorageTests))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
