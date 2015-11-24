import sys
from setuptools import setup
from setuptools.command.test import test as TestCommand

from rdio_dl import __version__


class PyTest(TestCommand):
    def finalize_options(self):
        # XXX sometimes TestCommand is not a newstyle class
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # XXX import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


try:
    with open('README.rst') as readme:
        README = readme.read()
except IOError:
    README = ''

setup(
    name='rdio_dl',
    version=__version__,
    packages=['rdio_dl'],
    install_requires=['requests', 'youtube_dl', 'click'],
    author='Dirley Rodrigues',
    author_email='dirleyrls@gmail.com',
    long_description=README,
    license='MIT',
    test_suite='tests',
    tests_require=['pytest'],
    cmdclass={'test': PyTest},
    scripts=['bin/rdio-dl'],
)
