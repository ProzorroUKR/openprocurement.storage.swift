import unittest
from unittest import mock

from documentservice.storage import (
    ContentUploaded,
    HashInvalid,
    KeyNotFound,
    StorageRedirect,
    StorageUploadError,
)
from requests import RequestException
from swiftclient import ClientException, Connection

import storage_swift
from storage_swift import SwiftStorage
from storage_swift.tests.base import BaseWebTest


class Uuid4Mock:
    hex = "9a21e3cb7a4042edad9838ac4b19b358"


class PostFileMock:
    filename = "file_name"
    type = "text/plain"
    file = "Test text"


class SwiftStorageTests(unittest.TestCase):
    def setUp(self):
        self.container = "test_container_name"
        self.etag = "1234abcd"
        self.md5 = f"md5:{self.etag}"
        self.path = "9a21e3cb/7a40/42ed/ad/98/38ac4b19b358"
        Connection.get_auth = mock.MagicMock()
        Connection.get_auth.return_value = (
            "https://some-swift-host.com/v1/AUTH_user_id",
            "some_token",
        )
        self.storage = SwiftStorage(
            "auth_url",
            "auth_version",
            "username",
            "password",
            "project_name",
            "project_domain_name",
            "user_domain_name",
            self.container,
            "https://swift-proxy-test.com",
            "temp_url_key",
        )
        self.storage.connection.put_object = mock.MagicMock()
        self.storage.connection.put_object.return_value = self.etag
        self.storage.connection.get_object = mock.MagicMock()
        self.storage.connection.get_object.return_value = [
            {
                "content-length": "3032",
                "content-disposition": "content-disposition",
                "etag": self.etag,
                "content-type": PostFileMock.type,
                "x-object-meta-hash": self.md5,
            },
            PostFileMock.file,
        ]

    def test_call_register(self):
        with mock.patch("storage_swift.storage.uuid4", return_value=Uuid4Mock):
            uuid = self.storage.register(self.md5)
            expected = [
                mock.call.put_object(
                    self.container,
                    self.path,
                    contents="",
                    headers={
                        "X-Object-Meta-hash": self.md5,
                        "If-None-Match": "*",
                        "Expect": "100-Continue",
                    },
                )
            ]

            self.assertEqual(self.storage.connection.put_object.mock_calls, expected)
            self.assertEqual(uuid, Uuid4Mock.hex)

    def test_call_upload_when_uuid_is_None(self):
        with (
            mock.patch.object(
                SwiftStorage, "_sha256_uuid", return_value=Uuid4Mock.hex
            ),
            mock.patch(
                "storage_swift.storage.get_filename", return_value=PostFileMock.filename
            ),
            mock.patch(
                "storage_swift.storage.content_disposition",
                return_value="content_disposition",
            ),
            mock.patch(
                "storage_swift.storage.compute_hash", return_value=Uuid4Mock.hex
            ),
        ):
            self.storage.connection.get_object.side_effect = ClientException("not found")
            self.storage.connection.put_object.return_value = Uuid4Mock.hex
            uuid, md5, content_type, filename = self.storage.upload(PostFileMock)
            expected = [
                mock.call.put_object(
                    self.container,
                    self.path,
                    contents=PostFileMock.file,
                    content_type=PostFileMock.type,
                    headers={"content_disposition": "content_disposition"},
                )
            ]

            self.assertEqual(self.storage.connection.put_object.mock_calls, expected)
            self.assertEqual(uuid, Uuid4Mock.hex)
            self.assertEqual(md5, "md5:" + Uuid4Mock.hex)
            self.assertEqual(content_type, PostFileMock.type)
            self.assertEqual(filename, PostFileMock.filename)

    def test_call_upload_when_uuid_is_None_and_content_already_exists(self):
        with (
            mock.patch.object(
                SwiftStorage, "_sha256_uuid", return_value=Uuid4Mock.hex
            ),
            mock.patch(
                "storage_swift.storage.get_filename", return_value=PostFileMock.filename
            ),
            mock.patch(
                "storage_swift.storage.compute_hash", return_value=self.etag
            ),
        ):
            uuid, md5, content_type, filename = self.storage.upload(PostFileMock)
            self.assertEqual(uuid, Uuid4Mock.hex)
            self.assertEqual(md5, self.md5)
            self.assertEqual(self.storage.connection.put_object.call_count, 0)

    def test_call_upload_when_uuid_is_not_None(self):
        with mock.patch(
            "storage_swift.storage.get_filename", return_value=PostFileMock.filename
        ), mock.patch(
            "storage_swift.storage.compute_hash", return_value=self.etag
        ), mock.patch(
            "storage_swift.storage.content_disposition",
            return_value="content_disposition",
        ):
            self.storage.connection.get_object.return_value = [
                {
                    "content-length": "0",
                    "content-disposition": "content-disposition",
                    "etag": self.etag,
                    "content-type": PostFileMock.type,
                    "x-object-meta-hash": self.md5,
                },
                "",
            ]
            uuid, md5, content_type, filename = self.storage.upload(
                PostFileMock, Uuid4Mock.hex
            )
            expected = [
                mock.call.put_object(
                    self.container,
                    self.path,
                    contents=PostFileMock.file,
                    content_type=PostFileMock.type,
                    headers={"content_disposition": "content_disposition"},
                )
            ]

            self.assertEqual(
                self.storage.connection.put_object.mock_calls, expected
            )
            self.assertEqual(uuid, Uuid4Mock.hex)
            self.assertEqual(md5, self.md5)
            self.assertEqual(content_type, PostFileMock.type)
            self.assertEqual(filename, PostFileMock.filename)

    def test_call_upload_when_content_uploaded_for_this_uuid(self):
        with mock.patch(
            "storage_swift.storage.get_filename", return_value=PostFileMock.filename
        ), mock.patch(
            "storage_swift.storage.compute_hash", return_value=self.etag
        ):
            self.storage.connection.get_object.return_value = [
                {
                    "content-length": "3032",
                    "content-disposition": "content-disposition",
                    "etag": self.etag,
                    "content-type": PostFileMock.type,
                    "x-object-meta-hash": self.md5,
                },
                PostFileMock.file,
            ]
            uuid, md5, content_type, filename = self.storage.upload(
                PostFileMock, Uuid4Mock.hex
            )
            self.assertEqual(uuid, Uuid4Mock.hex)
            self.assertEqual(md5, self.md5)

    def test_call_upload_when_incorrect_hash(self):
        with mock.patch(
            "storage_swift.storage.get_filename", return_value=PostFileMock.filename
        ), mock.patch(
            "storage_swift.storage.compute_hash", return_value="other_hash"
        ):
            self.storage.connection.get_object.return_value = [
                {
                    "content-length": "0",
                    "content-disposition": "content-disposition",
                    "etag": self.etag,
                    "content-type": PostFileMock.type,
                    "x-object-meta-hash": self.md5,
                },
                "",
            ]
            with self.assertRaises(HashInvalid) as hash_invalid:
                self.storage.upload(PostFileMock, Uuid4Mock.hex)

            self.assertEqual(str(hash_invalid.exception), self.md5)

    def test_call_upload_when_incorrect_uuid(self):
        with mock.patch(
            "storage_swift.storage.get_filename", return_value=PostFileMock.filename
        ):
            self.storage.connection.get_object.side_effect = ClientException(
                "exception"
            )
            with self.assertRaises(KeyNotFound) as key_not_found:
                self.storage.upload(PostFileMock, Uuid4Mock.hex)

            self.assertEqual(str(key_not_found.exception).strip("'"), Uuid4Mock.hex)

    def test_call_get(self):
        with self.assertRaises(StorageRedirect) as storage_redirect:
            self.storage.get(Uuid4Mock.hex)
        url = "https://swift-proxy-test.com/9a21e3cb/7a40/42ed/ad/98/38ac4b19b358"
        exception_url = storage_redirect.exception.url
        self.assertTrue(exception_url.startswith(url))
        self.assertTrue("temp_url_sig" in exception_url)
        self.assertTrue("temp_url_expires" in exception_url)

    def test_put_object_raise_swift_exception(self):
        self.storage.connection.put_object.side_effect = ClientException("Swift error")
        with self.assertRaises(StorageUploadError):
            self.storage.register(self.md5)

        with mock.patch.object(
            SwiftStorage, "_sha256_uuid", return_value=Uuid4Mock.hex
        ), mock.patch(
            "storage_swift.storage.compute_hash", return_value=Uuid4Mock.hex
        ):
            self.storage.connection.get_object.side_effect = ClientException("not found")
            with self.assertRaises(StorageUploadError):
                self.storage.upload(PostFileMock)

    def test_put_object_raise_requests_exception(self):
        self.storage.connection.put_object.side_effect = RequestException(
            "Connection error"
        )
        with self.assertRaises(StorageUploadError):
            self.storage.register(self.md5)

        with mock.patch.object(
            SwiftStorage, "_sha256_uuid", return_value=Uuid4Mock.hex
        ), mock.patch(
            "storage_swift.storage.compute_hash", return_value=Uuid4Mock.hex
        ):
            self.storage.connection.get_object.side_effect = ClientException("not found")
            with self.assertRaises(StorageUploadError):
                self.storage.upload(PostFileMock)

    def test_put_object_return_none(self):
        self.storage.connection.put_object.return_value = None

        with self.assertRaises(StorageUploadError):
            self.storage.register(self.md5)

        with mock.patch.object(
            SwiftStorage, "_sha256_uuid", return_value=Uuid4Mock.hex
        ), mock.patch(
            "storage_swift.storage.compute_hash", return_value=Uuid4Mock.hex
        ):
            self.storage.connection.get_object.side_effect = ClientException("not found")
            with self.assertRaises(StorageUploadError):
                self.storage.upload(PostFileMock)


class PluginLoadTest(BaseWebTest):
    def test_plugin_loaded_via_entry_point(self):
        self.assertIsInstance(self.storage, SwiftStorage)

    def test_register(self):
        response = self.app.post(
            "/register", {"hash": "md5:" + "0" * 32, "filename": "file.txt"}
        )
        self.assertEqual(response.status, "201 Created")
        self.assertEqual(response.content_type, "application/json")
        self.assertIn("http://localhost/upload/", response.json["upload_url"])
        self.assertTrue(self.connection.put_object.called)


class IncludemeTest(unittest.TestCase):
    def test_missing_settings(self):
        config = mock.Mock()
        config.registry.settings = {"swift.auth_url": "url", "swift.username": "user"}
        with self.assertRaises(ValueError) as caught:
            storage_swift.includeme(config)
        self.assertEqual(
            str(caught.exception),
            "swift.auth_version, swift.password, swift.project_name, swift.project_domain_name, "
            "swift.user_domain_name, swift.container, swift.proxy_host, swift.temp_url_key are required",
        )
