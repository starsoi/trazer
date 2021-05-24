import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="trazer",
    author="Hongyan Zhang",
    author_email="starsoi@gmail.com",
    description="A lightweight trace analysis framework.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/starsoi/trazer",
    project_urls={},
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Embedded Systems",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Intended Audience :: Developers",
    ],
    package_dir={"": "."},
    packages=["trazer"],
    python_requires=">=3.8",
)
