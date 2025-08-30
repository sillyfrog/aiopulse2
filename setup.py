"""Pip setup file for aiopulse2 library."""

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="aiopulse2",
    packages=setuptools.find_packages(),
    version="1.0.0",
    license="apache-2.0",
    description="Rollease Acmeda Automate Pulse Hub v2 integration.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sillyfrog/aiopulse2",
    download_url="https://github.com/sillyfrog/aiopulse2/archive/v1.0.0.tar.gz",
    keywords=["automation"],
    install_requires=["async_timeout>=3.0", "websockets>=10.1"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
    ],
    python_requires=">=3.11",
    author="Sillyfrog",
    author_email="tgh@sillyfrog.com",
)
