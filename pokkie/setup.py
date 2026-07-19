from setuptools import setup, find_packages

setup(
    name="pokkie",
    version="0.4.0",
    description="Blazingly fast AI terminal assistant + coding agent (Groq + NVIDIA NIM)",
    author="Pokkie",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "rich>=13.7.0",
        "prompt_toolkit>=3.0.43",
    ],
    extras_require={
        "automation": [
            "pyautogui>=0.9.54",
            "pillow>=10.0.0",
            'pygetwindow>=0.0.9; sys_platform == "win32"',
        ],
    },
    entry_points={
        "console_scripts": [
            "pokkie=pokkie.main:main",
        ],
    },
)
