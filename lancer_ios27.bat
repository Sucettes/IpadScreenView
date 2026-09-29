@echo off
REM ============================================================================
REM  Mirroring iPad -> PC Windows  --  MODE iPadOS 27+ (flux video HEVC fluide)
REM  A UTILISER UNIQUEMENT quand l'iPad est sur iPadOS 27 ou plus.
REM  Methode : serveur de mirroring integre a pymobiledevice3 + navigateur.
REM  Decodage video par le navigateur (Edge/Chrome) : 30 a 60 images/seconde.
REM  Double-cliquer ce fichier. Il fait tout : admin, tunnel, montage, navigateur.
REM ============================================================================
title Mirroring iPad (iPadOS 27) - serve-web HEVC
cd /d "%~dp0"

REM --- 1) Droits administrateur (le tunnel l'exige) --------------------------
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Demande des droits administrateur ^(necessaires pour le tunnel^)...
    powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

echo ================================================================
echo   Mirroring iPad  -^>  PC Windows     (mode iPadOS 27 : video HEVC)
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

REM --- 5) Navigateur + serveur de mirroring video ---------------------------
echo [4/4] Ouverture du navigateur et demarrage du flux video HEVC...
start "" http://127.0.0.1:8080/
echo.
echo Le flux tourne. Pour arreter : Ctrl-C ici, puis fermer la fenetre "Tunnel".
echo Page noire ? Installer "HEVC Video Extensions" depuis le Microsoft Store.
echo.
REM --bind 127.0.0.1 = accessible seulement depuis ce PC (les endpoints
REM tactile/clavier/boutons n'ont aucune authentification).
python -m pymobiledevice3 developer core-device display serve-web --bind 127.0.0.1

echo.
echo Termine. Tu peux fermer cette fenetre et la fenetre "Tunnel".
pause
