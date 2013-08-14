from setuptools import setup

try:
    with open('README.rst') as readme:
        README = readme.read()
except IOError:
    README = ''

setup(
    name='rdio_dl',
    version='0.0.1dev',
    packages=['rdio_dl', 'rdio_dl.rdio_simple'],
    install_requires=['youtube_dl', 'requests', 'PyAMF'],
    author='Dirley Rodrigues',
    author_email='dirleyrls@gmail.com',
    long_description=README,
    entry_points={
        'youtube_dl.extractors': [
            'rdio = rdio_dl.extractor:RdioIE',
        ],
    },
)
