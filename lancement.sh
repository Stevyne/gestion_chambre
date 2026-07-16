#!/bin/bash
# Script de lancement rapide
# Usage : bash lancement.sh

clear
echo "========================================"
echo "  🏨 Chambres d'Hôtes — Lancement"
echo "========================================"
echo ""
echo "📁 Dossier actuel : $(pwd)"
echo "📄 Fichier source : chambres_hotes_app.py"
echo ""

# Vérifier Tkinter
python3 -c "import tkinter; print('✅ Tkinter détecté')" 2>/dev/null || {
    echo "❌ Tkinter manquant. Installez-le :"
    echo "   sudo apt install python3-tk   (Ubuntu/Debian)"
    exit 1
}

echo "🚀 Lancement de l'application (fermez la fenêtre pour arrêter)..."
echo ""
python3 chambres_hotes_app.py
