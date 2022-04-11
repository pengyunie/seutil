import setuptools

with open("README.rst", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="seutil",
    version="0.7.1",
    author="Pengyu Nie",
    author_email="prodigy.sov@gmail.com",
    description="Python utilities for SE research",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url="https://github.com/pengyunie/seutil",
    packages=setuptools.find_packages(exclude=["tests"]),
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX :: Linux",
    ],
    install_requires=[
        "ijson~=3.1.4",
        "jsonargparse[all]>=4.1.4,<4.7.0",
        "numpy>=1.14.4",
        "PyGitHub>=1.40",
        "PyYAML>=5.1",
        "recordclass>=0.11.1",
        "tqdm>=4.62.3,<4.65.0",
        "typing_inspect>=0.4.0",
        "unidiff>=0.5.5",
        "varname>=0.7.1",
    ],
)
