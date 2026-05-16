import pandas as pd
import json

# ============================================================
# ÉTAPE 1 : CHARGEMENT
# ============================================================

df = pd.read_csv("data/online_retail_enriched.csv", encoding="utf-8", low_memory=False)

# Nettoyage de base
df = df.dropna(subset=["InvoiceNo", "StockCode"])
df["CustomerID"] = pd.to_numeric(df["CustomerID"], errors="coerce").fillna(0).astype(int)
df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
df["LineTotal"] = df["Quantity"] * df["UnitPrice"]
# Diagnostic
print("Valeurs nulles dans UnitPrice :", df["UnitPrice"].isna().sum())
print("Valeurs nulles dans Quantity  :", df["Quantity"].isna().sum())
print("Lignes avec LineTotal <= 0    :", len(df[df["LineTotal"] <= 0]))
print("Exemple lignes problématiques :")
print(df[df["LineTotal"] <= 0][["InvoiceNo", "CustomerID", "Quantity", "UnitPrice", "LineTotal"]].head(10))
# On exclut les clients anonymes (CustomerID = 0)
df = df[df["CustomerID"] != 0]

print(f" Transactions après exclusion anonymes : {len(df)}")

# ============================================================
# ÉTAPE 2 : CALCUL DES STATS PAR CLIENT
# ============================================================
# Pour chaque client on calcule :
# - Nombre total de commandes
# - Total dépensé
# - Valeur moyenne par commande
# - Catégorie préférée
# - Date de dernière commande

clients = []
grouped = df.groupby("CustomerID")
total = len(grouped)

for i, (customer_id, group) in enumerate(grouped):

    if i % 500 == 0:
        print(f"   {i}/{total} clients traités...")

    # Première ligne pour les infos du profil client
    first = group.iloc[0]

    # ── Calcul des stats ─────────────────────────────────────

    # Commandes uniques
    commandes = group["InvoiceNo"].nunique()

    # Total dépensé
    total_depense = round(float(group["LineTotal"].sum()), 2)

    # Valeur moyenne par commande
    avg_commande = round(total_depense / commandes, 2) if commandes > 0 else 0

    # Catégorie la plus achetée (en quantité)
    categorie_preferee = (
        group.groupby("Categorie")["Quantity"]
        .sum()
        .idxmax()
        if "Categorie" in group.columns
        else "Unknown"
    )

    # Date de la dernière commande
    derniere_commande = group["InvoiceDate"].max().isoformat()

    # ── Construction du document client ──────────────────────
    client = {
        # _id = CustomerID unique
        "_id": int(customer_id),

        # Profil client → répond à "QUI est le client ?"
        "nom"         : str(first.get("Nom", "Inconnu")),
        "prenom"      : str(first.get("Prenom", "Inconnu")),
        "age"         : int(first["Age"]) if pd.notna(first.get("Age")) else 0,
        "sexe"        : str(first.get("Sexe", "N")),
        "adresse"     : str(first.get("Adresse", "Inconnue")) if "Adresse" in first else "Inconnue",
        "ville"       : str(first.get("Ville", "Inconnue")),
        "profession"  : str(first.get("Profession", "Inconnue")),
        "statutClient": str(first.get("StatutClient", "Inconnue")),

        # Pays du client
        "country": {
            "code": str(first.get("CodePays", "")),
            "name": str(first.get("NomPays", ""))
        },

        # Stats pré-calculées → répond à "COMBIEN dépense-t-il ?"
        "stats": {
            "totalOrders"      : int(commandes),
            "totalSpent"       : total_depense,
            "avgOrderValue"    : avg_commande,
            "favoriteCategory" : str(categorie_preferee),
            "lastOrderDate"    : derniere_commande
        }
    }

    clients.append(client)

# ============================================================
# ÉTAPE 3 : SAUVEGARDE EN JSON
# ============================================================

with open("data/clients.json", "w", encoding="utf-8") as f:
    json.dump(clients, f, ensure_ascii=False, indent=2)

print(f"\n {len(clients)} documents clients générés → data/clients.json")
print(f"\n Exemple du premier document :")
print(json.dumps(clients[0], indent=2, ensure_ascii=False))