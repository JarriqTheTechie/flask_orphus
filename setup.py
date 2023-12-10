from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="flask_orphus",
    version="0.1.1",
    author="Jarriq Rolle",
    author_email="jrolle@bnbbahamas.com",
    description="A package that extends the flask webframework in a very opinionated way.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/JarriqTheTechie/flask_orphus",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.9',
    install_requires=[
        'flask',
        "python-dotenv",
        "masonite-orm"
    ],
)