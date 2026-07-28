"""Setup script for yi-jing-agent."""
from setuptools import setup, find_packages

setup(
    name="yi-jing-agent",
    version="0.1.0",
    description="䷀ I Ching Six Lines AI Agent Framework",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="yayasasapig",
    license="MIT",
    python_requires=">=3.10",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    keywords="i-ching yi-jing ai-agent lifecycle fault-tolerance 六爻 易經",
    project_urls={
        "Homepage": "https://github.com/yayasasapig/yi-jing-agent",
        "Repository": "https://github.com/yayasasapig/yi-jing-agent",
        "Issues": "https://github.com/yayasasapig/yi-jing-agent/issues",
    },
)
