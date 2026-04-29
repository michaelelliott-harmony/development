from setuptools import setup, find_packages

setup(
    name="harmony-pipeline",
    version="0.1.0",
    description="Harmony Pillar 2 — Data Ingestion Pipeline",
    packages=find_packages(),
    python_requires=">=3.11",
    install_requires=[
        "click>=8.1.7,<9",
        "pyyaml>=6.0.1,<7",
        "httpx[http2]>=0.27.0,<1",
        "fiona>=1.9.5,<2",
        "shapely>=2.0.4,<3",
        "pyproj>=3.6.1,<4",
        "geopandas>=0.14.3,<1",
        "overpy>=0.7,<1",
        "pydantic>=2.7.0,<3",
    ],
    extras_require={
        "dev": [
            "pytest>=8.2.0,<9",
            "pytest-cov>=5.0.0,<6",
        ]
    },
    entry_points={
        "console_scripts": [
            "harmony-ingest=harmony.pipelines.cli:cli",
        ]
    },
)
