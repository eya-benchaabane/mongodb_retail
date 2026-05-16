from pymongo import MongoClient
import json

# ============================================================
# CONNEXION
# ============================================================

client = MongoClient("mongodb://localhost:27017/")
db = client["online_retail"]

print(" Connecté à MongoDB\n")

# ============================================================
# PIPELINE 1 : Quel pays achète le plus ?
# → On groupe les orders par pays et on calcule les totaux
# ============================================================

print("=" * 60)
print(" PIPELINE 1 : Classement des pays par chiffre d'affaires")
print("=" * 60)

pipeline_1 = [
    # Étape 1 : grouper par pays
    {
        "$group": {
            "_id": {
                "code": "$country.code",
                "name": "$country.name"
            },
            "totalRevenue"  : {"$sum": "$orderTotal"},    # CA total
            "totalOrders"   : {"$sum": 1},                # nb commandes
            "avgOrderValue" : {"$avg": "$orderTotal"},    # panier moyen
            "totalItems"    : {"$sum": "$itemCount"}      # nb articles
        }
    },
    # Étape 2 : trier par CA décroissant
    {"$sort": {"totalRevenue": -1}},
    # Étape 3 : garder les 10 premiers
    {"$limit": 10},
    # Étape 4 : reformater la sortie
    {
        "$project": {
            "_id"          : 0,
            "pays"         : "$_id.name",
            "code"         : "$_id.code",
            "totalRevenue" : {"$round": ["$totalRevenue", 2]},
            "totalOrders"  : 1,
            "avgOrderValue": {"$round": ["$avgOrderValue", 2]},
            "totalItems"   : 1
        }
    }
]

results_1 = list(db["orders"].aggregate(pipeline_1))
for r in results_1:
    print(f"  🌍 {r['pays']:<25} | CA: £{r['totalRevenue']:>10,.2f} | Commandes: {r['totalOrders']:>5} | Panier moyen: £{r['avgOrderValue']:>8.2f}")

# ============================================================
# PIPELINE 2 : Quel profil de client par pays ?
# → On analyse âge, sexe, profession des clients par pays
# ============================================================

print("\n" + "=" * 60)
print("👤 PIPELINE 2 : Profil client par pays")
print("=" * 60)

pipeline_2 = [
    # Exclut les clients anonymes
    {"$match": {"_id": {"$ne": 0}}},
    {
        "$group": {
            "_id"           : "$country.name",
            "nbClients"     : {"$sum": 1},
            "ageMoyen"      : {"$avg": "$age"},
            # Compte hommes et femmes
            "nbHommes"      : {"$sum": {"$cond": [{"$eq": ["$sexe", "M"]}, 1, 0]}},
            "nbFemmes"      : {"$sum": {"$cond": [{"$eq": ["$sexe", "F"]}, 1, 0]}},
            "depenseMoyenne": {"$avg": "$stats.totalSpent"}
        }
    },
    {"$sort": {"nbClients": -1}},
    {"$limit": 10},
    {
        "$project": {
            "_id"           : 0,
            "pays"          : "$_id",
            "nbClients"     : 1,
            "ageMoyen"      : {"$round": ["$ageMoyen", 1]},
            "nbHommes"      : 1,
            "nbFemmes"      : 1,
            "depenseMoyenne": {"$round": ["$depenseMoyenne", 2]}
        }
    }
]

results_2 = list(db["clients"].aggregate(pipeline_2))
for r in results_2:
    print(f"  👤 {r['pays']:<25} | Clients: {r['nbClients']:>4} | Age moyen: {r['ageMoyen']:>5} | H: {r['nbHommes']:>3} F: {r['nbFemmes']:>3} | Dépense moy: £{r['depenseMoyenne']:>8.2f}")

# ============================================================
# PIPELINE 3 : Quelle catégorie de produit par pays ?
# → On déroule les items[] et on groupe par pays + catégorie
# ============================================================

print("\n" + "=" * 60)
print("🛒 PIPELINE 3 : Catégorie préférée par pays")
print("=" * 60)

pipeline_3 = [
    # Deroule le tableau items[] → une ligne par item
    {"$unwind": "$items"},
    {
        "$group": {
            "_id": {
                "pays"    : "$country.name",
                "categorie": "$items.category"
            },
            "totalQty"    : {"$sum": "$items.quantity"},
            "totalRevenue": {"$sum": "$items.lineTotal"}
        }
    },
    {"$sort": {"totalQty": -1}},
    # Regroupe par pays pour garder la catégorie top 1
    {
        "$group": {
            "_id"             : "$_id.pays",
            "categorieTop"    : {"$first": "$_id.categorie"},
            "qtyTop"          : {"$first": "$totalQty"},
            "revenueTop"      : {"$first": "$totalRevenue"}
        }
    },
    {"$sort": {"qtyTop": -1}},
    {"$limit": 10},
    {
        "$project": {
            "_id"         : 0,
            "pays"        : "$_id",
            "categorieTop": 1,
            "qtyTop"      : 1,
            "revenueTop"  : {"$round": ["$revenueTop", 2]}
        }
    }
]

results_3 = list(db["orders"].aggregate(pipeline_3))
for r in results_3:
    print(f"  🛒 {r['pays']:<25} | Catégorie: {r['categorieTop']:<20} | Qté: {r['qtyTop']:>6} | CA: £{r['revenueTop']:>10,.2f}")

# ============================================================
# PIPELINE 4 : Générer country_stats avec $out
# → Résultat sauvegardé comme collection dans MongoDB
# ============================================================

print("\n" + "=" * 60)
print("📊 PIPELINE 4 : Génération de country_stats")
print("=" * 60)

pipeline_4 = [
    {"$group": {
        "_id"          : {
            "code": "$country.code",
            "name": "$country.name"
        },
        "totalRevenue" : {"$sum": "$orderTotal"},
        "totalOrders"  : {"$sum": 1},
        "avgOrderValue": {"$avg": "$orderTotal"},
        "totalItems"   : {"$sum": "$itemCount"}
    }},
    {"$sort": {"totalRevenue": -1}},
    {
        "$project": {
            "_id"          : 0,
            "code"         : "$_id.code",
            "name"         : "$_id.name",
            "totalRevenue" : {"$round": ["$totalRevenue", 2]},
            "totalOrders"  : 1,
            "avgOrderValue": {"$round": ["$avgOrderValue", 2]},
            "totalItems"   : 1
        }
    },
    # Sauvegarde le résultat dans une nouvelle collection
    {"$out": "country_stats"}
]

db["orders"].aggregate(pipeline_4)
count = db["country_stats"].count_documents({})
print(f"✅ country_stats générée : {count} pays")

print("\n📄 Top 5 pays :")
for r in db["country_stats"].find().sort("totalRevenue", -1).limit(5):
    print(f"  🌍 {r['name']:<25} | CA: £{r['totalRevenue']:>10,.2f} | Commandes: {r['totalOrders']:>5}")

client.close()
print("\n✅ Toutes les agrégations terminées !")