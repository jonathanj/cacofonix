import os
import codecs
import versioneer
from setuptools import setup, find_packages

HERE = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    with codecs.open(os.path.join(HERE, *parts), 'rb', 'utf-8') as f:
        return f.read()


setup(
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    name='cacofonix',
    description='Python tool to generate changelogs from structured data.',
    license='MIT',
    url='https://github.com/jonathanj/cacofonix',
    author='Jonathan Jacobs',
    author_email='jonathan@jsphere.com',
    maintainer='Jonathan Jacobs',
    maintainer_email='jonathan@jsphere.com',
    long_description=read('README.rst'),
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    entry_points={
        'console_scripts': ['cacofonix=cacofonix.main:main'],
    },
    include_package_data=True,
    zip_safe=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Build Tools',
    ],
    install_requires=[
        'towncrier @ git+https://github.com/hawkowl/towncrier.git#egg=towncrier',
        'pyyaml >= 5.3',
        'aniso8601 >= 8.0.0',
    ],
)
