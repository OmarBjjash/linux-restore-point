from setuptools import setup, find_packages
import os
from linux_restore_point import __version__

# Read the long description from the README.md file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='linux-restore-point', # Changed name
    version=__version__,
    packages=find_packages(),
    install_requires=[

    ],
    entry_points={
        'console_scripts': [
            'linux-restore-point=linux_restore_point.linux_restore_point:main', # Updated entry point
        ],
    },
    author='Omar Bajjash',
    description='A command-line tool for creating and restoring Linux system restore points.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/OmarBjjash/linux-restore-point',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Environment :: Console',
        'Topic :: System :: Archiving :: Backup',
        'Topic :: System :: Recovery',
        'Intended Audience :: System Administrators',
        'Development Status :: 3 - Alpha',
    ],
    python_requires='>=3.6',
)
