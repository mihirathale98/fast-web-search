from setuptools import setup, find_packages

setup(
    name="fast-web-search",
    version="0.2.0",
    description="A fast web search and scraping package with proxy support, batching, polite scraping, and fault tolerance.",
    author="Your Name",
    packages=find_packages(),
    install_requires=[
        "requests==2.31.0",
        "beautifulsoup4==4.12.2",
        "aiohttp",
        "pydantic",
    ],
    python_requires=">=3.7",
)
