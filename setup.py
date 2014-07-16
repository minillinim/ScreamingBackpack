from distutils.core import setup

setup(
    name='ScreamingBackpack',
    version='0.2.1',
    author='Michael Imelfort',
    author_email='mike@mikeimelfort.com',
    packages=['screamingbackpack'],
    scripts=['bin/screamingBackpack'],
    url='http://pypi.python.org/pypi/ScreamingBackpack/',
    license='GPLv3',
    description='ScreamingBackpack',
    long_description=open('README.md').read(),
    install_requires=[],
)

