import setuptools

with open("README.md", "r") as fh:

    setuptools.setup(
        name='downmail',
        version='0.0.1',
        author="Nat Quayle Nelson",
        author_email="natquaylenelson@gmail.com",
        description="Antisocial Markdown email client.",
        long_description=fh.read(),
        long_description_content_type="text/markdown",
        url="https://github.com/NQNStudios/downmail",
        packages=setuptools.find_packages(),
        classifiers=(
            "Programming Language :: Python :: 2",
            "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
            "Operating System :: OS Independent",
        ),
    )
