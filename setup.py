from setuptools import setup, find_packages
import os

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'README.md')) as f:
    README = f.read()

version = '1.0.6'

requires = [
    'python-swiftclient',
    'python-keystoneclient',
    'rfc6266',
    'setuptools',
    'openprocurement.documentservice>=1.1',
]

test_requires = requires + [
    'pytest',
    'pytest-cov',
    'python-coveralls',
    'mock',
    'webtest',
]

entry_points = {
    'openprocurement.documentservice.plugins': [
        'swift = openprocurement.storage.swift:includeme'
    ]
}

setup(name='openprocurement.storage.swift',
      version=version,
      description="Open Stack Swift storage for OpenProcurement document service",
      long_description=README,
      classifiers=[
          "Framework :: Pylons",
          "License :: OSI Approved :: Apache Software License",
          "Programming Language :: Python",
          "Topic :: Internet :: WWW/HTTP",
          "Topic :: Internet :: WWW/HTTP :: WSGI :: Application"
      ],
      keywords='web services',
      # author='',
      # author_email='',
      url='https://git.prozorro.gov.ua/cdb/openprocurement.storage.swift.git',
      license='Apache License 2.0',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['openprocurement', 'openprocurement.storage'],
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=test_requires,
      extras_require={'test': test_requires},
      test_suite="openprocurement.storage.swift.tests.tests.suite",
      entry_points=entry_points)
