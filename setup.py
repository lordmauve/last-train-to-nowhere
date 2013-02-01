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
    classifiers=[
        'Topic :: Games/Entertainment :: Side-Scrolling/Arcade Games',
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 2 :: Only',
        'Operating System :: OS Independent',
        'Natural Language :: English'
    ]
)
