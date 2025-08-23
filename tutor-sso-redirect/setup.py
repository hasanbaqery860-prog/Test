import io
import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

with io.open(os.path.join(here, "README.md"), "rt", encoding="utf8") as f:
    readme = f.read()

about = {}
with io.open(
    os.path.join(here, "tutorssoredirect", "__about__.py"),
    "rt",
    encoding="utf-8",
) as f:
    exec(f.read(), about)

setup(
    name="tutor-sso-redirect",
    version=about["__version__"],
    url="https://github.com/yourusername/tutor-sso-redirect",
    project_urls={
        "Code": "https://github.com/yourusername/tutor-sso-redirect",
        "Issue tracker": "https://github.com/yourusername/tutor-sso-redirect/issues",
    },
    license="AGPLv3",
    author="Your Name",
    author_email="your.email@example.com",
    description="Tutor plugin to disable Open edX login/register and redirect to SSO",
    long_description=readme,
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=["tests*"]),
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=[
        "tutor>=18.0.0",
    ],
    extras_require={
        "dev": [
            "tutor[dev]>=18.0.0",
        ]
    },
    entry_points={
        "tutor.plugin.v1": [
            "sso-redirect = tutorssoredirect.plugin"
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)