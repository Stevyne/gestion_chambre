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
# CONVERSION DE FORMAT DE DATE
# ============================================================
# En base et en interne (comparaisons, tris, calendrier), les dates
# restent au format AAAA-MM-JJ (ISO, triable lexicographiquement).
# À l'écran (saisie et tableaux), elles sont affichées en JJ/MM/AAAA.

def format_date_affichage(date_iso):
    """Convertit une date AAAA-MM-JJ (stockage) en JJ/MM/AAAA (affichage)."""
    try:
        return datetime.strptime(date_iso, "%Y-%m-%d").strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return date_iso

def parser_date_affichage(date_str):
    """Convertit une date JJ/MM/AAAA (saisie utilisateur) en AAAA-MM-JJ (stockage).
    Lève ValueError si le format est invalide."""
    return datetime.strptime(date_str.strip(), "%d/%m/%Y").strftime("%Y-%m-%d")

def reservation_chevauche(debut_iso, fin_iso, autre_debut_iso, autre_fin_iso):
    """Indique si deux plages [debut, fin] (dates ISO AAAA-MM-JJ, bornes incluses,
    comme partout ailleurs dans l'appli) se chevauchent."""
    return debut_iso <= autre_fin_iso and autre_debut_iso <= fin_iso

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
next_id = 4

# ============================================================
# CLASSE PRINCIPALE
# ============================================================

