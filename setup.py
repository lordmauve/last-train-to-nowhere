from setuptools import setup, find_packages


setup(
    name="last-train-to-nowhere",
    description='Last Train to Nowhere',
    version="1.0.0",
    packages=find_packages(),
    url='http://www.pyweek.org/e/wasabiparatha/',
    maintainer='Daniel Pope',
    maintainer_email='mauve@mauveweb.co.uk',
    long_description=open('README.rst').read(),
    install_requires=[
        'pyglet>=1.1.4',
    ],
    package_data={
        'wildwest': ['assets/*/*'],
    },
    entry_points={
        'console_scripts': [
            'last-train-to-knowhere = wildwest.__main__:main',
        ]   
    },
)
