import json
from pymongo import MongoClient, errors

# ============================================================
# ÉTAPE 1 : CONNEXION À MONGODB
# ============================================================
# On se connecte à MongoDB en local (port par défaut 27017)

client = MongoClient("mongodb://localhost:27017/")
db = client["online_retail"]  # nom de la base de données

print(" Connecté à MongoDB")
print(f" Base de données : online_retail")

# ============================================================
# ÉTAPE 2 : CHARGEMENT DES FICHIERS JSON
# ============================================================

with open("data/orders.json", "r", encoding="utf-8") as f:
    orders = json.load(f)

with open("data/clients.json", "r", encoding="utf-8") as f:
    clients = json.load(f)

print(f" Orders à importer  : {len(orders)}")
print(f" Clients à importer : {len(clients)}")

# ============================================================
# ÉTAPE 3 : IMPORT COLLECTION ORDERS
# ============================================================
# On supprime la collection si elle existe déjà
# pour éviter les doublons en cas de re-import

print("\n Import des orders...")

db["orders"].drop()  # supprime la collection existante

try:
    result = db["orders"].insert_many(orders, ordered=False)
    print(f" {len(result.inserted_ids)} orders importés")
except errors.BulkWriteError as e:
    print(f"  Orders importés avec quelques erreurs : {e.details['nInserted']} insérés")

# ============================================================
# ÉTAPE 4 : IMPORT COLLECTION CLIENTS
# ============================================================

print("\n⏳ Import des clients...")

db["clients"].drop()  # supprime la collection existante

try:
    result = db["clients"].insert_many(clients, ordered=False)
    print(f" {len(result.inserted_ids)} clients importés")
except errors.BulkWriteError as e:
    print(f"  Clients importés avec quelques erreurs : {e.details['nInserted']} insérés")

# ============================================================
# ÉTAPE 5 : CRÉATION DES INDEX
# ============================================================
# Les index accélèrent les requêtes fréquentes
# Sans index : MongoDB parcourt tous les documents (lent)
# Avec index : accès direct (rapide)

print("\n Création des index...")

# Index sur orders
db["orders"].create_index("customer.customerId")   # chercher par client
db["orders"].create_index("country.code")          # filtrer par pays
db["orders"].create_index("invoiceDate")           # trier par date
db["orders"].create_index("orderTotal")            # trier par montant

# Index sur clients
db["clients"].create_index("country.code")         # filtrer par pays
db["clients"].create_index("stats.totalSpent")     # trier par dépense
db["clients"].create_index("profession")           # filtrer par profession

print(" Index créés")

# ============================================================
# ÉTAPE 6 : VÉRIFICATION
# ============================================================

print("\n Vérification finale :")
print(f"  orders  : {db['orders'].count_documents({})} documents")
print(f"  clients : {db['clients'].count_documents({})} documents")

print("\n Exemple order :")
print(db["orders"].find_one({}, {"_id": 1, "country": 1, "orderTotal": 1, "customer.nom": 1}))

print("\n Exemple client :")
print(db["clients"].find_one({}, {"_id": 1, "nom": 1, "country": 1, "stats": 1}))

client.close()
print("\n Import terminé avec succès !")