from description import __version__, __author__
from setuptools import setup

readme = 'It extracts Korean words and keywords in documents without any linguistical knowloedge.'

setup(
   name="krwordrank",
   version=__version__,
   author=__author__,
   author_email='soy.lovit@gmail.com',
   url='https://github.com/lovit/KR-WordRank',
   description="KR-WordRank: Korean Unsupervised Word/Keyword Extractor",
   long_description=readme,
   install_requires=["numpy>=1.12.1"],
   keywords = ['Korean word keyword extraction'],
   packages=['krwordrank']
)