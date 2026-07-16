@echo off
REM Script de lancement rapide pour Windows
REM Placez ce fichier dans le même dossier que chambres_hotes_app.py

echo ==========================================
echo   🏨 Chambres d'Hôtes — Lancement
echo ==========================================
echo.

REM Vérifier que le script Python existe
if not exist "chambres_hotes_app.py" (
    echo ❌ Erreur : chambres_hotes_app.py non trouvé dans ce dossier.
    echo    Placez ce fichier .bat au même endroit que le script Python.
    pause
    exit /b 1
)

REM Vérifier que Python est installé
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Erreur : Python n'est pas installé ou pas dans le PATH.
    echo    Téléchargez Python : https://python.org/downloads/
    echo    ✅ Cochez "Add Python to PATH" pendant l'installation.
    pause
    exit /b 1
)

echo ✅ Python détecté.
echo 🚀 Lancement de l'application...
echo (Fermez la fenêtre Python pour arrêter)
echo.

python chambres_hotes_app.py

echo.
echo Application fermée.
pause
