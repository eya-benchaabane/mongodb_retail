import pandas as pd
import json

# ============================================================
# ÉTAPE 1 : CHARGEMENT DES FICHIERS CSV
# ============================================================

# low_memory=False : lit tout le fichier d'un coup pour éviter
# le warning "mixed types" sur les colonnes mixtes
df = pd.read_csv("data/online_retail_enriched.csv", encoding="utf-8", low_memory=False)
avis_df = pd.read_csv("data/avis.csv", encoding="utf-8")

print(f" Transactions chargées : {len(df)}")
print(f" Avis chargés : {len(avis_df)}")

# ============================================================
# ÉTAPE 2 : NETTOYAGE DES DONNÉES
# ============================================================

# Supprime les lignes sans InvoiceNo ou StockCode (données inutilisables)
df = df.dropna(subset=["InvoiceNo", "StockCode"])

# CustomerID peut contenir "ANONYME" → on le convertit en 0
# errors="coerce" : transforme les valeurs non numériques en NaN
# fillna(0)       : remplace NaN par 0
df["CustomerID"] = pd.to_numeric(df["CustomerID"], errors="coerce").fillna(0).astype(int)

# Convertit la date en format datetime pour pouvoir l'utiliser
df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])

# Calcule le total de chaque ligne : Quantité × Prix unitaire
df["LineTotal"] = df["Quantity"] * df["UnitPrice"]

print(f" Nettoyage terminé : {len(df)} lignes valides")

# ============================================================
# ÉTAPE 3 : PRÉ-INDEXATION DES AVIS (optimisation)
# ============================================================
# But : éviter de parcourir tout le fichier avis pour chaque item
# On crée un dictionnaire avec clé = (InvoiceNo, StockCode)
# Accès instantané au lieu de O(n×m) opérations

avis_index = {}
for _, row in avis_df.iterrows():
    # La clé unique identifie un avis : numéro facture + code produit
    key = (str(row["InvoiceNo"]), str(row["StockCode"]))
    avis_index[key] = {
        "note"        : int(row["Note"]),
        "commentaire" : str(row["Commentaire"]),
        "dateAvis"    : str(row["DateAvis"])
    }

print(f" Avis indexés : {len(avis_index)}")

# ============================================================
# ÉTAPE 4 : TRANSFORMATION CSV → DOCUMENTS MONGODB
# ============================================================
# Principe : grouper toutes les lignes d'une même facture
# pour créer UN seul document avec un tableau items[]
#
# CSV (lignes plates)          →    Document MongoDB
# ─────────────────────────────────────────────────
# 536365 | 85123A | John | 6        {
# 536365 | 71053  | John | 4   →      "_id": "536365",
# 536365 | 22752  | John | 2          "items": [...],
#                                     "orderTotal": 50.20
#                                    }

orders = []
grouped = df.groupby("InvoiceNo")  # groupe par numéro de facture
total = len(grouped)

for i, (invoice_no, group) in enumerate(grouped):

    # Affiche la progression toutes les 1000 factures
    if i % 1000 == 0:
        print(f"   {i}/{total} factures traitées...")

    # Prend la première ligne du groupe pour les infos communes
    # (client, pays, date) — elles sont identiques dans tout le groupe
    first = group.iloc[0]

    # ── Construction du tableau items[] ──────────────────────
    items = []
    for _, row in group.iterrows():

        # Informations de base du produit
        item = {
            "stockCode"  : str(row["StockCode"]),
            "description": str(row["Description"]),
            "category"   : str(row.get("Categorie", "Unknown")),
            "quantity"   : int(row["Quantity"]),
            "unitPrice"  : float(row["UnitPrice"]),
            "lineTotal"  : round(float(row["LineTotal"]), 2)
        }

        # Cherche si cet item a un avis dans le dictionnaire
        # Accès en O(1) : instantané peu importe la taille du fichier
        key = (str(invoice_no), str(row["StockCode"]))
        if key in avis_index:
            item["review"] = avis_index[key]  # embarque l'avis dans l'item

        items.append(item)

    # ── Construction du document order complet ────────────────
    order = {
        # _id = identifiant unique du document dans MongoDB
        "_id"        : str(invoice_no),
        "invoiceDate": first["InvoiceDate"].isoformat(),
        "status"     : str(first.get("Statut", "NORMAL")),

        # Informations client embarquées dans la commande
        # → permet de répondre à "QUI achète ?" sans jointure
        "customer": {
            "customerId"  : int(first["CustomerID"]),
            "nom"         : str(first.get("Nom", "Inconnu")),
            "prenom"      : str(first.get("Prenom", "Inconnu")),
            "age"         : int(first["Age"]) if pd.notna(first.get("Age")) else 0,
            "sexe"        : str(first.get("Sexe", "N")),
            "profession"  : str(first.get("Profession", "Inconnue")),
            "statutClient": str(first.get("StatutClient", "Inconnue")),
            "ville"       : str(first.get("Ville", "Inconnue"))
        },

        # Pays embarqué → permet de filtrer par pays sans jointure
        "country": {
            "code": str(first.get("CodePays", "")),
            "name": str(first.get("NomPays", ""))
        },

        # Tableau des produits achetés → répond à "QUOI ?"
        "items": items,

        # Totaux pré-calculés → répond à "COMBIEN ?"
        "orderTotal": round(float(group["LineTotal"].sum()), 2),
        "itemCount" : int(group["Quantity"].sum())
    }

    orders.append(order)

# ============================================================
# ÉTAPE 5 : SAUVEGARDE EN JSON
# ============================================================
# Crée le fichier orders.json prêt à importer dans MongoDB

with open("data/orders.json", "w", encoding="utf-8") as f:
    json.dump(orders, f, ensure_ascii=False, indent=2)

print(f"\n {len(orders)} documents orders générés → data/orders.json")
print(f"\nExemple du premier document :")
print(json.dumps(orders[0], indent=2, ensure_ascii=False))