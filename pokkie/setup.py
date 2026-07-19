from setuptools import setup, find_packages

setup(
    name="pokkie",
    version="0.2.0",
    description="Blazingly fast AI terminal assistant powered by Groq",
    author="Pokkie",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "rich>=13.7.0",
        "prompt_toolkit>=3.0.43",
        "pyautogui>=0.9.54",
        "pillow>=10.0.0",
        "pygetwindow>=0.0.9",
    ],
    entry_points={
        "console_scripts": [
            "pokkie=pokkie.main:main",
        ],
    },
)
