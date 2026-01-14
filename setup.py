"""Setup configuration for DockerMonitor."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
if requirements_file.exists():
    with open(requirements_file) as f:
        requirements = [
            line.strip()
            for line in f
            if line.strip() and not line.startswith("#")
        ]
else:
    requirements = []

setup(
    name="dockermonitor",
    version="0.1.0",
    description="Monitor Docker containers across multiple hosts via SSH jump host",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/dockermonitor",
    packages=find_packages(exclude=["tests", "tests.*"]),
    package_data={
        "src.tui": ["styles.css"],
    },
    include_package_data=True,
    install_requires=requirements,
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "dockermonitor=src.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Systems Administration",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="docker monitoring ssh containers devops tui",
    project_urls={
        "Documentation": "https://github.com/yourusername/dockermonitor/blob/main/README.md",
        "Source": "https://github.com/yourusername/dockermonitor",
        "Tracker": "https://github.com/yourusername/dockermonitor/issues",
    },
)
