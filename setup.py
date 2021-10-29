import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyEA",
    version="0.0.1",
    author="MintX",
    author_email="",
    description="A python adaptation of event assembler",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MinN-11/PyEA",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=["pyEA", "pyEA/FE8"],
    python_requires=">=3.6",
    install_requires=[
      'numpy', 'javaobj-py3', 'Pillow', 'varname'
    ],
)
