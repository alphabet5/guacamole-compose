import setuptools

with open("README.md", "r") as f:
    long_description = f.read()

with open('guacamole_compose/VERSION', 'r') as f:
    version = f.read()

setuptools.setup(
    name="guacamole-compose",
    version=version,
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
    install_requires=['ldap3>=2.9',
                      'pymysql>=1.0.2',
                      'docker>=5.0.0',
                      'sqlalchemy>=1.4.11',
                      'yamlarg>=0.0.6',
                      'pyyaml>=5.4.1',
                      'cryptography>=3.4.7',
                      'cffi>=1.14.5',
                      'dnspython>=2.1.0'],
)