class AppChambresHotes:
    def __init__(self, root):
        self.root = root
        self.root.title("🏨 Gestion des Chambres d'Hôtes")
        self.root.geometry("1100x780")
        self.root.minsize(900, 680)
        self.root.configure(bg="#eef2f7")

        # Style personnalisé
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background="#eef2f7", borderwidth=0)
        style.configure("TNotebook.Tab", font=("Segoe UI", 11, "bold"), padding=[15, 8], background="#e2e8f0", foreground="#1e293b")
        style.map("TNotebook.Tab", background=[("selected", "#f8fafc"), ("active", "#f1f5f9")])
        style.configure("TFrame", background="#eef2f7")
        style.configure("TLabelframe", background="#f8fafc", relief="solid", borderwidth=1, bordercolor="#e2e8f0")
        style.configure("TLabelframe.Label", background="#f8fafc", font=("Segoe UI", 11, "bold"), foreground="#475569")

        # Tableaux (Treeview) : look plat et moderne, lignes aérées
        style.configure("Treeview", background="#ffffff", fieldbackground="#ffffff", foreground="#0f172a",
                         rowheight=28, borderwidth=0, relief="flat", font=("Segoe UI", 10))
        style.configure("Treeview.Heading", background="#eef2f7", foreground="#0f172a",
                         font=("Segoe UI", 10, "bold"), relief="flat", borderwidth=0)
        style.map("Treeview.Heading", background=[("active", "#e2e8f0")])
        style.map("Treeview", background=[("selected", "#2563eb")], foreground=[("selected", "#ffffff")])

        # Listes déroulantes
        style.configure("TCombobox", fieldbackground="#ffffff", background="#ffffff", foreground="#0f172a", padding=4)
        style.map("TCombobox", fieldbackground=[("readonly", "#ffffff")], foreground=[("readonly", "#0f172a")])

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
        self.onglet_chiffre = self._creer_chiffre_affaires()

        self.notebook.add(self.onglet_accueil, text="🏠 Accueil")
        self.notebook.add(self.onglet_chambres, text="🛏️ Chambres")
        self.notebook.add(self.onglet_reservations, text="📅 Réservations")
        self.notebook.add(self.onglet_calendrier, text="📊 Calendrier")
        self.notebook.add(self.onglet_historique, text="📜 Historique")
        self.notebook.add(self.onglet_paiements, text="💰 Paiements")
        self.notebook.add(self.onglet_chiffre, text="💰 CA par Chambre")

        # Barre de statut
        self.status = tk.Label(root, text="Prêt • Données SQLite (chambres.db) • Persistance automatique", bg="#475569", fg="#f8fafc", font=("Segoe UI", 9), pady=6)
        self.status.pack(fill="x", side="bottom")

        # Charger les données sauvegardées
        self._charger_donnees()

        # Mise à jour initiale
        self._actualiser_accueil()
        self._actualiser_toutes_les_vues()

    # ============================================================
    # MENU
    # ============================================================
    def _creer_menu(self):
        menubar = tk.Menu(self.root, bg="#475569", fg="#f8fafc", font=("Segoe UI", 10))
        self.root.config(menu=menubar)

        menu_fichier = tk.Menu(menubar, tearoff=0, bg="#475569", fg="#f8fafc")
        menubar.add_cascade(label="Fichier", menu=menu_fichier)
        menu_fichier.add_command(label="Réinitialiser les données", command=self._reinitialiser_donnees)
        menu_fichier.add_separator()
        menu_fichier.add_command(label="Quitter", command=self.root.quit)

        menu_aide = tk.Menu(menubar, tearoff=0, bg="#475569", fg="#f8fafc")
        menubar.add_cascade(label="Aide", menu=menu_aide)
        menu_aide.add_command(label="À propos", command=self._apropos)

    # ============================================================
    # ACCUEIL (TABLEAU DE BORD)
    # ============================================================
    def _creer_accueil(self):
        frame = tk.Frame(self.notebook, bg="#f8fafc")
        frame.pack(fill="both", expand=True)

        # Titre
        tk.Label(frame, text="Tableau de Bord", font=("Segoe UI", 22, "bold"), bg="#f8fafc", fg="#0f172a").pack(pady=(15, 25))

        # Cartes statistiques (4 colonnes)
        cartes = tk.Frame(frame, bg="#f8fafc")
        cartes.pack(pady=10)

        self.stat_chambres_libres = self._carte_stat(cartes, "Chambres disponibles", "0", "#16a34a", 0)
        self.stat_reservations_actives = self._carte_stat(cartes, "Réservations actives", "0", "#2563eb", 1)
        self.stat_total_soldes = self._carte_stat(cartes, "Total des soldes dus", "0 €", "#ea580c", 2)
        self.stat_client_aujourdhui = self._carte_stat(cartes, "Client du jour", "—", "#7c3aed", 3)

        # Section réservations du jour / prochaines
        section = tk.LabelFrame(frame, text="Réservations du jour et à venir", bg="#f8fafc", font=("Segoe UI", 12, "bold"), fg="#475569")
        section.pack(fill="both", expand=True, padx=20, pady=20)

        self.table_accueil = ttk.Treeview(section, columns=("nom", "chambre", "dates", "solde"), show="headings", height=8)
        for col in ("nom", "chambre", "dates", "solde"):
            self.table_accueil.heading(col, text=col.capitalize())
            self.table_accueil.column(col, width=200, anchor="center")
        self.table_accueil.pack(fill="both", expand=True, padx=10, pady=10)

        # Section dernières réservations
        section2 = tk.LabelFrame(frame, text="Dernières réservations enregistrées", bg="#f8fafc", font=("Segoe UI", 11, "bold"), fg="#475569")
        section2.pack(fill="x", padx=20, pady=10)
        self.table_dernieres = ttk.Treeview(section2, columns=("id", "nom", "chambre", "debut", "fin"), show="headings", height=5)
        for col in ("id", "nom", "chambre", "debut", "fin"):
            self.table_dernieres.heading(col, text=col.capitalize())
            self.table_dernieres.column(col, width=130, anchor="center")
        self.table_dernieres.pack(fill="x", padx=10, pady=10)

        return frame

    def _carte_stat(self, parent, titre, valeur, couleur, colonne):
        carte = tk.Frame(parent, bg=couleur, relief="flat", bd=0)
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
        self.stat_total_soldes.label_val.config(text=f"{total_soldes:,} Ar".replace(",", " "))

        # Client du jour
        clients_aujourdhui = [r["nom_client"] for r in RESERVATIONS if r["date_debut"] <= aujourdhui <= r["date_fin"]]
        self.stat_client_aujourdhui.label_val.config(text=clients_aujourdhui[0] if clients_aujourdhui else "—")

        # Table accueil
        for item in self.table_accueil.get_children():
            self.table_accueil.delete(item)
        aujourdhui_dt = datetime.strptime(aujourdhui, "%Y-%m-%d")
        for r in sorted(RESERVATIONS, key=lambda x: x["date_debut"]):
            solde = max(0, r["montant_total"] - r["montant_paye"])
            self.table_accueil.insert("", "end", values=(r["nom_client"], f"Chambre {r['chambre_num']}", f"{format_date_affichage(r['date_debut'])} → {format_date_affichage(r['date_fin'])}", f"{solde:,} Ar".replace(",", " ")))

        # Table dernières réservations
        for item in self.table_dernieres.get_children():
            self.table_dernieres.delete(item)
        for r in sorted(RESERVATIONS, key=lambda x: x["date_debut"], reverse=True)[:5]:
            self.table_dernieres.insert("", "end", values=(r["id"], r["nom_client"], r["chambre_num"], format_date_affichage(r["date_debut"]), format_date_affichage(r["date_fin"])))

    # ============================================================
    # CHAMBRES
    # ============================================================
    def _creer_chambres(self):
        frame = tk.Frame(self.notebook, bg="#f8fafc")
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="État des Chambres", font=("Segoe UI", 20, "bold"), bg="#f8fafc", fg="#0f172a").pack(pady=(15, 20))

        # Liste des chambres (conteneur principal : table + formulaire côte à côte)
        conteneur_principal = tk.Frame(frame, bg="#f8fafc")
        conteneur_principal.pack(fill="both", expand=True, padx=20, pady=10)

        liste_frame = tk.Frame(conteneur_principal, bg="#f8fafc")
        liste_frame.pack(side="left", fill="both", expand=True)

        self.table_chambres = ttk.Treeview(liste_frame, columns=("num", "nom", "type", "prix", "statut"), show="headings", height=12)
        for col in ("num", "nom", "type", "prix", "statut"):
            self.table_chambres.heading(col, text=col.capitalize())
            self.table_chambres.column(col, width=160, anchor="center")
        self.table_chambres.pack(fill="both", expand=True)


        # Légende / Détails + Formulaire d'ajout (dans le même conteneur, à droite)
        colonne_droite = tk.Frame(conteneur_principal, bg="#f8fafc", width=380)
        colonne_droite.pack(side="right", fill="y", padx=(15, 0))
        colonne_droite.pack_propagate(False)

        details = tk.LabelFrame(colonne_droite, text="Informations", bg="#f8fafc", font=("Segoe UI", 10, "bold"), fg="#475569")
        details.pack(fill="x", pady=(0, 15))
        tk.Label(details, text="• Vert  = Disponible\n• Rouge = Occupée", bg="#f8fafc", fg="#1e293b", font=("Segoe UI", 9), justify="left").pack(anchor="w", padx=10, pady=8)

        # === FORMULAIRE AJOUT CHAMBRE ===
        form_chambre = tk.LabelFrame(colonne_droite, text="Ajouter une chambre", bg="#f8fafc", font=("Segoe UI", 11, "bold"), fg="#475569")
        form_chambre.pack(fill="x", pady=10)

        tk.Label(form_chambre, text="Numéro :", bg="#f8fafc", font=("Segoe UI", 9)).pack(anchor="w", padx=10, pady=(10, 2))
        self.entry_chambre_num = tk.Entry(form_chambre, font=("Segoe UI", 10), width=18)
        self.entry_chambre_num.pack(anchor="w", padx=10, pady=2)

        tk.Label(form_chambre, text="Nom :", bg="#f8fafc", font=("Segoe UI", 9)).pack(anchor="w", padx=10, pady=(8, 2))
        self.entry_chambre_nom = tk.Entry(form_chambre, font=("Segoe UI", 10), width=25)
        self.entry_chambre_nom.pack(anchor="w", padx=10, pady=2)
        self.entry_chambre_nom.insert(0, "Chambre du Soleil")

        tk.Label(form_chambre, text="Type :", bg="#f8fafc", font=("Segoe UI", 9)).pack(anchor="w", padx=10, pady=(8, 2))
        self.entry_chambre_type = ttk.Combobox(form_chambre, values=["Simple", "Double", "Suite"], width=15, state="readonly")
        self.entry_chambre_type.pack(anchor="w", padx=10, pady=2)
        self.entry_chambre_type.current(1)

        tk.Label(form_chambre, text="Prix / nuit (Ar) :", bg="#f8fafc", font=("Segoe UI", 9)).pack(anchor="w", padx=10, pady=(8, 2))
        self.entry_chambre_prix = tk.Entry(form_chambre, font=("Segoe UI", 10), width=15)
        self.entry_chambre_prix.pack(anchor="w", padx=10, pady=2)
        self.entry_chambre_prix.insert(0, "100")

        btn_ajouter_ch = tk.Button(form_chambre, text="➕ Ajouter cette chambre", command=self._ajouter_chambre, bg="#2563eb", fg="#ffffff", font=("Segoe UI", 9, "bold"), padx=6, pady=3, relief="flat", bd=0)
        btn_ajouter_ch.pack(pady=2)

        btn_charger = tk.Button(form_chambre, text="📋 Charger sélection", command=self._charger_chambre_selectionnee, bg="#3b82f6", fg="#ffffff", font=("Segoe UI", 9, "bold"), padx=6, pady=3, relief="flat", bd=0)
        btn_charger.pack(pady=2)

        btn_modifier_ch = tk.Button(form_chambre, text="✏️ Modifier", command=self._modifier_chambre, bg="#ea580c", fg="#ffffff", font=("Segoe UI", 9, "bold"), padx=6, pady=3, relief="flat", bd=0)
        btn_modifier_ch.pack(pady=2)

        btn_supprimer_ch = tk.Button(form_chambre, text="❌ Supprimer", command=self._supprimer_chambre, bg="#dc2626", fg="#ffffff", font=("Segoe UI", 9, "bold"), padx=6, pady=3, relief="flat", bd=0)
        btn_supprimer_ch.pack(pady=2)

        return frame

    def _ajouter_chambre(self):
        try:
            num = int(self.entry_chambre_num.get().strip())
        except ValueError:
            messagebox.showerror("Erreur", "Le numéro de chambre doit être un nombre entier.")
            return
        nom = self.entry_chambre_nom.get().strip()
        type_ch = self.entry_chambre_type.get()
        try:
            prix = float(self.entry_chambre_prix.get().strip())
        except ValueError:
            messagebox.showerror("Erreur", "Le prix doit être un nombre.")
            return
        if not nom:
            messagebox.showerror("Erreur", "Veuillez donner un nom à la chambre.")
            return
        # Vérifier si le numéro existe déjà
        for c in CHAMBRES:
            if c["numero"] == num:
                messagebox.showerror("Erreur", f"Le numéro {num} existe déjà.")
                return
        CHAMBRES.append({"numero": num, "nom": nom, "type": type_ch, "prix_nuit": prix})
        # Mettre à jour le combo des réservations
        self.combo_chambre.config(values=[f"Chambre {c['numero']} - {c['nom']}" for c in CHAMBRES])
        messagebox.showinfo("Succès", f"Chambre {num} — {nom} ajoutée !")
        self._actualiser_toutes_les_vues()
        self._sauvegarder_donnees()
        # Nettoyer le formulaire
        self.entry_chambre_num.delete(0, tk.END)
        self.entry_chambre_num.insert(0, str(num + 1))
        self.entry_chambre_nom.delete(0, tk.END)
        self.entry_chambre_nom.insert(0, "Nouvelle chambre")
        self.entry_chambre_prix.delete(0, tk.END)
        self.entry_chambre_prix.insert(0, "85")

    def _charger_chambre_selectionnee(self, event=None):
        selection = self.table_chambres.selection()
        if not selection:
            return
        item = self.table_chambres.item(selection[0])
        valeurs = item["values"]
        # Remplir le formulaire avec la chambre sélectionnée
        self.entry_chambre_num.delete(0, tk.END)
        self.entry_chambre_num.insert(0, str(valeurs[0]))
        self.entry_chambre_nom.delete(0, tk.END)
        self.entry_chambre_nom.insert(0, str(valeurs[1]))
        self.entry_chambre_type.set(str(valeurs[2]))
        self.entry_chambre_prix.delete(0, tk.END)
        # Extraire le prix (sans le symbole Ar)
        prix_str = str(valeurs[3]).replace(" Ar", "").replace("Ar", "").strip()
        self.entry_chambre_prix.insert(0, prix_str)

    def _modifier_chambre(self):
        try:
            num = int(self.entry_chambre_num.get().strip())
        except ValueError:
            messagebox.showerror("Erreur", "Le numéro de chambre doit être un nombre entier.")
            return
        nom = self.entry_chambre_nom.get().strip()
        type_ch = self.entry_chambre_type.get()
        try:
            prix = float(self.entry_chambre_prix.get().strip())
        except ValueError:
            messagebox.showerror("Erreur", "Le prix doit être un nombre.")
            return
        if not nom:
            messagebox.showerror("Erreur", "Veuillez donner un nom à la chambre.")
            return
        # Modifier la chambre dans la liste
        for c in CHAMBRES:
            if c["numero"] == num:
                c["nom"] = nom
                c["type"] = type_ch
                c["prix_nuit"] = prix
                break
        else:
            messagebox.showerror("Erreur", f"Aucune chambre avec le numéro {num} n'a été trouvée.")
            return
        # Mettre à jour le combo des réservations
        self.combo_chambre.config(values=[f"Chambre {c['numero']} - {c['nom']}" for c in CHAMBRES])
        messagebox.showinfo("Succès", f"Chambre {num} — {nom} modifiée !")
        self._actualiser_toutes_les_vues()
        self._sauvegarder_donnees()

    def _supprimer_chambre(self):
        try:
            num = int(self.entry_chambre_num.get().strip())
        except ValueError:
            messagebox.showerror("Erreur", "Aucun numéro valide dans le formulaire. Cliquez d'abord sur une chambre dans la liste.")
            return

        # Empêcher la suppression si des réservations (passées, en cours ou futures) référencent cette chambre
        reservations_liees = [r for r in RESERVATIONS if r["chambre_num"] == num]
        if reservations_liees:
            messagebox.showerror(
                "Suppression impossible",
                f"La chambre {num} est référencée par {len(reservations_liees)} réservation(s) "
                "(historique compris) et ne peut pas être supprimée.\n"
                "Vous pouvez toutefois la modifier (nom, type, prix) si nécessaire."
            )
            return

        if messagebox.askyesno("Confirmation", f"Voulez-vous vraiment supprimer la chambre {num} ?"):
            chambre_a_supprimer = None
            for c in CHAMBRES:
                if c["numero"] == num:
                    chambre_a_supprimer = c
                    break
            if chambre_a_supprimer:
                CHAMBRES.remove(chambre_a_supprimer)
                # Mettre à jour le combo des réservations
                self.combo_chambre.config(values=[f"Chambre {c['numero']} - {c['nom']}" for c in CHAMBRES])
                messagebox.showinfo("Succès", f"Chambre {num} supprimée.")
                self._actualiser_toutes_les_vues()
                self._sauvegarder_donnees()
                # Nettoyer le formulaire
                self.entry_chambre_num.delete(0, tk.END)
                self.entry_chambre_nom.delete(0, tk.END)
                self.entry_chambre_type.set("Double")
                self.entry_chambre_prix.delete(0, tk.END)
            else:
                messagebox.showerror("Erreur", f"Chambre {num} non trouvée.")

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
            self.table_chambres.insert("", "end", values=(ch["numero"], ch["nom"], ch["type"], f"{ch['prix_nuit']} Ar", statut), tags=(tag,))
        self.table_chambres.tag_configure("occupee", background="#fecaca", foreground="#7f1d1d")
        self.table_chambres.tag_configure("dispo", background="#bbf7d0", foreground="#15803d")

    # ============================================================
    # RÉSERVATIONS (FORMULAIRE)
    # ============================================================
    def _creer_reservations(self):
        global next_id
        self.id_reservation_en_edition = None
        frame = tk.Frame(self.notebook, bg="#f8fafc")
        frame.pack(fill="both", expand=True)

        # Titre
        tk.Label(frame, text="Nouvelle Réservation", font=("Segoe UI", 20, "bold"), bg="#f8fafc", fg="#0f172a").pack(pady=(15, 25))

        # Formulaire
        form = tk.LabelFrame(frame, text="Informations de réservation", bg="#f8fafc", font=("Segoe UI", 12, "bold"), fg="#475569")
        form.pack(padx=30, pady=15, fill="x")

        # Grille
        grid = tk.Frame(form, bg="#f8fafc")
        grid.pack(padx=15, pady=15)

        tk.Label(grid, text="Nom du client :", bg="#f8fafc", font=("Segoe UI", 10)).grid(row=0, column=0, sticky="e", pady=6)
        self.entry_nom = tk.Entry(grid, font=("Segoe UI", 10), width=30)
        self.entry_nom.grid(row=0, column=1, sticky="w", pady=6)
        self.entry_nom.insert(0, "Jean Dupont")

        tk.Label(grid, text="Chambre :", bg="#f8fafc", font=("Segoe UI", 10)).grid(row=1, column=0, sticky="e", pady=6)
        self.combo_chambre = ttk.Combobox(grid, values=[f"Chambre {c['numero']} - {c['nom']}" for c in CHAMBRES], width=28, state="readonly")
        self.combo_chambre.grid(row=1, column=1, sticky="w", pady=6)
        self.combo_chambre.current(0)

        tk.Label(grid, text="Date début (JJ/MM/AAAA) :", bg="#f8fafc", font=("Segoe UI", 10)).grid(row=2, column=0, sticky="e", pady=6)
        self.entry_debut = tk.Entry(grid, font=("Segoe UI", 10), width=20)
        self.entry_debut.grid(row=2, column=1, sticky="w", pady=6)
        self.entry_debut.insert(0, datetime.now().strftime("%d/%m/%Y"))

        tk.Label(grid, text="Date fin (JJ/MM/AAAA) :", bg="#f8fafc", font=("Segoe UI", 10)).grid(row=3, column=0, sticky="e", pady=6)
        self.entry_fin = tk.Entry(grid, font=("Segoe UI", 10), width=20)
        self.entry_fin.grid(row=3, column=1, sticky="w", pady=6)
        self.entry_fin.insert(0, (datetime.now() + timedelta(days=3)).strftime("%d/%m/%Y"))

        self.label_remise = tk.Label(grid, text="Remise (%) :", bg="#f8fafc", font=("Segoe UI", 10))
        self.label_remise.grid(row=4, column=0, sticky="e", pady=6)
        ligne_remise = tk.Frame(grid, bg="#f8fafc")
        ligne_remise.grid(row=4, column=1, sticky="w", pady=6)
        self.entry_remise = tk.Entry(ligne_remise, font=("Segoe UI", 10), width=8)
        self.entry_remise.pack(side="left")
        self.entry_remise.insert(0, "0")

        self.type_remise = tk.StringVar(value="pourcentage")
        tk.Radiobutton(ligne_remise, text="%", variable=self.type_remise, value="pourcentage", bg="#f8fafc", font=("Segoe UI", 9), command=self._on_type_remise_change).pack(side="left", padx=(8, 0))
        tk.Radiobutton(ligne_remise, text="Ar fixe", variable=self.type_remise, value="montant", bg="#f8fafc", font=("Segoe UI", 9), command=self._on_type_remise_change).pack(side="left")

        self.boutons_remise_rapide = []
        for pct, label in ((10, "10%"), (20, "20%"), (30, "30%"), (50, "50%")):
            btn = tk.Button(
                ligne_remise, text=label, bg="#e2e8f0", fg="#0f172a", font=("Segoe UI", 8, "bold"),
                padx=4, pady=2, relief="flat", bd=0,
                command=lambda p=pct: self._appliquer_remise_rapide(p)
            )
            btn.pack(side="left", padx=(6, 0))
            self.boutons_remise_rapide.append(btn)

        tk.Label(grid, text="Montant total (Ar) :", bg="#f8fafc", font=("Segoe UI", 10)).grid(row=5, column=0, sticky="e", pady=6)
        self.entry_total = tk.Entry(grid, font=("Segoe UI", 10), width=20, state="readonly", readonlybackground="#f8fafc")
        self.entry_total.grid(row=5, column=1, sticky="w", pady=6)
        self.entry_total.insert(0, "300")

        tk.Label(grid, text="Montant payé (Ar) :", bg="#f8fafc", font=("Segoe UI", 10)).grid(row=6, column=0, sticky="e", pady=6)
        ligne_paye = tk.Frame(grid, bg="#f8fafc")
        ligne_paye.grid(row=6, column=1, sticky="w", pady=6)
        self.entry_paye = tk.Entry(ligne_paye, font=("Segoe UI", 10), width=14)
        self.entry_paye.pack(side="left")
        self.entry_paye.insert(0, "0")
        btn_paye_total = tk.Button(ligne_paye, text="✅ Payé intégralement", command=self._marquer_paye_formulaire, bg="#16a34a", fg="#ffffff", font=("Segoe UI", 8, "bold"), padx=4, pady=2, relief="flat", bd=0)
        btn_paye_total.pack(side="left", padx=(8, 0))

        # Lier le calcul automatique
        self.combo_chambre.bind("<<ComboboxSelected>>", self._calculer_montant_automatique)
        self.entry_debut.bind("<KeyRelease>", self._calculer_montant_automatique)
        self.entry_fin.bind("<KeyRelease>", self._calculer_montant_automatique)
        self.entry_remise.bind("<KeyRelease>", self._calculer_montant_automatique)

        # Indicateur de mode édition
        self.label_mode_reservation = tk.Label(form, text="", bg="#f8fafc", fg="#dc2626", font=("Segoe UI", 9, "bold"))
        self.label_mode_reservation.pack(pady=(0, 4))

        # Boutons
        btn_frame = tk.Frame(form, bg="#f8fafc")
        btn_frame.pack(pady=(5, 15))
        self.btn_enregistrer_reservation = tk.Button(btn_frame, text="✅ Enregistrer la réservation", command=self._enregistrer_reservation, bg="#16a34a", fg="#ffffff", font=("Segoe UI", 11, "bold"), padx=14, pady=8, relief="flat", bd=0)
        self.btn_enregistrer_reservation.pack(side="left", padx=5)
        btn_nouvelle_resa = tk.Button(btn_frame, text="🆕 Nouvelle réservation", command=self._nouvelle_reservation_form, bg="#2563eb", fg="#ffffff", font=("Segoe UI", 10, "bold"), padx=12, pady=8, relief="flat", bd=0)
        btn_nouvelle_resa.pack(side="left", padx=5)
        btn_supprimer_resa = tk.Button(btn_frame, text="🗑️ Supprimer la réservation", command=self._supprimer_reservation, bg="#dc2626", fg="#ffffff", font=("Segoe UI", 10, "bold"), padx=12, pady=8, relief="flat", bd=0)
        btn_supprimer_resa.pack(side="left", padx=5)

        # Tableau des réservations en cours
        section_table = tk.LabelFrame(frame, text="Réservations enregistrées", bg="#f8fafc", font=("Segoe UI", 12, "bold"), fg="#475569")
        section_table.pack(fill="both", expand=True, padx=30, pady=15)

        tk.Label(section_table, text="Astuce : cliquez sur une ligne pour la charger dans le formulaire ci-dessus (modification ou suppression).", bg="#f8fafc", fg="#64748b", font=("Segoe UI", 8, "italic")).pack(anchor="w", padx=10, pady=(8, 0))

        self.table_reservations = ttk.Treeview(section_table, columns=("id", "nom", "chambre", "debut", "fin", "total", "paye", "solde"), show="headings", height=8)
        for col in ("id", "nom", "chambre", "debut", "fin", "total", "paye", "solde"):
            self.table_reservations.heading(col, text=col.capitalize())
            self.table_reservations.column(col, width=110, anchor="center")
        self.table_reservations.pack(fill="both", expand=True, padx=10, pady=10)
        self.table_reservations.bind("<<TreeviewSelect>>", self._charger_reservation_selectionnee)

        return frame

    def _calculer_montant_automatique(self, event=None):
        chambre_str = self.combo_chambre.get()
        debut_str = self.entry_debut.get().strip()
        fin_str = self.entry_fin.get().strip()
        if not chambre_str or not debut_str or not fin_str:
            self.entry_total.config(state="normal")
            self.entry_total.delete(0, tk.END)
            self.entry_total.insert(0, "0")
            self.entry_total.config(state="readonly", readonlybackground="#f8fafc")
            return
        try:
            chambre_num = int(chambre_str.split()[1])
            debut_dt = datetime.strptime(debut_str, "%d/%m/%Y")
            fin_dt = datetime.strptime(fin_str, "%d/%m/%Y")
            duree = (fin_dt - debut_dt).days
            if duree <= 0:
                duree = 1  # au moins 1 nuit
        except (ValueError, IndexError):
            return
        # Trouver le prix de la chambre
        prix_nuit = 0
        for ch in CHAMBRES:
            if ch["numero"] == chambre_num:
                prix_nuit = ch["prix_nuit"]
                break
        montant_brut = prix_nuit * duree

        # Appliquer la remise éventuelle, selon le type choisi (pourcentage ou montant fixe)
        try:
            remise = float(self.entry_remise.get().strip() or "0")
        except ValueError:
            remise = 0

        if self.type_remise.get() == "montant":
            remise = max(0.0, remise)
            total = montant_brut - remise
        else:
            remise = max(0.0, min(100.0, remise))
            total = montant_brut * (1 - remise / 100)

        total = max(0.0, total)  # le total ne descend jamais sous 0, même si la remise fixe dépasse le montant brut
        self.entry_total.config(state="normal")
        self.entry_total.delete(0, tk.END)
        self.entry_total.insert(0, f"{total:.0f}")
        self.entry_total.config(state="readonly", readonlybackground="#f8fafc")

    def _on_type_remise_change(self):
        if self.type_remise.get() == "montant":
            self.label_remise.config(text="Remise (Ar) :")
            for btn in self.boutons_remise_rapide:
                btn.config(state="disabled")
        else:
            self.label_remise.config(text="Remise (%) :")
            for btn in self.boutons_remise_rapide:
                btn.config(state="normal")
        self._calculer_montant_automatique()

    def _appliquer_remise_rapide(self, pourcentage):
        self.type_remise.set("pourcentage")
        self.label_remise.config(text="Remise (%) :")
        self.entry_remise.delete(0, tk.END)
        self.entry_remise.insert(0, str(pourcentage))
        self._calculer_montant_automatique()

    def _marquer_paye_formulaire(self):
        montant_total_str = self.entry_total.get().strip()
        self.entry_paye.delete(0, tk.END)
        self.entry_paye.insert(0, montant_total_str)

    def _enregistrer_reservation(self):
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

        try:
            remise = float(self.entry_remise.get().strip() or "0")
        except ValueError:
            messagebox.showerror("Erreur", "La remise doit être un nombre (par exemple 20 pour 20%, ou 10000 pour 10 000 Ar).")
            return

        type_remise = self.type_remise.get()
        if type_remise == "montant":
            if remise < 0:
                messagebox.showerror("Erreur", "La remise fixe ne peut pas être négative.")
                return
            remise_pourcentage = 0.0
            remise_montant = remise
        else:
            if remise < 0 or remise > 100:
                messagebox.showerror("Erreur", "La remise en pourcentage doit être comprise entre 0 et 100.")
                return
            remise_pourcentage = remise
            remise_montant = 0.0

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

        # Vérifier le format de date (saisie JJ/MM/AAAA) et convertir vers le format de stockage AAAA-MM-JJ
        try:
            debut_iso = parser_date_affichage(debut)
            fin_iso = parser_date_affichage(fin)
        except ValueError:
            messagebox.showerror("Erreur", "Les dates doivent être au format JJ/MM/AAAA.")
            return

        # Vérifier que la date de fin n'est pas avant la date de début
        if fin_iso < debut_iso:
            messagebox.showerror("Erreur", "La date de fin ne peut pas être antérieure à la date de début.")
            return

        # Vérifier qu'il n'y a pas de chevauchement avec une réservation existante sur la même chambre
        # (on ignore la réservation elle-même si on est en train de la modifier)
        for r in RESERVATIONS:
            if r["id"] == self.id_reservation_en_edition:
                continue
            if r["chambre_num"] == chambre_num and reservation_chevauche(debut_iso, fin_iso, r["date_debut"], r["date_fin"]):
                messagebox.showerror(
                    "Chambre déjà réservée",
                    f"La chambre {chambre_num} est déjà réservée par {r['nom_client']} "
                    f"du {format_date_affichage(r['date_debut'])} au {format_date_affichage(r['date_fin'])}.\n"
                    "Veuillez choisir une autre chambre ou d'autres dates."
                )
                return

        # Vérifier que le montant payé ne dépasse pas le total
        if montant_paye > montant_total:
            messagebox.showerror("Erreur", "Le montant payé ne peut pas dépasser le montant total.")
            return

        if self.id_reservation_en_edition is not None:
            # Mode modification : mettre à jour la réservation existante
            reservation = next((r for r in RESERVATIONS if r["id"] == self.id_reservation_en_edition), None)
            if reservation is None:
                messagebox.showerror("Erreur", "Cette réservation n'existe plus (elle a peut-être été supprimée entretemps).")
                self._nouvelle_reservation_form()
                return
            reservation["nom_client"] = nom
            reservation["chambre_num"] = chambre_num
            reservation["date_debut"] = debut_iso
            reservation["date_fin"] = fin_iso
            reservation["montant_total"] = montant_total
            reservation["montant_paye"] = montant_paye
            reservation["remise_pourcentage"] = remise_pourcentage
            reservation["remise_montant"] = remise_montant
            messagebox.showinfo("Succès", f"Réservation #{reservation['id']} mise à jour pour {nom}.")
            self._nouvelle_reservation_form()
        else:
            # Mode ajout : nouvelle réservation
            nouvelle_reservation = {
                "id": next_id,
                "nom_client": nom,
                "chambre_num": chambre_num,
                "date_debut": debut_iso,
                "date_fin": fin_iso,
                "montant_total": montant_total,
                "montant_paye": montant_paye,
                "remise_pourcentage": remise_pourcentage,
                "remise_montant": remise_montant
            }
            RESERVATIONS.append(nouvelle_reservation)
            next_id += 1
            messagebox.showinfo("Succès", f"Réservation enregistrée pour {nom} (Chambre {chambre_num}).")

        self._actualiser_toutes_les_vues()
        self._sauvegarder_donnees()

    def _charger_reservation_selectionnee(self, event=None):
        selection = self.table_reservations.selection()
        if not selection:
            return
        valeurs = self.table_reservations.item(selection[0])["values"]
        # Colonnes : id, nom, chambre, debut, fin, total, paye, solde
        resa_id = int(valeurs[0])
        reservation = next((r for r in RESERVATIONS if r["id"] == resa_id), None)
        if reservation is None:
            return

        self.id_reservation_en_edition = resa_id

        self.entry_nom.delete(0, tk.END)
        self.entry_nom.insert(0, reservation["nom_client"])

        for i, c in enumerate(CHAMBRES):
            if c["numero"] == reservation["chambre_num"]:
                self.combo_chambre.current(i)
                break

        self.entry_debut.delete(0, tk.END)
        self.entry_debut.insert(0, format_date_affichage(reservation["date_debut"]))

        self.entry_fin.delete(0, tk.END)
        self.entry_fin.insert(0, format_date_affichage(reservation["date_fin"]))

        remise_montant = reservation.get("remise_montant", 0) or 0
        remise_pourcentage = reservation.get("remise_pourcentage", 0) or 0
        if remise_montant > 0:
            self.type_remise.set("montant")
            self.label_remise.config(text="Remise (Ar) :")
            for btn in self.boutons_remise_rapide:
                btn.config(state="disabled")
            self.entry_remise.delete(0, tk.END)
            self.entry_remise.insert(0, str(remise_montant))
        else:
            self.type_remise.set("pourcentage")
            self.label_remise.config(text="Remise (%) :")
            for btn in self.boutons_remise_rapide:
                btn.config(state="normal")
            self.entry_remise.delete(0, tk.END)
            self.entry_remise.insert(0, str(remise_pourcentage))

        self.entry_total.config(state="normal")
        self.entry_total.delete(0, tk.END)
        self.entry_total.insert(0, str(reservation["montant_total"]))
        self.entry_total.config(state="readonly", readonlybackground="#f8fafc")

        self.entry_paye.delete(0, tk.END)
        self.entry_paye.insert(0, str(reservation["montant_paye"]))

        self.btn_enregistrer_reservation.config(text="💾 Enregistrer les modifications", bg="#ea580c")
        self.label_mode_reservation.config(text=f"✏️ Modification de la réservation #{resa_id} ({reservation['nom_client']}) — cliquez sur \"Nouvelle réservation\" pour annuler.")

    def _nouvelle_reservation_form(self):
        self.id_reservation_en_edition = None
        self.label_mode_reservation.config(text="")
        self.btn_enregistrer_reservation.config(text="✅ Enregistrer la réservation", bg="#16a34a")

        self.entry_nom.delete(0, tk.END)
        self.entry_nom.insert(0, "Jean Dupont")
        if CHAMBRES:
            self.combo_chambre.current(0)
        self.entry_debut.delete(0, tk.END)
        self.entry_debut.insert(0, datetime.now().strftime("%d/%m/%Y"))
        self.entry_fin.delete(0, tk.END)
        self.entry_fin.insert(0, (datetime.now() + timedelta(days=3)).strftime("%d/%m/%Y"))
        self.type_remise.set("pourcentage")
        self.label_remise.config(text="Remise (%) :")
        for btn in self.boutons_remise_rapide:
            btn.config(state="normal")
        self.entry_remise.delete(0, tk.END)
        self.entry_remise.insert(0, "0")
        self.entry_paye.delete(0, tk.END)
        self.entry_paye.insert(0, "0")
        self._calculer_montant_automatique()

        for item in self.table_reservations.selection():
            self.table_reservations.selection_remove(item)

    def _supprimer_reservation(self):
        if self.id_reservation_en_edition is None:
            messagebox.showinfo("Information", "Sélectionnez d'abord une réservation dans le tableau ci-dessous.")
            return
        reservation = next((r for r in RESERVATIONS if r["id"] == self.id_reservation_en_edition), None)
        if reservation is None:
            messagebox.showerror("Erreur", "Cette réservation n'existe plus.")
            self._nouvelle_reservation_form()
            return
        if messagebox.askyesno(
            "Confirmation",
            f"Voulez-vous vraiment supprimer la réservation #{reservation['id']} de {reservation['nom_client']} "
            f"(Chambre {reservation['chambre_num']}, du {format_date_affichage(reservation['date_debut'])} "
            f"au {format_date_affichage(reservation['date_fin'])}) ?\n\nCette action est irréversible."
        ):
            RESERVATIONS.remove(reservation)
            messagebox.showinfo("Succès", "Réservation supprimée.")
            self._nouvelle_reservation_form()
            self._actualiser_toutes_les_vues()
            self._sauvegarder_donnees()

    # ============================================================
    # CALENDRIER
    # ============================================================
    def _creer_calendrier(self):
        frame = tk.Frame(self.notebook, bg="#f8fafc")
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="Calendrier des Réservations", font=("Segoe UI", 20, "bold"), bg="#f8fafc", fg="#0f172a").pack(pady=(15, 25))

        # Sélection du mois
        controles = tk.Frame(frame, bg="#f8fafc")
        controles.pack(pady=5)

        self.mois_actuel = datetime.now().strftime("%Y-%m")

        btn_prec = tk.Button(controles, text="◀ Mois précédent", command=self._mois_precedent, bg="#e2e8f0", fg="#475569", font=("Segoe UI", 9, "bold"))
        btn_prec.pack(side="left", padx=10)

        self.label_mois = tk.Label(controles, text=self.mois_actuel, bg="#f8fafc", fg="#0f172a", font=("Segoe UI", 14, "bold"), width=15)
        self.label_mois.pack(side="left", padx=20)

        btn_suiv = tk.Button(controles, text="Mois suivant ▶", command=self._mois_suivant, bg="#e2e8f0", fg="#475569", font=("Segoe UI", 9, "bold"))
        btn_suiv.pack(side="left", padx=10)

        # Calendrier visuel
        calendrier_frame = tk.Frame(frame, bg="#f8fafc")
        calendrier_frame.pack(padx=20, pady=15, fill="both", expand=True)

        self.cells = {}
        for i in range(7):
            calendrier_frame.grid_columnconfigure(i, weight=1)
        for i in range(7):
            calendrier_frame.grid_rowconfigure(i, weight=1)

        jours_semaine = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
        for i, jour in enumerate(jours_semaine):
            tk.Label(calendrier_frame, text=jour, bg="#475569", fg="#f8fafc", font=("Segoe UI", 10, "bold"), relief="flat", bd=1).grid(row=0, column=i, sticky="nsew", padx=2, pady=2)

        for i in range(6):
            for j in range(7):
                cell = tk.Label(calendrier_frame, text="", bg="#f8fafc", relief="flat", bd=1, highlightthickness=1, highlightbackground="#e2e8f0", font=("Segoe UI", 9))
                cell.grid(row=i+1, column=j, sticky="nsew", padx=2, pady=2)
                self.cells[(i+1, j)] = cell

        self._afficher_mois()

        # Légende
        legende = tk.Frame(frame, bg="#f8fafc")
        legende.pack(pady=10)
        tk.Label(legende, text="● Disponible", bg="#f8fafc", fg="#16a34a", font=("Segoe UI", 10, "bold")).pack(side="left", padx=15)
        tk.Label(legende, text="● Réservé", bg="#f8fafc", fg="#ea580c", font=("Segoe UI", 10, "bold")).pack(side="left", padx=15)
        tk.Label(legende, text="● Occupé (aujourd'hui)", bg="#f8fafc", fg="#dc2626", font=("Segoe UI", 10, "bold")).pack(side="left", padx=15)

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
            cell.config(text="", bg="#f8fafc", fg="#0f172a")

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
                couleur = "#f87171"
                texte = f"{jour}\n(AUJ.)\n"
            elif chambres_reservees:
                couleur = "#fed7aa"
                texte = f"{jour}\n"
            else:
                couleur = "#dcfce7"
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
                cell.config(text=texte, bg=couleur, fg="#0f172a", font=("Segoe UI", 8))

    # ============================================================
    # HISTORIQUE
    # ============================================================
    def _creer_historique(self):
        frame = tk.Frame(self.notebook, bg="#f8fafc")
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="Historique des Réservations", font=("Segoe UI", 20, "bold"), bg="#f8fafc", fg="#0f172a").pack(pady=(15, 25))

        # Filtres
        filtres = tk.Frame(frame, bg="#f8fafc")
        filtres.pack(pady=5)
        tk.Label(filtres, text="Client :", bg="#f8fafc", font=("Segoe UI", 10)).pack(side="left", padx=5)
        self.entry_filtre_client = tk.Entry(filtres, width=20)
        self.entry_filtre_client.pack(side="left", padx=5)
        tk.Label(filtres, text="Chambre :", bg="#f8fafc", font=("Segoe UI", 10)).pack(side="left", padx=5)
        self.entry_filtre_chambre = tk.Entry(filtres, width=10)
        self.entry_filtre_chambre.pack(side="left", padx=5)
        btn_filtrer = tk.Button(filtres, text="Filtrer", command=self._filtrer_historique, bg="#475569", fg="#f8fafc", font=("Segoe UI", 9, "bold"))
        btn_filtrer.pack(side="left", padx=10)
        btn_reset = tk.Button(filtres, text="Réinitialiser", command=self._actualiser_historique, bg="#e2e8f0", fg="#475569", font=("Segoe UI", 9, "bold"))
        btn_reset.pack(side="left", padx=5)

        # Table historique
        table_frame = tk.LabelFrame(frame, text="Toutes les réservations", bg="#f8fafc", font=("Segoe UI", 11, "bold"), fg="#475569")
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
                format_date_affichage(r["date_debut"]), format_date_affichage(r["date_fin"]), f"{duree} nuits",
                f"{r['montant_total']:,} Ar".replace(",", " "),
                f"{r['montant_paye']:,} Ar".replace(",", " "),
                f"{solde:,} Ar".replace(",", " ")
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
                    format_date_affichage(r["date_debut"]), format_date_affichage(r["date_fin"]), f"{duree} nuits",
                    f"{r['montant_total']:,} Ar".replace(",", " "),
                    f"{r['montant_paye']:,} Ar".replace(",", " "),
                    f"{solde:,} Ar".replace(",", " ")
                ))

    # ============================================================
    # PAIEMENTS / SOLDES
    # ============================================================
    def _creer_paiements(self):
        frame = tk.Frame(self.notebook, bg="#f8fafc")
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="Soldes et Paiements", font=("Segoe UI", 20, "bold"), bg="#f8fafc", fg="#0f172a").pack(pady=(15, 25))

        # Résumé par client
        resume = tk.LabelFrame(frame, text="Résumé des soldes par client", bg="#f8fafc", font=("Segoe UI", 12, "bold"), fg="#475569")
        resume.pack(fill="x", padx=20, pady=10)

        self.table_soldes = ttk.Treeview(resume, columns=("client", "reservations", "total_du", "total_paye", "solde_restant"), show="headings", height=5)
        for col in ("client", "reservations", "total_du", "total_paye", "solde_restant"):
            self.table_soldes.heading(col, text=col.replace("_", " ").capitalize())
            self.table_soldes.column(col, width=140, anchor="center")
        self.table_soldes.pack(fill="x", padx=10, pady=10)

        # Mise à jour d'un paiement (placé ici, avant le tableau extensible, pour rester
        # toujours visible même sur un écran ou une fenêtre de taille réduite)
        maj = tk.LabelFrame(frame, text="Mettre à jour un paiement", bg="#f8fafc", font=("Segoe UI", 11, "bold"), fg="#475569")
        maj.pack(fill="x", padx=20, pady=(0, 10))

        ligne = tk.Frame(maj, bg="#f8fafc")
        ligne.pack(padx=10, pady=(10, 2), fill="x")

        tk.Label(ligne, text="Réservation (ID) :", bg="#f8fafc", font=("Segoe UI", 9)).pack(side="left", padx=(0, 5))
        self.entry_paiement_id = tk.Entry(ligne, font=("Segoe UI", 10), width=8)
        self.entry_paiement_id.pack(side="left", padx=(0, 15))

        tk.Label(ligne, text="Montant payé (Ar) :", bg="#f8fafc", font=("Segoe UI", 9)).pack(side="left", padx=(0, 5))
        self.entry_paiement_montant = tk.Entry(ligne, font=("Segoe UI", 10), width=12)
        self.entry_paiement_montant.pack(side="left", padx=(0, 15))

        btn_enregistrer_paiement = tk.Button(ligne, text="💾 Enregistrer le paiement", command=self._enregistrer_paiement, bg="#2563eb", fg="#ffffff", font=("Segoe UI", 9, "bold"), padx=8, pady=4, relief="flat", bd=0)
        btn_enregistrer_paiement.pack(side="left", padx=(0, 10))

        btn_marquer_paye = tk.Button(ligne, text="✅ Marquer comme payé (solde total)", command=self._marquer_comme_paye, bg="#16a34a", fg="#ffffff", font=("Segoe UI", 9, "bold"), padx=8, pady=4, relief="flat", bd=0)
        btn_marquer_paye.pack(side="left")

        tk.Label(maj, text="Astuce : cliquez sur une ligne du tableau ci-dessous pour pré-remplir l'ID et le montant payé actuel.", bg="#f8fafc", fg="#64748b", font=("Segoe UI", 8, "italic")).pack(anchor="w", padx=10, pady=(2, 10))

        # Détail des réservations avec solde
        detail = tk.LabelFrame(frame, text="Détail des réservations avec solde", bg="#f8fafc", font=("Segoe UI", 11, "bold"), fg="#475569")
        detail.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        self.table_detail_soldes = ttk.Treeview(detail, columns=("id", "client", "chambre", "debut", "fin", "montant_total", "montant_paye", "solde"), show="headings", height=6)
        for col in ("id", "client", "chambre", "debut", "fin", "montant_total", "montant_paye", "solde"):
            self.table_detail_soldes.heading(col, text=col.replace("_", " ").capitalize())
            self.table_detail_soldes.column(col, width=110, anchor="center")
        self.table_detail_soldes.pack(fill="both", expand=True, padx=10, pady=10)
        self.table_detail_soldes.bind("<<TreeviewSelect>>", self._charger_paiement_selectionne)

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
                f"{data['total_du']:,} Ar".replace(",", " "),
                f"{data['total_paye']:,} Ar".replace(",", " "),
                f"{solde:,} Ar".replace(",", " ")
            ))

        # Détail
        for r in sorted(RESERVATIONS, key=lambda x: x["nom_client"]):
            solde = max(0, r["montant_total"] - r["montant_paye"])
            self.table_detail_soldes.insert("", "end", values=(
                r["id"], r["nom_client"], r["chambre_num"], format_date_affichage(r["date_debut"]), format_date_affichage(r["date_fin"]),
                f"{r['montant_total']:,} Ar".replace(",", " "),
                f"{r['montant_paye']:,} Ar".replace(",", " "),
                f"{solde:,} Ar".replace(",", " ")
            ))

    def _charger_paiement_selectionne(self, event=None):
        selection = self.table_detail_soldes.selection()
        if not selection:
            return
        valeurs = self.table_detail_soldes.item(selection[0])["values"]
        # Colonnes : id, client, chambre, debut, fin, montant_total, montant_paye, solde
        resa_id = valeurs[0]
        montant_paye_str = str(valeurs[6]).replace("Ar", "").replace(" ", "").strip()
        self.entry_paiement_id.delete(0, tk.END)
        self.entry_paiement_id.insert(0, str(resa_id))
        self.entry_paiement_montant.delete(0, tk.END)
        self.entry_paiement_montant.insert(0, montant_paye_str)

    def _enregistrer_paiement(self):
        try:
            resa_id = int(self.entry_paiement_id.get().strip())
        except ValueError:
            messagebox.showerror("Erreur", "Veuillez indiquer un ID de réservation valide.")
            return

        try:
            nouveau_montant = float(self.entry_paiement_montant.get().strip())
        except ValueError:
            messagebox.showerror("Erreur", "Le montant payé doit être un nombre.")
            return

        reservation = next((r for r in RESERVATIONS if r["id"] == resa_id), None)
        if reservation is None:
            messagebox.showerror("Erreur", f"Aucune réservation avec l'ID {resa_id}.")
            return

        if nouveau_montant < 0:
            messagebox.showerror("Erreur", "Le montant payé ne peut pas être négatif.")
            return

        if nouveau_montant > reservation["montant_total"]:
            messagebox.showerror("Erreur", "Le montant payé ne peut pas dépasser le montant total de la réservation.")
            return

        reservation["montant_paye"] = nouveau_montant
        messagebox.showinfo("Succès", f"Paiement mis à jour pour la réservation #{resa_id} ({reservation['nom_client']}).")
        self._actualiser_toutes_les_vues()
        self._sauvegarder_donnees()

    def _marquer_comme_paye(self):
        try:
            resa_id = int(self.entry_paiement_id.get().strip())
        except ValueError:
            messagebox.showerror("Erreur", "Veuillez indiquer un ID de réservation valide.")
            return

        reservation = next((r for r in RESERVATIONS if r["id"] == resa_id), None)
        if reservation is None:
            messagebox.showerror("Erreur", f"Aucune réservation avec l'ID {resa_id}.")
            return

        reservation["montant_paye"] = reservation["montant_total"]
        self.entry_paiement_montant.delete(0, tk.END)
        self.entry_paiement_montant.insert(0, str(reservation["montant_total"]))
        messagebox.showinfo("Succès", f"Réservation #{resa_id} ({reservation['nom_client']}) marquée comme intégralement payée.")
        self._actualiser_toutes_les_vues()
        self._sauvegarder_donnees()

    # ============================================================
    # CHIFFRE D'AFFAIRES PAR CHAMBRE (MOIS EN COURS)
    # ============================================================
    def _creer_chiffre_affaires(self):
        frame = tk.Frame(self.notebook, bg="#f8fafc")
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="Chiffre d'Affaires du Mois par Chambre", font=("Segoe UI", 20, "bold"), bg="#f8fafc", fg="#0f172a").pack(pady=(15, 20))

        self.mois_ca = datetime.now().strftime("%Y-%m")

        controles = tk.Frame(frame, bg="#f8fafc")
        controles.pack(pady=(5, 15))

        btn_prec_ca = tk.Button(controles, text="◀ Mois précédent", command=self._mois_precedent_ca, bg="#e2e8f0", fg="#475569", font=("Segoe UI", 9, "bold"))
        btn_prec_ca.pack(side="left", padx=10)

        self.label_mois_ca = tk.Label(controles, text=self.mois_ca, bg="#f8fafc", fg="#0f172a", font=("Segoe UI", 14, "bold"), width=15)
        self.label_mois_ca.pack(side="left", padx=20)

        btn_suiv_ca = tk.Button(controles, text="Mois suivant ▶", command=self._mois_suivant_ca, bg="#e2e8f0", fg="#475569", font=("Segoe UI", 9, "bold"))
        btn_suiv_ca.pack(side="left", padx=10)

        btn_ce_mois_ca = tk.Button(controles, text="Mois en cours", command=self._mois_courant_ca, bg="#2563eb", fg="#ffffff", font=("Segoe UI", 9, "bold"))
        btn_ce_mois_ca.pack(side="left", padx=(20, 0))

        table_frame = tk.LabelFrame(frame, text="Chiffre d'affaires du mois", bg="#f8fafc", font=("Segoe UI", 11, "bold"), fg="#475569")
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.table_chiffre = ttk.Treeview(table_frame, columns=("num", "nom", "ca_mois", "nb_resa_mois"), show="headings", height=12)
        for col in ("num", "nom", "ca_mois", "nb_resa_mois"):
            self.table_chiffre.heading(col, text=col.replace("_", " ").capitalize())
            self.table_chiffre.column(col, width=180, anchor="center")
        self.table_chiffre.pack(fill="both", expand=True, padx=10, pady=10)

        return frame

    def _mois_precedent_ca(self):
        annee, mois = map(int, self.mois_ca.split("-"))
        mois -= 1
        if mois == 0:
            mois = 12
            annee -= 1
        self.mois_ca = f"{annee}-{mois:02d}"
        self.label_mois_ca.config(text=self.mois_ca)
        self._actualiser_chiffre()

    def _mois_suivant_ca(self):
        annee, mois = map(int, self.mois_ca.split("-"))
        mois += 1
        if mois == 13:
            mois = 1
            annee += 1
        self.mois_ca = f"{annee}-{mois:02d}"
        self.label_mois_ca.config(text=self.mois_ca)
        self._actualiser_chiffre()

    def _mois_courant_ca(self):
        self.mois_ca = datetime.now().strftime("%Y-%m")
        self.label_mois_ca.config(text=self.mois_ca)
        self._actualiser_chiffre()

    def _actualiser_chiffre(self):
        for item in self.table_chiffre.get_children():
            self.table_chiffre.delete(item)
        for ch in CHAMBRES:
            ca = 0
            nb = 0
            for r in RESERVATIONS:
                if r["chambre_num"] == ch["numero"] and r["date_debut"][:7] == self.mois_ca:
                    ca += r["montant_total"]
                    nb += 1
            self.table_chiffre.insert("", "end", values=(
                ch["numero"],
                ch["nom"],
                f"{ca:,} Ar".replace(",", " "),
                nb
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
                r["id"], r["nom_client"], r["chambre_num"], format_date_affichage(r["date_debut"]), format_date_affichage(r["date_fin"]),
                f"{r['montant_total']:,} Ar".replace(",", " "), f"{r['montant_paye']:,} Ar".replace(",", " "),
                f"{solde:,} Ar".replace(",", " ")
            ))
        self._afficher_mois()
        self._actualiser_historique()
        self._actualiser_paiements()
        self._actualiser_chiffre()
        self.status.config(text=f"Actualisé • {len(RESERVATIONS)} réservation(s) • Données SQLite (chambres.db) • {self.date_aujourd_hui}")

    # ============================================================
    # RÉINITIALISER
    # ============================================================
    def _reinitialiser_donnees(self):
        if messagebox.askyesno(
            "Confirmation",
            "Voulez-vous réinitialiser TOUTES les données (chambres ET réservations) "
            "aux valeurs de départ ? Cette action est irréversible."
        ):
            CHAMBRES.clear()
            CHAMBRES.extend([
                {"numero": 101, "nom": "Chambre du Jardin", "type": "Double", "prix_nuit": 85},
                {"numero": 102, "nom": "Chambre de la Mer", "type": "Double", "prix_nuit": 95},
                {"numero": 103, "nom": "Suite Royale", "type": "Suite", "prix_nuit": 140},
                {"numero": 104, "nom": "Chambre des Oliviers", "type": "Simple", "prix_nuit": 65},
                {"numero": 105, "nom": "Chambre du Lac", "type": "Double", "prix_nuit": 90},
            ])
            RESERVATIONS.clear()
            RESERVATIONS.extend([
                {"id": 1, "nom_client": "Marie Dupont", "chambre_num": 101, "date_debut": "2026-07-10", "date_fin": "2026-07-15", "montant_paye": 200, "montant_total": 425},
                {"id": 2, "nom_client": "Jean Lefebvre", "chambre_num": 102, "date_debut": "2026-07-14", "date_fin": "2026-07-20", "montant_paye": 300, "montant_total": 570},
                {"id": 3, "nom_client": "Claire Martin", "chambre_num": 103, "date_debut": "2026-07-18", "date_fin": "2026-07-25", "montant_paye": 700, "montant_total": 980},
            ])
            global next_id
            next_id = 4
            self.combo_chambre.config(values=[f"Chambre {c['numero']} - {c['nom']}" for c in CHAMBRES])
            self._nouvelle_reservation_form()
            self._actualiser_toutes_les_vues()
            self._sauvegarder_donnees()
            messagebox.showinfo("Réinitialisé", "Les chambres et les réservations ont été restaurées aux valeurs initiales.")

    def _get_db_path(self):
        import sys, os
        if getattr(sys, 'frozen', False):
            return os.path.join(os.path.dirname(sys.executable), "chambres.db")
        else:
            return os.path.join(os.path.dirname(os.path.abspath(__file__)), "chambres.db")

    def _migrer_schema_reservations(self, cursor, conn):
        """Ajoute les colonnes remise_pourcentage / remise_montant si elles n'existent pas encore
        (bases créées avant ces fonctionnalités)."""
        cursor.execute("PRAGMA table_info(reservations)")
        colonnes = [col[1] for col in cursor.fetchall()]
        if "remise_pourcentage" not in colonnes:
            cursor.execute("ALTER TABLE reservations ADD COLUMN remise_pourcentage REAL DEFAULT 0")
            conn.commit()
        if "remise_montant" not in colonnes:
            cursor.execute("ALTER TABLE reservations ADD COLUMN remise_montant REAL DEFAULT 0")
            conn.commit()

    def _init_db(self):
        import sqlite3
        conn = None
        try:
            conn = sqlite3.connect(self._get_db_path())
            cursor = conn.cursor()
            cursor.execute('CREATE TABLE IF NOT EXISTS chambres (numero INTEGER PRIMARY KEY, nom TEXT, type TEXT, prix_nuit REAL)')
            cursor.execute('CREATE TABLE IF NOT EXISTS reservations (id INTEGER PRIMARY KEY AUTOINCREMENT, nom_client TEXT, chambre_num INTEGER, date_debut TEXT, date_fin TEXT, montant_total REAL, montant_paye REAL, remise_pourcentage REAL DEFAULT 0, remise_montant REAL DEFAULT 0)')
            self._migrer_schema_reservations(cursor, conn)
            conn.commit()
        except sqlite3.Error as e:
            messagebox.showerror(
                "Erreur de base de données",
                f"Impossible d'initialiser chambres.db.\nDétail : {e}\n\n"
                "Les données ne pourront pas être sauvegardées tant que ce problème n'est pas résolu."
            )
        finally:
            if conn is not None:
                conn.close()

    def _sauvegarder_donnees(self):
        import sqlite3
        conn = None
        try:
            conn = sqlite3.connect(self._get_db_path())
            cursor = conn.cursor()
            self._migrer_schema_reservations(cursor, conn)
            cursor.execute("DELETE FROM chambres")
            for ch in CHAMBRES:
                cursor.execute("INSERT INTO chambres VALUES (?, ?, ?, ?)", (ch["numero"], ch["nom"], ch["type"], ch["prix_nuit"]))
            cursor.execute("DELETE FROM reservations")
            for r in RESERVATIONS:
                cursor.execute(
                    "INSERT INTO reservations (id, nom_client, chambre_num, date_debut, date_fin, montant_total, montant_paye, remise_pourcentage, remise_montant) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (r["id"], r["nom_client"], r["chambre_num"], r["date_debut"], r["date_fin"], r["montant_total"], r["montant_paye"], r.get("remise_pourcentage", 0), r.get("remise_montant", 0))
                )
            conn.commit()
        except sqlite3.Error as e:
            if conn is not None:
                conn.rollback()
            messagebox.showerror(
                "Erreur de sauvegarde",
                "Impossible d'enregistrer les données dans chambres.db.\n"
                f"Détail : {e}\n\n"
                "Vos modifications restent visibles dans l'application, mais ne seront pas "
                "conservées si vous fermez le programme tant que ce problème n'est pas résolu "
                "(vérifiez par exemple l'espace disque ou les droits d'écriture du dossier)."
            )
        finally:
            if conn is not None:
                conn.close()

    def _charger_donnees(self):
        import sqlite3, os, sys
        db_path = self._get_db_path()
        # Si le .db intégré dans le .exe existe (sys._MEIPASS) mais pas dans le répertoire du .exe, le copier
        meipass_db = os.path.join(getattr(sys, '_MEIPASS', ''), "chambres.db") if getattr(sys, 'frozen', False) else ""
        if meipass_db and os.path.exists(meipass_db) and not os.path.exists(db_path):
            import shutil
            shutil.copy(meipass_db, db_path)
        if not os.path.exists(db_path):
            self._init_db()
            return
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            self._migrer_schema_reservations(cursor, conn)
            cursor.execute("SELECT * FROM chambres")
            rows = cursor.fetchall()
            global CHAMBRES, RESERVATIONS, next_id
            CHAMBRES.clear()
            for row in rows:
                CHAMBRES.append({"numero": row[0], "nom": row[1], "type": row[2], "prix_nuit": row[3]})
            cursor.execute("SELECT id, nom_client, chambre_num, date_debut, date_fin, montant_total, montant_paye, remise_pourcentage, remise_montant FROM reservations")
            rows = cursor.fetchall()
            RESERVATIONS.clear()
            for row in rows:
                RESERVATIONS.append({"id": row[0], "nom_client": row[1], "chambre_num": row[2], "date_debut": row[3], "date_fin": row[4], "montant_total": row[5], "montant_paye": row[6], "remise_pourcentage": row[7] or 0, "remise_montant": row[8] or 0})
            next_id = max([r["id"] for r in RESERVATIONS] + [0]) + 1
            conn.close()
            if hasattr(self, 'combo_chambre'):
                self.combo_chambre.config(values=[f"Chambre {c['numero']} - {c['nom']}" for c in CHAMBRES])
        except sqlite3.Error as e:
            messagebox.showwarning(
                "Erreur de chargement",
                f"Impossible de charger chambres.db.\nDétail : {e}\n\n"
                "L'application démarre avec les données par défaut en mémoire. "
                "Vos anciennes données ne seront pas modifiées tant que vous n'enregistrez rien."
            )

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
