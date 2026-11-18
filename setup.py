from setuptools import setup, find_packages

setup(
    name="crossborder-agent-toolkit",
    version="1.0.0",
    description="Cross-border ecommerce agent toolkit for pricing, listing quality, and ad funnel optimization",
    packages=find_packages(),
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "crossborder-toolkit=crossborder_toolkit.cli:main",
        ],
    },
)
