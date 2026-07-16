#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Application de gestion des chambres d'hôtes
Stockage : en mémoire (pas de base de données)
Interface : Tkinter (multi-plateforme)
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime, timedelta
from collections import defaultdict

# ============================================================
# DONNÉES EN MÉMOIRE
# ============================================================

CHAMBRES = [
    {"numero": 101, "nom": "Chambre du Jardin", "type": "Double", "prix_nuit": 85},
    {"numero": 102, "nom": "Chambre de la Mer", "type": "Double", "prix_nuit": 95},
    {"numero": 103, "nom": "Suite Royale", "type": "Suite", "prix_nuit": 140},
    {"numero": 104, "nom": "Chambre des Oliviers", "type": "Simple", "prix_nuit": 65},
    {"numero": 105, "nom": "Chambre du Lac", "type": "Double", "prix_nuit": 90},
]

RESERVATIONS = [
    {"id": 1, "nom_client": "Marie Dupont", "chambre_num": 101, "date_debut": "2026-07-10", "date_fin": "2026-07-15", "montant_paye": 200, "montant_total": 425},
    {"id": 2, "nom_client": "Jean Lefebvre", "chambre_num": 102, "date_debut": "2026-07-14", "date_fin": "2026-07-20", "montant_paye": 300, "montant_total": 570},
    {"id": 3, "nom_client": "Claire Martin", "chambre_num": 103, "date_debut": "2026-07-18", "date_fin": "2026-07-25", "montant_paye": 700, "montant_total": 980},
]

# On calcule le prochain ID
next_id = max([r["id"] for r in RESERVATIONS], default=0) + 1

# ============================================================
# CLASSE PRINCIPALE
# ============================================================

