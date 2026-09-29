@echo off
REM ============================================================================
REM  _env.bat  --  environnement Python local au projet (.venv)
REM  Appele par les lanceurs : cree .venv la 1re fois et y installe les
REM  dependances (rien n'est installe dans le Python global de l'ordi).
REM  Reinstalle automatiquement si requirements.txt change.
REM ============================================================================
if not exist ".venv\Scripts\python.exe" (
    echo Creation de l'environnement Python local .venv ^(une seule fois^)...
    python -m venv .venv
    if errorlevel 1 (
        echo ERREUR : Python introuvable. Installer Python 3 avec "Add Python to PATH".
        exit /b 1
    )
)

fc /b requirements.txt .venv\requirements.installed >nul 2>&1
if errorlevel 1 (
    echo Installation des dependances dans .venv ^(peut prendre une minute^)...
    .venv\Scripts\python.exe -m pip install --disable-pip-version-check -q -r requirements.txt
    if errorlevel 1 (
        echo ERREUR : installation des dependances echouee.
        exit /b 1
    )
    copy /y requirements.txt .venv\requirements.installed >nul
)
exit /b 0
