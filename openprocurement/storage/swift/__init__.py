from openprocurement.storage.swift.storage import SwiftStorage


def includeme(config):
    settings = config.registry.settings
    if ('swift.auth_url' in settings and 'swift.auth_version' in settings and 'swift.username' in settings
        and 'swift.password' in settings and 'swift.project_name' in settings and 'swift.project_domain_name' in settings
        and 'swift.user_domain_name' in settings and 'swift.container' in settings):
        config.registry.storage = SwiftStorage(
            settings['swift.auth_url'],
            settings['swift.auth_version'],
            settings['swift.username'],
            settings['swift.password'],
            settings['swift.project_name'],
            settings['swift.project_domain_name'],
            settings['swift.user_domain_name'],
            settings['swift.container'],
            settings['swift.proxy_host'],
            settings['swift.temp_url_key'],
            settings.get('swift.insecure', False)
        )
    else:
        raise Exception('Wrong settings of SwiftStorage')
