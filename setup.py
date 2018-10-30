# Copyright 2018 miruka
# This file is part of lunakit, licensed under LGPLv3.

"lunakit setuptools file"

from setuptools import setup, find_packages

from lunakit import __about__


def get_readme():
    with open("README.md", "r") as readme:
        return readme.read()


setup(
    name        = __about__.__pkg_name__,
    version     = __about__.__version__,

    author       = __about__.__author__,
    author_email = __about__.__email__,
    license      = __about__.__license__,

    description                   = __about__.__doc__,
    long_description              = get_readme(),
    long_description_content_type = "text/markdown",

    python_requires  = ">=3.6, <4",
    install_requires = [
        "appdirs",
        "atomicfile",
        "blessed",
        "cached_property",
        "dataclasses;python_version<'3.7'",
        "docopt",
        "lazy_object_proxy",
        "logzero",
        "pendulum",
        "pybooru",
        "pygments",
        "requests",
        "setuptools",
        "simplejson",
        "urllib3",
        "whratio",
    ],

    include_package_data = True,
    package_data         = {__about__.__pkg_name__: ["data/*"]},
    packages             = find_packages(),
    entry_points    = {
        "console_scripts": [
            f"{__about__.__pkg_name__}={__about__.__pkg_name__}.cli:main"
        ]
    },

    keywords = "booru danbooru api client images ugoira anime cli terminal " \
               "scrap tags download filter order",

    url = "https://github.com/mirukan/lunakit",

    classifiers=[
        "Development Status :: 3 - Alpha",
        # "Development Status :: 4 - Beta",
        # "Development Status :: 5 - Production/Stable",

        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",

        "Environment :: Console",

        "Topic :: Utilities",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
        "Topic :: Software Development :: Libraries :: Python Modules",

        ("License :: OSI Approved :: "
         "GNU Lesser General Public License v3 or later (LGPLv3+)"),

        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",

        "Natural Language :: English",

        "Operating System :: POSIX",
    ]
)