class AppChambresHotes:
    def __init__(self, root):
        self.root = root
        self.root.title("🏨 Gestion des Chambres d'Hôtes")
        self.root.geometry("1100x720")
        self.root.minsize(900, 600)
        self.root.configure(bg="#f5f0e6")

        # Style personnalisé
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background="#f5f0e6", borderwidth=0)
        style.configure("TNotebook.Tab", font=("Segoe UI", 11, "bold"), padding=[15, 8], background="#e8dcc8", foreground="#4a3c2a")
        style.map("TNotebook.Tab", background=[("selected", "#fff8e7"), ("active", "#f0e6cc")])
        style.configure("TFrame", background="#f5f0e6")
        style.configure("TLabelframe", background="#fff8e7", relief="solid", borderwidth=1)
        style.configure("TLabelframe.Label", background="#fff8e7", font=("Segoe UI", 11, "bold"), foreground="#5a4a32")

        # Variables
        self.date_aujourd_hui = datetime.now().strftime("%Y-%m-%d")

        # Menu
        self._creer_menu()

        # Notebook (onglets)
        self.notebook = ttk.Notebook(root, style="TNotebook")
        self.notebook.pack(fill="both", expand=True, padx=15, pady=(10, 15))

        # Création des onglets
        self.onglet_accueil = self._creer_accueil()
        self.onglet_chambres = self._creer_chambres()
        self.onglet_reservations = self._creer_reservations()
        self.onglet_calendrier = self._creer_calendrier()
        self.onglet_historique = self._creer_historique()
        self.onglet_paiements = self._creer_paiements()

        self.notebook.add(self.onglet_accueil, text="🏠 Accueil")
        self.notebook.add(self.onglet_chambres, text="🛏️ Chambres")
        self.notebook.add(self.onglet_reservations, text="📅 Réservations")
        self.notebook.add(self.onglet_calendrier, text="📊 Calendrier")
        self.notebook.add(self.onglet_historique, text="📜 Historique")
        self.notebook.add(self.onglet_paiements, text="💰 Paiements")

        # Barre de statut
        self.status = tk.Label(root, text="Prêt • Données en mémoire • Aucune base de données requise", bg="#5a4a32", fg="#fff8e7", font=("Segoe UI", 9), pady=6)
        self.status.pack(fill="x", side="bottom")

        # Mise à jour initiale
        self._actualiser_accueil()
        self._actualiser_toutes_les_vues()

    # ============================================================
    # MENU
    # ============================================================
    def _creer_menu(self):
        menubar = tk.Menu(self.root, bg="#5a4a32", fg="#fff8e7", font=("Segoe UI", 10))
        self.root.config(menu=menubar)

        menu_fichier = tk.Menu(menubar, tearoff=0, bg="#5a4a32", fg="#fff8e7")
        menubar.add_cascade(label="Fichier", menu=menu_fichier)
        menu_fichier.add_command(label="Réinitialiser les données", command=self._reinitialiser_donnees)
        menu_fichier.add_separator()
        menu_fichier.add_command(label="Quitter", command=self.root.quit)

        menu_aide = tk.Menu(menubar, tearoff=0, bg="#5a4a32", fg="#fff8e7")
        menubar.add_cascade(label="Aide", menu=menu_aide)
        menu_aide.add_command(label="À propos", command=self._apropos)

    # ============================================================
    # ACCUEIL (TABLEAU DE BORD)
    # ============================================================
    def _creer_accueil(self):
        frame = tk.Frame(self.notebook, bg="#fff8e7")
        frame.pack(fill="both", expand=True)

        # Titre
        tk.Label(frame, text="Tableau de Bord", font=("Segoe UI", 22, "bold"), bg="#fff8e7", fg="#3a2a1a").pack(pady=(15, 25))

        # Cartes statistiques (4 colonnes)
        cartes = tk.Frame(frame, bg="#fff8e7")
        cartes.pack(pady=10)

        self.stat_chambres_libres = self._carte_stat(cartes, "Chambres disponibles", "0", "#6aaa64", 0)
        self.stat_reservations_actives = self._carte_stat(cartes, "Réservations actives", "0", "#4a90e2", 1)
        self.stat_total_soldes = self._carte_stat(cartes, "Total des soldes dus", "0 €", "#e67e22", 2)
        self.stat_client_aujourdhui = self._carte_stat(cartes, "Client du jour", "—", "#9b59b6", 3)

        # Section réservations du jour / prochaines
        section = tk.LabelFrame(frame, text="Réservations du jour et à venir", bg="#fff8e7", font=("Segoe UI", 12, "bold"), fg="#5a4a32")
        section.pack(fill="both", expand=True, padx=20, pady=20)

        self.table_accueil = ttk.Treeview(section, columns=("nom", "chambre", "dates", "solde"), show="headings", height=8)
        for col in ("nom", "chambre", "dates", "solde"):
            self.table_accueil.heading(col, text=col.capitalize())
            self.table_accueil.column(col, width=200, anchor="center")
        self.table_accueil.pack(fill="both", expand=True, padx=10, pady=10)

        # Section dernières réservations
        section2 = tk.LabelFrame(frame, text="Dernières réservations enregistrées", bg="#fff8e7", font=("Segoe UI", 11, "bold"), fg="#5a4a32")
        section2.pack(fill="x", padx=20, pady=10)
        self.table_dernieres = ttk.Treeview(section2, columns=("id", "nom", "chambre", "debut", "fin"), show="headings", height=5)
        for col in ("id", "nom", "chambre", "debut", "fin"):
            self.table_dernieres.heading(col, text=col.capitalize())
            self.table_dernieres.column(col, width=130, anchor="center")
        self.table_dernieres.pack(fill="x", padx=10, pady=10)

        return frame

    def _carte_stat(self, parent, titre, valeur, couleur, colonne):
        carte = tk.Frame(parent, bg=couleur, relief="raised", bd=2)
        carte.grid(row=0, column=colonne, padx=15, pady=10, sticky="nsew")
        parent.grid_columnconfigure(colonne, weight=1)
        tk.Label(carte, text=titre, bg=couleur, fg="#ffffff", font=("Segoe UI", 10, "bold")).pack(pady=(8, 2))
        label_val = tk.Label(carte, text=valeur, bg=couleur, fg="#ffffff", font=("Segoe UI", 16, "bold"))
        label_val.pack(pady=(2, 8))
        # On retourne la référence au label de valeur pour le mettre à jour
        carte.label_val = label_val
        return carte

    def _actualiser_accueil(self):
        # Chambres disponibles (celles qui ne sont pas réservées aujourd'hui)
        aujourdhui = self.date_aujourd_hui
        chambres_occupees_aujourdhui = set()
        for r in RESERVATIONS:
            if r["date_debut"] <= aujourdhui <= r["date_fin"]:
                chambres_occupees_aujourdhui.add(r["chambre_num"])
        libres = len(CHAMBRES) - len(chambres_occupees_aujourdhui)

        # Réservations actives (en cours ou à venir)
        aujourdhui_dt = datetime.strptime(aujourdhui, "%Y-%m-%d")
        actives = [r for r in RESERVATIONS if datetime.strptime(r["date_fin"], "%Y-%m-%d") >= aujourdhui_dt]

        # Solde total
        total_soldes = sum(max(0, r["montant_total"] - r["montant_paye"]) for r in RESERVATIONS)

        # Mise à jour des cartes
        self.stat_chambres_libres.label_val.config(text=str(libres))
        self.stat_reservations_actives.label_val.config(text=str(len(actives)))
        self.stat_total_soldes.label_val.config(text=f"{total_soldes:,} €".replace(",", " "))

        # Client du jour
        clients_aujourdhui = [r["nom_client"] for r in RESERVATIONS if r["date_debut"] <= aujourdhui <= r["date_fin"]]
        self.stat_client_aujourdhui.label_val.config(text=clients_aujourdhui[0] if clients_aujourdhui else "—")

        # Table accueil
        for item in self.table_accueil.get_children():
            self.table_accueil.delete(item)
        aujourdhui_dt = datetime.strptime(aujourdhui, "%Y-%m-%d")
        for r in sorted(RESERVATIONS, key=lambda x: x["date_debut"]):
            solde = max(0, r["montant_total"] - r["montant_paye"])
            self.table_accueil.insert("", "end", values=(r["nom_client"], f"Chambre {r['chambre_num']}", f"{r['date_debut']} → {r['date_fin']}", f"{solde:,} €".replace(",", " ")))

        # Table dernières réservations
        for item in self.table_dernieres.get_children():
            self.table_dernieres.delete(item)
        for r in sorted(RESERVATIONS, key=lambda x: x["date_debut"], reverse=True)[:5]:
            self.table_dernieres.insert("", "end", values=(r["id"], r["nom_client"], r["chambre_num"], r["date_debut"], r["date_fin"]))

    # ============================================================
    # CHAMBRES
    # ============================================================
    def _creer_chambres(self):
        frame = tk.Frame(self.notebook, bg="#fff8e7")
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="État des Chambres", font=("Segoe UI", 20, "bold"), bg="#fff8e7", fg="#3a2a1a").pack(pady=(15, 20))

        # Liste des chambres
        liste_frame = tk.Frame(frame, bg="#fff8e7")
        liste_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.table_chambres = ttk.Treeview(liste_frame, columns=("num", "nom", "type", "prix", "statut"), show="headings", height=10)
        for col in ("num", "nom", "type", "prix", "statut"):
            self.table_chambres.heading(col, text=col.capitalize())
            self.table_chambres.column(col, width=160, anchor="center")
        self.table_chambres.pack(side="left", fill="both", expand=True)

        # Légende / Détails
        details = tk.LabelFrame(frame, text="Informations", bg="#fff8e7", font=("Segoe UI", 10, "bold"), fg="#5a4a32")
        details.pack(fill="x", padx=20, pady=10)
        tk.Label(details, text="• Vert  = Chambre disponible\n• Rouge = Chambre occupée aujourd'hui", bg="#fff8e7", fg="#4a3c2a", font=("Segoe UI", 9), justify="left").pack(anchor="w", padx=10, pady=8)

        return frame

    def _actualiser_chambres(self):
        for item in self.table_chambres.get_children():
            self.table_chambres.delete(item)
        aujourdhui = self.date_aujourd_hui
        chambres_occupees = set()
        for r in RESERVATIONS:
            if r["date_debut"] <= aujourdhui <= r["date_fin"]:
                chambres_occupees.add(r["chambre_num"])
        for ch in CHAMBRES:
            statut = "Occupée" if ch["numero"] in chambres_occupees else "Disponible"
            tag = "occupee" if ch["numero"] in chambres_occupees else "dispo"
            self.table_chambres.insert("", "end", values=(ch["numero"], ch["nom"], ch["type"], f"{ch['prix_nuit']} €", statut), tags=(tag,))
        self.table_chambres.tag_configure("occupee", background="#ffc7c7", foreground="#7a1a1a")
        self.table_chambres.tag_configure("dispo", background="#c7ffc7", foreground="#1a7a1a")

    # ============================================================
    # RÉSERVATIONS (FORMULAIRE)
    # ============================================================
    def _creer_reservations(self):
        global next_id
        frame = tk.Frame(self.notebook, bg="#fff8e7")
        frame.pack(fill="both", expand=True)

        # Titre
        tk.Label(frame, text="Nouvelle Réservation", font=("Segoe UI", 20, "bold"), bg="#fff8e7", fg="#3a2a1a").pack(pady=(15, 25))

        # Formulaire
        form = tk.LabelFrame(frame, text="Informations de réservation", bg="#fff8e7", font=("Segoe UI", 12, "bold"), fg="#5a4a32")
        form.pack(padx=30, pady=15, fill="x")

        # Grille
        grid = tk.Frame(form, bg="#fff8e7")
        grid.pack(padx=15, pady=15)

        tk.Label(grid, text="Nom du client :", bg="#fff8e7", font=("Segoe UI", 10)).grid(row=0, column=0, sticky="e", pady=6)
        self.entry_nom = tk.Entry(grid, font=("Segoe UI", 10), width=30)
        self.entry_nom.grid(row=0, column=1, sticky="w", pady=6)
        self.entry_nom.insert(0, "Jean Dupont")

        tk.Label(grid, text="Chambre :", bg="#fff8e7", font=("Segoe UI", 10)).grid(row=1, column=0, sticky="e", pady=6)
        self.combo_chambre = ttk.Combobox(grid, values=[f"Chambre {c['numero']} - {c['nom']}" for c in CHAMBRES], width=28, state="readonly")
        self.combo_chambre.grid(row=1, column=1, sticky="w", pady=6)
        self.combo_chambre.current(0)

        tk.Label(grid, text="Date début (AAAA-MM-JJ) :", bg="#fff8e7", font=("Segoe UI", 10)).grid(row=2, column=0, sticky="e", pady=6)
        self.entry_debut = tk.Entry(grid, font=("Segoe UI", 10), width=20)
        self.entry_debut.grid(row=2, column=1, sticky="w", pady=6)
        self.entry_debut.insert(0, datetime.now().strftime("%Y-%m-%d"))

        tk.Label(grid, text="Date fin (AAAA-MM-JJ) :", bg="#fff8e7", font=("Segoe UI", 10)).grid(row=3, column=0, sticky="e", pady=6)
        self.entry_fin = tk.Entry(grid, font=("Segoe UI", 10), width=20)
        self.entry_fin.grid(row=3, column=1, sticky="w", pady=6)
        self.entry_fin.insert(0, (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"))

        tk.Label(grid, text="Montant total (€) :", bg="#fff8e7", font=("Segoe UI", 10)).grid(row=4, column=0, sticky="e", pady=6)
        self.entry_total = tk.Entry(grid, font=("Segoe UI", 10), width=20)
        self.entry_total.grid(row=4, column=1, sticky="w", pady=6)
        self.entry_total.insert(0, "300")

        tk.Label(grid, text="Montant payé (€) :", bg="#fff8e7", font=("Segoe UI", 10)).grid(row=5, column=0, sticky="e", pady=6)
        self.entry_paye = tk.Entry(grid, font=("Segoe UI", 10), width=20)
        self.entry_paye.grid(row=5, column=1, sticky="w", pady=6)
        self.entry_paye.insert(0, "0")

        # Bouton
        btn_frame = tk.Frame(form, bg="#fff8e7")
        btn_frame.pack(pady=15)
        btn_ajouter = tk.Button(btn_frame, text="✅ Enregistrer la réservation", command=self._ajouter_reservation, bg="#6aaa64", fg="#ffffff", font=("Segoe UI", 12, "bold"), padx=20, pady=8, relief="raised", bd=2)
        btn_ajouter.pack()

        # Tableau des réservations en cours
        section_table = tk.LabelFrame(frame, text="Réservations enregistrées", bg="#fff8e7", font=("Segoe UI", 12, "bold"), fg="#5a4a32")
        section_table.pack(fill="both", expand=True, padx=30, pady=15)

        self.table_reservations = ttk.Treeview(section_table, columns=("id", "nom", "chambre", "debut", "fin", "total", "paye", "solde"), show="headings", height=8)
        for col in ("id", "nom", "chambre", "debut", "fin", "total", "paye", "solde"):
            self.table_reservations.heading(col, text=col.capitalize())
            self.table_reservations.column(col, width=110, anchor="center")
        self.table_reservations.pack(fill="both", expand=True, padx=10, pady=10)

        return frame

    def _ajouter_reservation(self):
        global next_id
        nom = self.entry_nom.get().strip()
        chambre_str = self.combo_chambre.get()
        debut = self.entry_debut.get().strip()
        fin = self.entry_fin.get().strip()
        try:
            montant_total = float(self.entry_total.get().strip())
            montant_paye = float(self.entry_paye.get().strip())
        except ValueError:
            messagebox.showerror("Erreur", "Le montant total et le montant payé doivent être des nombres.")
            return

        if not nom:
            messagebox.showerror("Erreur", "Veuillez saisir le nom du client.")
            return
        if not chambre_str:
            messagebox.showerror("Erreur", "Veuillez sélectionner une chambre.")
            return
        # Extraire le numéro de chambre
        try:
            chambre_num = int(chambre_str.split()[1])
        except (IndexError, ValueError):
            messagebox.showerror("Erreur", "Chambre non reconnue.")
            return

        # Vérifier format date basique
        try:
            datetime.strptime(debut, "%Y-%m-%d")
            datetime.strptime(fin, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Erreur", "Les dates doivent être au format AAAA-MM-JJ.")
            return

        # Vérifier que le montant payé ne dépasse pas le total
        if montant_paye > montant_total:
            messagebox.showerror("Erreur", "Le montant payé ne peut pas dépasser le montant total.")
            return

        nouvelle_reservation = {
            "id": next_id,
            "nom_client": nom,
            "chambre_num": chambre_num,
            "date_debut": debut,
            "date_fin": fin,
            "montant_total": montant_total,
            "montant_paye": montant_paye
        }
        RESERVATIONS.append(nouvelle_reservation)
        next_id += 1

        messagebox.showinfo("Succès", f"Réservation enregistrée pour {nom} (Chambre {chambre_num}).")
        self._actualiser_toutes_les_vues()

    # ============================================================
    # CALENDRIER
    # ============================================================
    def _creer_calendrier(self):
        frame = tk.Frame(self.notebook, bg="#fff8e7")
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="Calendrier des Réservations", font=("Segoe UI", 20, "bold"), bg="#fff8e7", fg="#3a2a1a").pack(pady=(15, 25))

        # Sélection du mois
        controles = tk.Frame(frame, bg="#fff8e7")
        controles.pack(pady=5)

        self.mois_actuel = datetime.now().strftime("%Y-%m")

        btn_prec = tk.Button(controles, text="◀ Mois précédent", command=self._mois_precedent, bg="#e8dcc8", fg="#5a4a32", font=("Segoe UI", 9, "bold"))
        btn_prec.pack(side="left", padx=10)

        self.label_mois = tk.Label(controles, text=self.mois_actuel, bg="#fff8e7", fg="#3a2a1a", font=("Segoe UI", 14, "bold"), width=15)
        self.label_mois.pack(side="left", padx=20)

        btn_suiv = tk.Button(controles, text="Mois suivant ▶", command=self._mois_suivant, bg="#e8dcc8", fg="#5a4a32", font=("Segoe UI", 9, "bold"))
        btn_suiv.pack(side="left", padx=10)

        # Calendrier visuel
        calendrier_frame = tk.Frame(frame, bg="#fff8e7")
        calendrier_frame.pack(padx=20, pady=15, fill="both", expand=True)

        self.cells = {}
        for i in range(7):
            calendrier_frame.grid_columnconfigure(i, weight=1)
        for i in range(7):
            calendrier_frame.grid_rowconfigure(i, weight=1)

        jours_semaine = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
        for i, jour in enumerate(jours_semaine):
            tk.Label(calendrier_frame, text=jour, bg="#5a4a32", fg="#fff8e7", font=("Segoe UI", 10, "bold"), relief="raised", bd=1).grid(row=0, column=i, sticky="nsew", padx=2, pady=2)

        for i in range(6):
            for j in range(7):
                cell = tk.Label(calendrier_frame, text="", bg="#fff8e7", relief="sunken", bd=1, font=("Segoe UI", 9))
                cell.grid(row=i+1, column=j, sticky="nsew", padx=2, pady=2)
                self.cells[(i+1, j)] = cell

        self._afficher_mois()

        # Légende
        legende = tk.Frame(frame, bg="#fff8e7")
        legende.pack(pady=10)
        tk.Label(legende, text="● Disponible", bg="#fff8e7", fg="#6aaa64", font=("Segoe UI", 10, "bold")).pack(side="left", padx=15)
        tk.Label(legende, text="● Réservé", bg="#fff8e7", fg="#e67e22", font=("Segoe UI", 10, "bold")).pack(side="left", padx=15)
        tk.Label(legende, text="● Occupé (aujourd'hui)", bg="#fff8e7", fg="#c0392b", font=("Segoe UI", 10, "bold")).pack(side="left", padx=15)

        return frame

    def _mois_precedent(self):
        annee, mois = map(int, self.mois_actuel.split("-"))
        mois -= 1
        if mois == 0:
            mois = 12
            annee -= 1
        self.mois_actuel = f"{annee}-{mois:02d}"
        self.label_mois.config(text=self.mois_actuel)
        self._afficher_mois()

    def _mois_suivant(self):
        annee, mois = map(int, self.mois_actuel.split("-"))
        mois += 1
        if mois == 13:
            mois = 1
            annee += 1
        self.mois_actuel = f"{annee}-{mois:02d}"
        self.label_mois.config(text=self.mois_actuel)
        self._afficher_mois()

    def _afficher_mois(self):
        annee, mois = map(int, self.mois_actuel.split("-"))
        premier_jour = datetime(annee, mois, 1)
        # Jour de la semaine (lundi = 0)
        jour_semaine = premier_jour.weekday()
        # Nombre de jours dans le mois
        if mois == 12:
            dernier_jour_mois = datetime(annee + 1, 1, 1) - timedelta(days=1)
        else:
            dernier_jour_mois = datetime(annee, mois + 1, 1) - timedelta(days=1)
        nb_jours = dernier_jour_mois.day

        # Nettoyer
        for cell in self.cells.values():
            cell.config(text="", bg="#fff8e7", fg="#3a2a1a")

        aujourdhui_str = datetime.now().strftime("%Y-%m-%d")

        for jour in range(1, nb_jours + 1):
            date_str = f"{annee}-{mois:02d}-{jour:02d}"
            # Déterminer la cellule (ligne, colonne)
            # La première ligne est le 1er du mois
            # On commence après le header (row 1+)
            index_cell = jour + jour_semaine - 1
            row = index_cell // 7 + 1
            col = index_cell % 7

            # Vérifier réservations
            chambres_reservees = set()
            chambres_occupees_aujourdhui = set()
            for r in RESERVATIONS:
                if r["date_debut"] <= date_str <= r["date_fin"]:
                    chambres_reservees.add(r["chambre_num"])
                if r["date_debut"] <= aujourdhui_str <= r["date_fin"] and date_str == aujourdhui_str:
                    chambres_occupees_aujourdhui.add(r["chambre_num"])

            # Couleurs
            if date_str == aujourdhui_str:
                couleur = "#ff9999"
                texte = f"{jour}\n(AUJ.)\n"
            elif chambres_reservees:
                couleur = "#ffe0b2"
                texte = f"{jour}\n"
            else:
                couleur = "#e8f5e9"
                texte = f"{jour}\n"

            # Ajouter le nom des réservations
            noms = []
            for r in RESERVATIONS:
                if r["date_debut"] <= date_str <= r["date_fin"]:
                    noms.append(f"{r['nom_client']} (Ch.{r['chambre_num']})")
            texte += "\n".join(noms[:3])
            if len(noms) > 3:
                texte += f"\n+{len(noms)-3} autre(s)"

            cell = self.cells.get((row, col))
            if cell:
                cell.config(text=texte, bg=couleur, fg="#3a2a1a", font=("Segoe UI", 8))

    # ============================================================
    # HISTORIQUE
    # ============================================================
    def _creer_historique(self):
        frame = tk.Frame(self.notebook, bg="#fff8e7")
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="Historique des Réservations", font=("Segoe UI", 20, "bold"), bg="#fff8e7", fg="#3a2a1a").pack(pady=(15, 25))

        # Filtres
        filtres = tk.Frame(frame, bg="#fff8e7")
        filtres.pack(pady=5)
        tk.Label(filtres, text="Client :", bg="#fff8e7", font=("Segoe UI", 10)).pack(side="left", padx=5)
        self.entry_filtre_client = tk.Entry(filtres, width=20)
        self.entry_filtre_client.pack(side="left", padx=5)
        tk.Label(filtres, text="Chambre :", bg="#fff8e7", font=("Segoe UI", 10)).pack(side="left", padx=5)
        self.entry_filtre_chambre = tk.Entry(filtres, width=10)
        self.entry_filtre_chambre.pack(side="left", padx=5)
        btn_filtrer = tk.Button(filtres, text="Filtrer", command=self._filtrer_historique, bg="#5a4a32", fg="#fff8e7", font=("Segoe UI", 9, "bold"))
        btn_filtrer.pack(side="left", padx=10)
        btn_reset = tk.Button(filtres, text="Réinitialiser", command=self._actualiser_historique, bg="#e8dcc8", fg="#5a4a32", font=("Segoe UI", 9, "bold"))
        btn_reset.pack(side="left", padx=5)

        # Table historique
        table_frame = tk.LabelFrame(frame, text="Toutes les réservations", bg="#fff8e7", font=("Segoe UI", 11, "bold"), fg="#5a4a32")
        table_frame.pack(fill="both", expand=True, padx=20, pady=15)

        self.table_historique = ttk.Treeview(table_frame, columns=("id", "client", "chambre", "debut", "fin", "duree", "total", "paye", "solde"), show="headings", height=12)
        for col in ("id", "client", "chambre", "debut", "fin", "duree", "total", "paye", "solde"):
            self.table_historique.heading(col, text=col.capitalize())
            self.table_historique.column(col, width=110, anchor="center")
        self.table_historique.pack(fill="both", expand=True, padx=10, pady=10)

        return frame

    def _actualiser_historique(self):
        for item in self.table_historique.get_children():
            self.table_historique.delete(item)
        for r in sorted(RESERVATIONS, key=lambda x: x["date_debut"], reverse=True):
            debut_dt = datetime.strptime(r["date_debut"], "%Y-%m-%d")
            fin_dt = datetime.strptime(r["date_fin"], "%Y-%m-%d")
            duree = (fin_dt - debut_dt).days
            solde = max(0, r["montant_total"] - r["montant_paye"])
            self.table_historique.insert("", "end", values=(
                r["id"], r["nom_client"], r["chambre_num"],
                r["date_debut"], r["date_fin"], f"{duree} nuits",
                f"{r['montant_total']:,} €".replace(",", " "),
                f"{r['montant_paye']:,} €".replace(",", " "),
                f"{solde:,} €".replace(",", " ")
            ))

    def _filtrer_historique(self):
        filtre_client = self.entry_filtre_client.get().lower().strip()
        filtre_chambre = self.entry_filtre_chambre.get().strip()
        for item in self.table_historique.get_children():
            self.table_historique.delete(item)
        for r in sorted(RESERVATIONS, key=lambda x: x["date_debut"], reverse=True):
            ok_client = not filtre_client or filtre_client in r["nom_client"].lower()
            ok_chambre = not filtre_chambre or filtre_chambre == str(r["chambre_num"])
            if ok_client and ok_chambre:
                debut_dt = datetime.strptime(r["date_debut"], "%Y-%m-%d")
                fin_dt = datetime.strptime(r["date_fin"], "%Y-%m-%d")
                duree = (fin_dt - debut_dt).days
                solde = max(0, r["montant_total"] - r["montant_paye"])
                self.table_historique.insert("", "end", values=(
                    r["id"], r["nom_client"], r["chambre_num"],
                    r["date_debut"], r["date_fin"], f"{duree} nuits",
                    f"{r['montant_total']:,} €".replace(",", " "),
                    f"{r['montant_paye']:,} €".replace(",", " "),
                    f"{solde:,} €".replace(",", " ")
                ))

    # ============================================================
    # PAIEMENTS / SOLDES
    # ============================================================
    def _creer_paiements(self):
        frame = tk.Frame(self.notebook, bg="#fff8e7")
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="Soldes et Paiements", font=("Segoe UI", 20, "bold"), bg="#fff8e7", fg="#3a2a1a").pack(pady=(15, 25))

        # Résumé par client
        resume = tk.LabelFrame(frame, text="Résumé des soldes par client", bg="#fff8e7", font=("Segoe UI", 12, "bold"), fg="#5a4a32")
        resume.pack(fill="x", padx=20, pady=10)

        self.table_soldes = ttk.Treeview(resume, columns=("client", "reservations", "total_du", "total_paye", "solde_restant"), show="headings", height=8)
        for col in ("client", "reservations", "total_du", "total_paye", "solde_restant"):
            self.table_soldes.heading(col, text=col.replace("_", " ").capitalize())
            self.table_soldes.column(col, width=140, anchor="center")
        self.table_soldes.pack(fill="x", padx=10, pady=10)

        # Détail des réservations avec solde
        detail = tk.LabelFrame(frame, text="Détail des réservations avec solde", bg="#fff8e7", font=("Segoe UI", 11, "bold"), fg="#5a4a32")
        detail.pack(fill="both", expand=True, padx=20, pady=10)

        self.table_detail_soldes = ttk.Treeview(detail, columns=("id", "client", "chambre", "debut", "fin", "montant_total", "montant_paye", "solde"), show="headings", height=10)
        for col in ("id", "client", "chambre", "debut", "fin", "montant_total", "montant_paye", "solde"):
            self.table_detail_soldes.heading(col, text=col.replace("_", " ").capitalize())
            self.table_detail_soldes.column(col, width=110, anchor="center")
        self.table_detail_soldes.pack(fill="both", expand=True, padx=10, pady=10)

        return frame

    def _actualiser_paiements(self):
        # Nettoyer
        for item in self.table_soldes.get_children():
            self.table_soldes.delete(item)
        for item in self.table_detail_soldes.get_children():
            self.table_detail_soldes.delete(item)

        # Résumé par client
        clients = defaultdict(lambda: {"total_du": 0, "total_paye": 0, "nb_resa": 0})
        for r in RESERVATIONS:
            clients[r["nom_client"]]["total_du"] += r["montant_total"]
            clients[r["nom_client"]]["total_paye"] += r["montant_paye"]
            clients[r["nom_client"]]["nb_resa"] += 1

        for client, data in sorted(clients.items()):
            solde = data["total_du"] - data["total_paye"]
            self.table_soldes.insert("", "end", values=(
                client,
                data["nb_resa"],
                f"{data['total_du']:,} €".replace(",", " "),
                f"{data['total_paye']:,} €".replace(",", " "),
                f"{solde:,} €".replace(",", " ")
            ))

        # Détail
        for r in sorted(RESERVATIONS, key=lambda x: x["nom_client"]):
            solde = max(0, r["montant_total"] - r["montant_paye"])
            self.table_detail_soldes.insert("", "end", values=(
                r["id"], r["nom_client"], r["chambre_num"], r["date_debut"], r["date_fin"],
                f"{r['montant_total']:,} €".replace(",", " "),
                f"{r['montant_paye']:,} €".replace(",", " "),
                f"{solde:,} €".replace(",", " ")
            ))

    # ============================================================
    # MISE À JOUR GLOBALE
    # ============================================================
    def _actualiser_toutes_les_vues(self):
        self._actualiser_accueil()
        self._actualiser_chambres()
        self.table_reservations.delete(*self.table_reservations.get_children())
        for r in sorted(RESERVATIONS, key=lambda x: x["date_debut"], reverse=True):
            solde = max(0, r["montant_total"] - r["montant_paye"])
            self.table_reservations.insert("", "end", values=(
                r["id"], r["nom_client"], r["chambre_num"], r["date_debut"], r["date_fin"],
                f"{r['montant_total']:,} €".replace(",", " "), f"{r['montant_paye']:,} €".replace(",", " "),
                f"{solde:,} €".replace(",", " ")
            ))
        self._afficher_mois()
        self._actualiser_historique()
        self._actualiser_paiements()
        self.status.config(text=f"Actualisé • {len(RESERVATIONS)} réservation(s) • Données en mémoire • {self.date_aujourd_hui}")

    # ============================================================
    # RÉINITIALISER
    # ============================================================
    def _reinitialiser_donnees(self):
        if messagebox.askyesno("Confirmation", "Voulez-vous réinitialiser toutes les données ?"):
            RESERVATIONS.clear()
            RESERVATIONS.extend([
                {"id": 1, "nom_client": "Marie Dupont", "chambre_num": 101, "date_debut": "2026-07-10", "date_fin": "2026-07-15", "montant_paye": 200, "montant_total": 425},
                {"id": 2, "nom_client": "Jean Lefebvre", "chambre_num": 102, "date_debut": "2026-07-14", "date_fin": "2026-07-20", "montant_paye": 300, "montant_total": 570},
                {"id": 3, "nom_client": "Claire Martin", "chambre_num": 103, "date_debut": "2026-07-18", "date_fin": "2026-07-25", "montant_paye": 700, "montant_total": 980},
            ])
            global next_id
            next_id = 4
            self._actualiser_toutes_les_vues()
            messagebox.showinfo("Réinitialisé", "Les données ont été restaurées aux valeurs initiales.")

    def _apropos(self):
        messagebox.showinfo("À propos", "Application de gestion des chambres d'hôtes\nDéveloppée avec Python et Tkinter\nStockage des données en mémoire (RAM)\nPas de base de données requise\n© 2026")


# ============================================================
# LANCEMENT
# ============================================================
if __name__ == "__main__":
    root = tk.Tk()
    app = AppChambresHotes(root)
    # Forcer la mise à jour au démarrage
    root.after(500, app._actualiser_toutes_les_vues)
    root.mainloop()
