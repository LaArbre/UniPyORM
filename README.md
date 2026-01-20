# PyCrossORM

Un ORM Python complet pour SQLite et MySQL, conçu pour être sûr, robuste et polyvalent.
Il permet de définir des modèles, gérer les types SQL et les relations, et créer des vues sécurisées en lecture seule.

## Table des matières
- Présentation
- Fonctionnalités
- Installation
- Utilisation
- Exemples de scripts
- Contribution
- Roadmap
- Licence

## Présentation
PyCrossORM est un ORM Python permettant de travailler avec SQLite et MySQL avec validation automatique des types, gestion des relations et vues sécurisées.
Il vise à fournir une interface simple et sûre pour la manipulation des bases de données sans permettre l'exécution de requêtes arbitraires.

## Fonctionnalités
- Définition de modèles avec types forts (INTEGER, TEXT, REAL, BOOLEAN, DATETIME, JSON, ForeignKey)
- Validation automatique des types et valeurs par défaut
- Gestion automatique des clés primaires et des relations (ForeignKey)
- Journalisation des actions CRUD dans une base dédiée
- Système de vues avec jointures limitées et lecture seule après validation
- Compatible SQLite et MySQL
- Configuration via fichier `.env`

## Installation
```bash
git clone https://github.com/<votre_utilisateur>/PyCrossORM.git
cd PyCrossORM
pip install -r requirements.txt
```

### Configuration avec `.env`
```ini
# Pour SQLite
DB_BASE_PATH=local.db
DB_LOG_PATH=logs.db

# Pour MySQL
DB_SQL=1
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=
DB_NAME=ma_base
```

* `DB_SQL` = 1 pour MySQL, sinon SQLite
* `DB_BASE_PATH` = chemin vers votre fichier SQLite
* `DB_LOG_PATH` = chemin vers la base de logs
* `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` = infos de connexion MySQL

## Utilisation

### Définir un modèle

```python
from UniPyORM import Model, INTEGER, TEXT, BOOLEAN, DATETIME, JSON, ForeignKey


class Utilisateur(Model):
    id = INTEGER(primary_key=True)
    pseudo = TEXT(unique=True, not_null=True)
    email = TEXT(not_null=True)
    date_inscription = DATETIME(default=lambda: datetime.now())
```

### Créer et manipuler des objets
```python
user = Utilisateur.new(pseudo="alice", email="alice@example.com")
user.age = 25
user.save()

retrieved = Utilisateur.get(pseudo="alice")
print(retrieved.email)
```

### Créer une vue avec jointures sécurisées

```python
from UniPyORM.view import View

ArticlesAvecAuteur = (
    View(Article)
    .select(Article, ["id", "titre", "prix"])
    .join(lambda row: (row.auteur.id, ["pseudo", "email"]))
)

view_data = ArticlesAvecAuteur.validate()
for row in view_data:
    print(row["titre"], row["pseudo"], row["email"])
```

## Licence
MIT License

