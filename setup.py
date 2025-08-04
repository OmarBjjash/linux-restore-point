from setuptools import setup, find_packages

setup(
    name="linux-restore-point",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "colorama",
    ],
    entry_points={
        "console_scripts": [
            "linux-restore-point = linux_restore_point.linux_restore_point:main",
        ],
    },
    author="System Admin",
    author_email="admin@example.com",
    description="Linux Restore Point - System Snapshot Utility",
    long_description="A command-line tool for creating and restoring Linux system restore points",
    license="MIT",
    keywords="linux system restore backup snapshot",
    url="https://github.com/yourusername/linux-restore-point",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Topic :: System :: Recovery Tools",
        "Topic :: System :: Systems Administration",
    ],
)
