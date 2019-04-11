import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="fw_heudiconv",
    version="0.0.1",
    author="Tinashe M. Tapera, Matt Cieslak, Harsha Kethineni",
    author_email="tinashemtapera@gmail.com",
    description="Use heudiconv heuristics for BIDS curation on flywheel",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/PennBBL/fw_heudiconv",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        'console_scripts': [
            'fw_heudiconv=fw_heudiconv.cli.run:main',
        ],
    }
)