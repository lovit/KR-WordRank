import krwordrank
from setuptools import setup, find_packages

with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="krwordrank",
    version=krwordrank.__version__,
    author=krwordrank.__author__,
    author_email='soy.lovit@gmail.com',
    url='https://github.com/lovit/KR-WordRank',
    description="KR-WordRank: Korean Unsupervised Word/Keyword Extractor",
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=["numpy>=1.12.1"],
    keywords = ['Korean word keyword extraction'],
    packages=find_packages()
)