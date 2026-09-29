@echo off
REM ============================================================================
REM  Mirroring iPad -> PC Windows  --  MODE ACTUEL (iPadOS 16 a 26.x)
REM  Methode : captures d'ecran (app.py), ~15-20 images/seconde.
REM  Double-cliquer ce fichier. Il fait tout : admin, tunnel, montage, lancement.
REM ============================================================================
title Mirroring iPad (mode captures) - app.py
cd /d "%~dp0"

REM --- 1) Droits administrateur (le tunnel iOS 17+ l'exige) -------------------
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Demande des droits administrateur ^(necessaires pour le tunnel^)...
    powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

echo ================================================================
echo   Mirroring iPad  -^>  PC Windows     (mode captures d'ecran)
echo ================================================================
echo.

REM --- 2) Tunnel dans sa propre fenetre (a NE PAS fermer) ---------------------
echo [1/4] Demarrage du tunnel (laisser la fenetre "Tunnel" ouverte)...
start "iPad - Tunnel (NE PAS FERMER)" cmd /k python -m pymobiledevice3 remote tunneld

REM --- 3) Attendre que le tunnel detecte l'iPad ------------------------------
echo [2/4] Attente de la detection de l'iPad...
set /a _tries=0
:wait_tunnel
timeout /t 2 /nobreak >nul
python -c "import requests,sys; r=requests.get('http://127.0.0.1:49151',timeout=1); sys.exit(0 if r.ok and r.json() else 1)" >nul 2>&1
if %errorlevel%==0 goto tunnel_ok
set /a _tries+=1
if %_tries% lss 15 goto wait_tunnel
echo.
echo ERREUR : le tunnel n'a pas detecte l'iPad apres ~30s.
echo   - iPad branche, deverrouille, "Faire confiance" accepte ?
echo   - Mode developpeur active ?
echo   - Regarder la fenetre "Tunnel" pour le detail.
echo.
pause
exit /b 1
:tunnel_ok
echo       OK : iPad detecte.

REM --- 4) Monter l'image developpeur (ignore si deja montee) -----------------
echo [3/4] Montage de l'image developpeur (DDI)...
python -m pymobiledevice3 mounter auto-mount

REM --- 5) Lancer l'application de capture ------------------------------------
echo [4/4] Demarrage de l'affichage... (fermer avec q ou Echap)
echo.
python app.py

echo.
echo Termine. Tu peux fermer cette fenetre et la fenetre "Tunnel".
pause
