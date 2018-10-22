import setuptools

with open("README.md", "r") as readme:
    with open("requirements.txt", "r") as requirements:
        setuptools.setup(
            name='downmail',
            version='0.0.8',
            author="Nat Quayle Nelson",
            author_email="natquaylenelson@gmail.com",
            description="Antisocial Markdown email client.",
            long_description=readme.read(),
            long_description_content_type="text/markdown",
            url="https://github.com/NQNStudios/downmail",
            packages=setuptools.find_packages(),
            classifiers=(
                "Programming Language :: Python :: 3",
                "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
                "Operating System :: OS Independent",
            ),
            install_requires=requirements.readlines(),
            entry_points={
                'console_scripts': ['downmail = downmail.main:main']
            },
        )
