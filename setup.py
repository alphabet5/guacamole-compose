import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="guacamole-compose",
    version="0.0.5",
    author="John Burt",
    author_email="johnburt.jab@gmail.com",
    description="Easy deployment of Apache Guacamole.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/alphabet5/guacamole-compose",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
    entry_points={'console_scripts': ['guacamole-compose=guacamole_compose.cli:main']},
    include_package_data=True,
    package_data={'guacamole_compose': ['*', 'templates/*'], },
)
