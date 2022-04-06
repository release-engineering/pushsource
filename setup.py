from setuptools import setup, find_packages


def get_description():
    return "A library to load push items from a variety of sources"


def get_long_description():
    with open("README.md") as f:
        text = f.read()

    # Long description is everything after README's initial heading
    idx = text.find("\n\n")
    return text[idx:]


def get_requirements():
    with open("requirements.in") as f:
        return f.read().splitlines()


setup(
    name="pushsource",
    version="2.18.2",
    packages=find_packages("src"),
    package_dir={"": "src"},
    include_package_data=True,
    url="https://github.com/release-engineering/pushsource",
    license="GNU General Public License",
    description=get_description(),
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    install_requires=get_requirements(),
    python_requires=">=2.6",
    entry_points={"console_scripts": ["pushsource-ls=pushsource._impl.list_cmd:main"]},
    project_urls={
        "Documentation": "https://release-engineering.github.io/pushsource/",
        "Changelog": "https://github.com/release-engineering/pushsource/blob/master/CHANGELOG.md",
    },
)
