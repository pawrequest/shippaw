import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="AmDesp",
    version="0.1",
    author="Paul Sees",
    author_email="paul.sees.27@gmail.com",
    description="Commence Rm -> Desptachbay shipping middleware",
    install_requires=['suds-py3', 'requests', 'pywinauto', 'pyexcel_ods3', 'psutil'],
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://test.pypi.org/project/despatchbay/",
    packages=setuptools.find_namespace_packages(
        include=['despatchbay', 'suds-py3', 'requests', 'pywinauto', 'pyexcel_ods3', 'psutil', 'AmDesp_python-dateutil']),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
