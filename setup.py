#!/usr/bin/env python

__copyright__ = "Copyright (C) 2013 Ivan D Vasin and Cogo Labs"
__credits__ = ["Dave Bonner", "Ivan D Vasin"]
__maintainer__ = "Ivan D Vasin"
__email__ = "nisavid@gmail.com"
__docformat__ = "restructuredtext"

from setuptools import find_packages as _find_packages, setup as _setup


# basics ----------------------------------------------------------------------

NAME = 'Bedframe'

VERSION = '0.13.1'

SITE_URI = ''

DESCRIPTION = 'A resource-oriented web services framework.'

LONG_DESCRIPTION = DESCRIPTION + '''
'''

LICENSE = 'LGPLv3'

TROVE_CLASSIFIERS = \
    ('Development Status :: 5 - Production/Stable',
     'Intended Audience :: Developers',
     'License :: OSI Approved :: GNU Lesser General Public License v3'
      ' (LGPLv3)',
     'Operating System :: POSIX',
     'Programming Language :: Python :: 2.7',
     'Topic :: Internet :: WWW/HTTP',
     'Topic :: Software Development :: Libraries :: Application Frameworks',
     'Topic :: Software Development :: Libraries :: Python Modules',
     )


# dependencies ----------------------------------------------------------------

SETUP_DEPS = ()

INSTALL_DEPS = ('nisavid-collections',
                'nisavid-datetime',
                'nisavid-lang',
                'nisavid-logging',
                'nisavid-pprint',
                'nisavid-http-common',
                'nisavid-validation',
                'psutil',
                'raven',
                'pytz',
                'requests >1',
                'ujson-bedframe',
                )

EXTRAS_DEPS = {'ldap': ('python-ldap',),
               'memcache': ('python-memcached',),
               'test_ldap': ('nisavid-ldap [openldap]',),
               'tornado': ('tornado-bedframe >3',),
               'tornado_wsgi': ('gevent', 'tornado-bedframe >3'),
               }

TESTS_DEPS = ()

DEPS_SEARCH_URIS = ()


# packages --------------------------------------------------------------------

ROOT_PKG = NAME.lower()

NAMESPACE_PKGS = ()

SCRIPTS_PKG = '.'.join((ROOT_PKG, 'scripts'))

TESTS_PKG = '.'.join((ROOT_PKG, 'tests'))


# entry points ----------------------------------------------------------------

STD_SCRIPTS_PKG_COMMANDS = {}

COMMANDS = {cmd: '{}.{}:{}'.format(SCRIPTS_PKG,
                                   script if isinstance(script, basestring)
                                          else script[0],
                                   'main' if isinstance(script, basestring)
                                          else script[1])
            for cmd, script in STD_SCRIPTS_PKG_COMMANDS.items()}

ENTRY_POINTS = {'console_scripts': ['{} = {}'.format(name, funcpath)
                                    for name, funcpath in COMMANDS.items()]}


if __name__ == '__main__':
    _setup(name=NAME,
           version=VERSION,
           url=SITE_URI,
           description=DESCRIPTION,
           long_description=LONG_DESCRIPTION,
           author=', '.join(__credits__),
           maintainer=__maintainer__,
           maintainer_email=__email__,
           license=LICENSE,
           classifiers=TROVE_CLASSIFIERS,
           setup_requires=SETUP_DEPS,
           install_requires=INSTALL_DEPS,
           extras_require=EXTRAS_DEPS,
           tests_require=TESTS_DEPS,
           dependency_links=DEPS_SEARCH_URIS,
           namespace_packages=NAMESPACE_PKGS,
           packages=_find_packages(),
           test_suite=TESTS_PKG,
           include_package_data=True,
           entry_points=ENTRY_POINTS)
