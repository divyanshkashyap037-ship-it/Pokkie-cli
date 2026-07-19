@echo off
echo Installing Pokkie v0.4...
python -m pip install --upgrade pip
python -m pip install --upgrade ".[automation]"
echo.
echo Done. Open a new terminal and run:  pokkie
pause
