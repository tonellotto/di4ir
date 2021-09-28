from setuptools import setup, find_packages

readme = ''

setup(
    name='DeepImpact',
    version='0.0.1',
    url='https://github.com/tonellotto/di4ir',
    packages=['deepimpact'],
    long_description=readme,
    install_requires=[
        'transformers==3.4.0',
    ],
)
