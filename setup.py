"""
WishlistOps setup configuration.
"""

from setuptools import setup, find_packages

setup(
    name="wishlistops",
    version="0.1.0",
    description="Automated Steam marketing for indie game developers",
    author="WishlistOps",
    python_requires=">=3.11",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31.0",
        "aiohttp>=3.9.0",
        "httpx>=0.25.0",
        "pydantic>=2.5.0",
        "pydantic-settings>=2.1.0",
        "GitPython>=3.1.40",
        "Pillow>=10.0.0",
        "python-dotenv>=1.0.0",
        "tomli>=2.0.1",
        "pyyaml>=6.0.1",
        "google-generativeai>=0.3.0",
        "discord-webhook>=1.3.0",
        "discord.py>=2.3.0",
        "python-dateutil>=2.8.2",
        "pytz>=2023.3",
        "tenacity>=8.2.3",
        "ratelimit>=2.2.1",
        "structlog>=23.2.0",
        "python-json-logger>=2.0.7",
        "orjson>=3.9.0",
        "aiohttp-session>=2.12.0",
        "cryptography>=41.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.12.0",
            "mypy>=1.7.0",
            "types-requests>=2.31.0",
            "types-PyYAML>=6.0.12",
            "pylint>=3.0.0",
            "black>=23.11.0",
            "isort>=5.12.0",
            "flake8>=6.1.0",
        ],
        "web": [
            "aiohttp>=3.9.0",
            "aiohttp-cors>=0.7.0",
            "aiohttp-session>=2.12.0",
            "cryptography>=41.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "wishlistops=wishlistops.__main__:main_cli",
            "wishlistops-web=wishlistops.__main__:launch_web_interface",
        ],
    },
    package_data={
        "wishlistops": ["../dashboard/*.*", "../dashboard/**/*.*"],
    },
    include_package_data=True,
)
