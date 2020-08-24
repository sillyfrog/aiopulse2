"""Pip setup file for aiopulse2 library."""
from distutils.core import setup

setup(
    name="aiopulse2",
    packages=["aiopulse2"],
    version="0.5.0",
    license="apache-2.0",
    description="Python module for Rollease Acmeda Automate integration.",
    url="https://github.com/sillyfrog/aiopulse2",
    # download_url="https://github.com/sillyfrog/aiopulse2/archive/v0.4.0.tar.gz",
    keywords=["automation"],
    install_requires=["asyncio", "async_timeout"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
    ],
)
