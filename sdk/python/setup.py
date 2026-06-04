"""
FastBlog API Python SDK
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="fastblog-sdk",
    version="1.0.0",
    author="FastBlog Team",
    author_email="support@fastblog.example.com",
    description="FastBlog API Python SDK - 同步和异步客户端",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/fastblog/fast_blog",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.14",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.31.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
    },
)
