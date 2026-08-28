import os
import unittest
from unittest import mock

import webtest


class BaseWebTest(unittest.TestCase):

    """Base Web Test to test storage_swift."""

    def setUp(self):
        # SwiftStorage.__init__ calls get_auth() eagerly, so Connection has to be
        # patched while the app is being built, not after.
        with mock.patch('storage_swift.storage.Connection') as mock_connection_cls:
            self.connection = mock_connection_cls.return_value
            self.connection.get_auth.return_value = (
                'https://some-swift-host.com/v1/AUTH_user_id', 'some_token')
            self.connection.put_object.return_value = '1234abcd'

            self.app = webtest.TestApp(
                "config:tests.ini", relative_to=os.path.dirname(__file__))

        self.app.authorization = ('Basic', ('broker', 'broker'))
        self.storage = self.app.app.registry.storage
