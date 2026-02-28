"""Setup script for FortiMonitor MCP Server."""

from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = [
        line.strip()
        for line in f
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="unofficial-fortimonitor-mcp-server",
    version="0.1.0",
    description="Unofficial community MCP server for FortiMonitor/Panopta v2 API integration",
    author="Gregori Jenkins",
    packages=find_packages(),
    package_dir={"": "."},
    python_requires=">=3.9",
    install_requires=[
        req for req in requirements
        if not any(dev in req.lower() for dev in ["pytest", "black", "flake8", "mypy"])
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "black>=23.12.0",
            "flake8>=6.1.0",
            "mypy>=1.7.0",
            "types-requests>=2.31.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "unofficial-fortimonitor-mcp=src.server:main",
        ]
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
