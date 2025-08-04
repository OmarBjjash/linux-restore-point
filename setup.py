from setuptools import setup, find_packages
import os

# Read the long description from the README.md file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='linux-restore-point', # Changed name
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        # No specific Python packages are strictly required beyond standard library
        # for the core functionality. 'pv' is a system dependency.
    ],
    entry_points={
        'console_scripts': [
            'linux-restore-point=linux_restore_point.linux_restore_point:main', # Updated entry point
        ],
    },
    author='Your Name', # <<< REMEMBER TO CHANGE THIS
    author_email='your.email@example.com', # <<< REMEMBER TO CHANGE THIS
    description='A command-line tool for creating and restoring Linux system restore points.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/linux-restore-point', # <<< REMEMBER TO CHANGE THIS
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
