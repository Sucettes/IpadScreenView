@echo off
REM ============================================================================
REM  mirror.bat  --  LANCEUR INTELLIGENT (detecte la version, choisit la methode)
REM
REM   - iPadOS < 27  -> mode captures (app.py), ~15-20 fps
REM   - iPadOS 27+   -> mode video HEVC (serve-web + navigateur), 30-60 fps
REM
REM  Double-cliquer ce fichier : il fait TOUT (admin, detection, tunnel,
REM  montage, lancement de la bonne methode). Aucune commande a retenir.
REM ============================================================================
title Mirroring iPad (lanceur automatique)
cd /d "%~dp0"

REM --- 1) Droits administrateur (le tunnel iOS 17+ l'exige) -------------------
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Demande des droits administrateur ^(necessaires pour le tunnel^)...
    powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

echo ================================================================
echo   Mirroring iPad  -^>  PC Windows        (lanceur automatique)
echo ================================================================
echo.

REM --- 2) Detecter la version d'iPadOS via usbmux (pas besoin du tunnel) ------
echo [1/5] Detection de la version de l'iPad...
set "VER="
set "MAJOR="
for /f "usebackq delims=" %%v in (`python -c "import asyncio;from pymobiledevice3.lockdown import create_using_usbmux;print(asyncio.run(create_using_usbmux()).product_version)" 2^>nul`) do set "VER=%%v"

if not defined VER (
    echo.
    echo ERREUR : impossible de lire la version de l'iPad.
    echo   - iPad branche en USB-C, deverrouille ?
    echo   - "Faire confiance a cet ordinateur" accepte ?
    echo   - Pilotes Apple installes ? Tester :  python -m pymobiledevice3 usbmux list
    echo.
    pause
    exit /b 1
)
for /f "delims=." %%a in ("%VER%") do set "MAJOR=%%a"
echo       iPad detecte : iPadOS %VER%  (version majeure %MAJOR%)

REM --- 3) Tunnel dans sa propre fenetre (a NE PAS fermer) ---------------------
echo [2/5] Demarrage du tunnel (laisser la fenetre "Tunnel" ouverte)...
start "iPad - Tunnel (NE PAS FERMER)" cmd /k python -m pymobiledevice3 remote tunneld

REM --- 4) Attendre que le tunnel detecte l'iPad ------------------------------
echo [3/5] Attente de la detection de l'iPad par le tunnel...
set /a _tries=0
:wait_tunnel
timeout /t 2 /nobreak >nul
python -c "import requests,sys; r=requests.get('http://127.0.0.1:49151',timeout=1); sys.exit(0 if r.ok and r.json() else 1)" >nul 2>&1
if %errorlevel%==0 goto tunnel_ok
set /a _tries+=1
if %_tries% lss 15 goto wait_tunnel
echo.
echo ERREUR : le tunnel n'a pas detecte l'iPad apres ~30s.
echo   Regarder la fenetre "Tunnel" pour le detail (mode developpeur active ?).
echo.
pause
exit /b 1
:tunnel_ok
echo       OK : tunnel pret.

REM --- 5) Monter l'image developpeur (ignore si deja montee) -----------------
echo [4/5] Montage de l'image developpeur (DDI)...
python -m pymobiledevice3 mounter auto-mount

REM --- 6) Choisir la methode selon la version --------------------------------
if %MAJOR% geq 27 (
    echo [5/5] iPadOS 27+ : mode video HEVC fluide.
    echo       Ouverture du navigateur sur http://127.0.0.1:8080/
    echo       Page noire ? Installer "HEVC Video Extensions" ^(Microsoft Store^).
    echo.
    start "" http://127.0.0.1:8080/
    python -m pymobiledevice3 developer core-device display serve-web --bind 127.0.0.1
) else (
    echo [5/5] iPadOS %MAJOR% : mode captures d'ecran ^(~15-20 fps^).
    echo       Quitter la fenetre video : touche q ou Echap.
    echo.
    python app.py
)

echo.
echo Termine. Tu peux fermer cette fenetre et la fenetre "Tunnel".
pause
