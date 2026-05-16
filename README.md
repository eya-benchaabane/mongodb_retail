---

## Collections MongoDB

### `orders` — 25 900 documents
```json
{
  "_id": "536365",
  "invoiceDate": "2010-12-01T08:26:00",
  "customer": {
    "customerId": 17850,
    "nom": "Burns",
    "age": 43,
    "sexe": "M",
    "profession": "Avocat"
  },
  "country": { "code": "GBR", "name": "United Kingdom" },
  "items": [
    {
      "stockCode": "85123A",
      "description": "WHITE HANGING HEART",
      "category": "Home Decor",
      "quantity": 6,
      "unitPrice": 2.55,
      "lineTotal": 15.30,
      "review": { "note": 4, "commentaire": "Super produit !" }
    }
  ],
  "orderTotal": 139.12,
  "itemCount": 25
}
```

### `clients` — 4 372 documents
```json
{
  "_id": 17850,
  "nom": "Burns",
  "age": 43,
  "sexe": "M",
  "profession": "Avocat",
  "country": { "code": "GBR", "name": "United Kingdom" },
  "stats": {
    "totalOrders": 12,
    "totalSpent": 450.20,
    "avgOrderValue": 37.52,
    "favoriteCategory": "Home Decor",
    "lastOrderDate": "2011-11-15T00:00:00"
  }
}
```

### `country_stats` — générée automatiquement
Créée par le pipeline `$out` — pas de création manuelle.

---

##  Installation

### Prérequis
- Python 3.11+
- MongoDB 7.x (local)
- MongoDB Compass (interface graphique)

### Installer les dépendances
```bash
pip install pymongo pandas
```

---

##  Lancement

```bash
# Étape 1 : Transformer les commandes
python 01_transform_orders.py

# Étape 2 : Transformer les clients
python 02_transform_clients.py

# Étape 3 : Importer dans MongoDB
python 03_import_mongodb.py

# Étape 4 : Lancer les agrégations
python 04_aggregations.py
```

---

##  Résultats

### Top 5 pays par CA
| Pays | CA (GBP) | Commandes |
|---|---|---|
| United Kingdom | 8 127 499 | 23 494 |
| Netherlands | 284 661 | 101 |
| EIRE | 261 773 | 360 |
| Germany | 221 004 | 603 |
| France | 197 207 | 461 |

### Catégorie préférée par pays
| Pays | Catégorie |
|---|---|
| UK, Netherlands, EIRE, Germany | Clothing |
| France, Australie | Home Decor |
| Suède | Books |
| Japon | Kitchen |

---

##  Modélisation

| Concept | Appliqué à | Raison |
|---|---|---|
| **Imbrication** | `customer`, `country`, `items[]`, `review` | Accès rapide sans jointure |
| **Référence** | `customerId`, `stockCode` | Lien vers document complet |

---

##  Technologies

![Python](https://img.shields.io/badge/Python-3.11-blue)
![MongoDB](https://img.shields.io/badge/MongoDB-7.x-green)
![Pandas](https://img.shields.io/badge/Pandas-latest-orange)
![PyMongo](https://img.shields.io/badge/PyMongo-latest-green)

---

##  Dataset

- **Source** : [Online Retail Dataset - UCI](https://archive.ics.uci.edu/ml/datasets/online+retail)
- **Enrichissement** : Données clients (Nom, Age, Sexe, Profession)
  et produits (Catégorie, Note Moyenne) ajoutées
- **Période** : Décembre 2010 — Décembre 2011
- **Pays** : 38 pays analysés
