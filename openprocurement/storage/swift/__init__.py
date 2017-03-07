from openprocurement.storage.swift.storage import SwiftStorage


def includeme(config):
    settings = config.registry.settings
    if 'swift.auth_token' in settings and 'swift.storage_url' in settings and 'swift.container' in settings:
        config.registry.storage = SwiftStorage(
            settings['swift.auth_token'],
            settings['swift.storage_url'],
            settings['swift.container'],
        )
    else:
        raise
