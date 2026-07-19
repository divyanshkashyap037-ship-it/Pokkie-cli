@echo off
where py >nul 2>nul
if errorlevel 1 (
    python -m pokkie.main %*
) else (
    py -3 -m pokkie.main %*
)
