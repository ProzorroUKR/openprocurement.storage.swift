from .storage import SwiftStorage

REQUIRED_SETTINGS = (
    'swift.auth_url',
    'swift.auth_version',
    'swift.username',
    'swift.password',
    'swift.project_name',
    'swift.project_domain_name',
    'swift.user_domain_name',
    'swift.container',
    'swift.proxy_host',
    'swift.temp_url_key',
)


def includeme(config):
    settings = config.registry.settings
    missing = [name for name in REQUIRED_SETTINGS if name not in settings]
    if missing:
        raise ValueError('{} are required'.format(', '.join(missing)))
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
        settings.get('swift.insecure', False),
    )
