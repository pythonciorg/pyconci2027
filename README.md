# 🐍 PyCon Côte d'Ivoire 2027 — Backend

> API back-end officielle de **PyCon Côte d'Ivoire 2027**, construite avec **FastAPI**.
> Billetterie, appel à conférences (CFP), paiement en ligne, génération de billets, programme, blog, multilinguisme et back-office administrateur.

**Site officiel :** [https://pycon.ci/](https://pycon.ci/)

---

## 📑 Sommaire

- [Aperçu](#-aperçu)
- [Stack technique](#-stack-technique)
- [Architecture du projet](#-architecture-du-projet)
- [Prérequis](#-prérequis)
- [Installation](#-installation)
- [Variables d'environnement](#-variables-denvironnement)
- [Lancer le projet](#-lancer-le-projet)
- [Documentation de l'API](#-documentation-de-lapi)
- [Modules fonctionnels](#-modules-fonctionnels)
- [Authentification & rôles](#-authentification--rôles)
- [Modèle de gestion des quotas](#-modèle-de-gestion-des-quotas-billetterie)
- [Multilinguisme (FR / EN)](#-multilinguisme-fr--en)
- [Sécurité](#-sécurité)
- [Sauvegardes automatisées](#-sauvegardes-automatisées)
- [Tests automatisés](#-tests-automatisés)
- [Migrations de base de données](#-migrations-de-base-de-données)
- [Intégration front-end](#-intégration-front-end)
- [Liste complète des endpoints](#-liste-complète-des-endpoints)
- [État du projet](#-état-du-projet)

---

## 🔎 Aperçu

Ce dépôt contient l'intégralité du back-end de l'événement PyCon Côte d'Ivoire 2027 : de l'inscription des participants à la génération des billets, en passant par la gestion des propositions de conférences (CFP), le paiement en ligne, le programme, le blog et le back-office administrateur.

Le projet est **entièrement conteneurisé** (API, base de données, sauvegardes) et pensé pour être consommé par un **front-end séparé** (React), développé en parallèle par une autre équipe.

---

## 🧱 Stack technique

| Composant | Technologie |
|---|---|
| Framework API | **FastAPI** (async) |
| Base de données | **PostgreSQL 16** |
| ORM | **SQLAlchemy 2.0** (style `Mapped` / `mapped_column`, async) |
| Migrations | **Alembic** |
| Authentification | **JWT** (access + refresh tokens), hachage **bcrypt** |
| Rate limiting | **slowapi** |
| Paiement | **GeniusPay** (Mobile Money + carte bancaire) |
| Traduction automatique | **DeepL API** |
| Génération de QR codes | **qrcode** + **Pillow** |
| Tests | **pytest** + **pytest-asyncio** + **httpx** (client de test ASGI) |
| Conteneurisation | **Docker** / **Docker Compose** |
| Sauvegardes | Conteneur dédié (**pg_dump** + **cron**) |

---

## 🗂 Architecture du projet

```
backend_pycon/
├── app/
│   ├── main.py                  # Point d'entrée FastAPI (factory create_app)
│   ├── core/
│   │   ├── config.py             # Paramètres (Settings, lues depuis .env)
│   │   ├── security.py           # Hachage mots de passe, JWT
│   │   └── limiter.py            # Instance slowapi partagée
│   ├── db/
│   │   ├── session.py            # Fabrique de sessions SQLAlchemy async
│   │   └── base.py                # Regroupe les modèles pour Alembic
│   ├── models/                   # Modèles SQLAlchemy (un fichier par entité)
│   ├── schemas/                  # Schémas Pydantic (validation entrée/sortie)
│   ├── services/                 # Logique métier réutilisable
│   │   ├── geniuspay_client.py    # Client HTTP vers GeniusPay
│   │   ├── qrcode_service.py      # Génération d'images de QR code
│   │   ├── ticket_service.py      # Création des billets après paiement
│   │   └── translation_service.py # Traduction automatique DeepL
│   ├── tasks/
│   │   └── email_tasks.py         # Envoi d'emails en tâche de fond
│   └── api/v1/
│       ├── deps.py                # Dépendances FastAPI (auth, rôles)
│       └── routers/               # Un routeur par module fonctionnel
├── alembic/
│   ├── env.py
│   └── versions/                  # Historique des migrations
├── backup/
│   ├── Dockerfile                 # Image dédiée aux sauvegardes
│   └── backup.sh                  # Script pg_dump + purge automatique
├── tests/
│   ├── conftest.py                # Fixtures pytest (base de test, client HTTP)
│   ├── test_auth.py
│   ├── test_cfp.py
│   └── test_payments.py
├── docker-compose.yml              # Services : api, db, backup
├── Dockerfile                      # Image de l'API
├── requirements.txt
├── .env.example
└── .env.test                       # Config dédiée aux tests automatisés
```

---

## ✅ Prérequis

- **Docker** et **Docker Compose** installés et lancés
- **Git**
- Un client HTTP pour tester (Swagger intégré, ou Postman/Insomnia)

Aucune installation locale de Python ni de PostgreSQL n'est nécessaire : tout tourne dans des conteneurs.

---

## ⚙️ Installation

```bash
git clone <url-du-dépôt>
cd backend_pycon
```

Copier le fichier d'environnement d'exemple :

```bash
copy .env.example .env        # Windows
# ou
cp .env.example .env          # macOS / Linux
```

Renseigner ensuite les valeurs réelles dans `.env` (voir section suivante).

---

## 🔐 Variables d'environnement

| Variable | Description | Exemple |
|---|---|---|
| `DATABASE_URL` | URL de connexion PostgreSQL async | `postgresql+asyncpg://pycon_admin:password@db:5432/pyconci` |
| `JWT_SECRET_KEY` | Clé secrète de signature des tokens | *(chaîne aléatoire longue)* |
| `JWT_ALGORITHM` | Algorithme de signature JWT | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Durée de vie du token d'accès | `60` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Durée de vie du token de rafraîchissement | `7` |
| `GENIUSPAY_API_KEY` | Clé API du prestataire de paiement | `pk_sandbox_...` |
| `GENIUSPAY_API_SECRET` | Secret API GeniusPay | `sk_sandbox_...` |
| `GENIUSPAY_WEBHOOK_SECRET` | Secret de vérification des webhooks | `wh_sandbox_...` |
| `GENIUSPAY_ENVIRONMENT` | Environnement GeniusPay | `sandbox` ou `production` |
| `DEEPL_API_KEY` | Clé API DeepL (traduction automatique) | `xxxxxxxx-xxxx-xxxx:fx` |
| `ALLOWED_ORIGINS` | Origines autorisées en CORS, séparées par des virgules | `http://localhost:3000,https://pycon.ci/` |
| `APP_HOST` | Hôte d'écoute de l'API | `0.0.0.0` |
| `APP_PORT` | Port d'écoute de l'API | `8000` |

> ⚠️ **`DEEPL_API_KEY` est optionnelle** : si elle est vide, la traduction automatique est simplement désactivée, sans erreur — le reste de l'API fonctionne normalement.

---

## 🚀 Lancer le projet

```bash
docker-compose up --build
```

Ceci démarre trois conteneurs :

| Conteneur | Rôle |
|---|---|
| `pyconci_api` | L'API FastAPI, avec rechargement automatique |
| `pyconci_db` | La base PostgreSQL |
| `pyconci_backup` | Sauvegardes automatisées quotidiennes |

Pour les lancements suivants (sans nouvelle dépendance) :

```bash
docker-compose up
```

L'API est alors accessible sur **http://localhost:8000**.

---

## 📘 Documentation de l'API

FastAPI génère automatiquement une documentation interactive complète :

- **Swagger UI** : http://localhost:8000/docs
- **Redoc** : http://localhost:8000/redoc
- **Schéma OpenAPI brut** : http://localhost:8000/openapi.json

Chaque route peut être testée directement depuis `/docs`, y compris les routes protégées via le bouton **Authorize** (coller le token JWT obtenu via `/auth/login`).

---

## 🧩 Modules fonctionnels

| Module | Description |
|---|---|
| **Auth** | Inscription, connexion, rafraîchissement de token, profil courant |
| **CFP** | Soumission et gestion des propositions de conférences (talks / ateliers) |
| **Billetterie** | Catégories de billets, commandes, paiement, e-billets avec QR code |
| **Programme** | Salles et sessions du programme, avec filtres |
| **Speakers** | Profils des intervenants, biographie, réseaux sociaux |
| **Sponsors** | Niveaux de sponsoring et sponsors |
| **Blog / Articles** | Articles avec statut brouillon/publié et champs SEO |
| **Code de conduite** | Formulaire de signalement anonyme, consultation restreinte |
| **Traductions** | Système générique de traduction multilingue, manuel et automatique |
| **Back-office admin** | Gestion CFP, tableau de bord statistique |

---

## 🔑 Authentification & rôles

L'authentification repose sur des **tokens JWT** :

1. `POST /auth/register` — création de compte (rôle `participant` par défaut)
2. `POST /auth/login` — renvoie un `access_token` (courte durée) et un `refresh_token` (longue durée)
3. `POST /auth/refresh` — renouvelle les tokens sans ressaisir le mot de passe
4. `GET /auth/me` — profil de l'utilisateur connecté

### Rôles disponibles

| Rôle | Usage |
|---|---|
| `participant` | Utilisateur standard (par défaut à l'inscription) |
| `staff` | Accès à certaines opérations opérationnelles (vérification de billets, programme) |
| `moderator` | Accès à la modération du CFP |
| `admin` | Accès complet au back-office |

Les routes protégées utilisent la dépendance `require_role(...)`, qui accepte un ou plusieurs rôles autorisés.

---

## 🎟 Modèle de gestion des quotas (billetterie)

Le quota d'une catégorie de billets (`ticket_categories.quota`) est une **valeur fixe, définie à la création** et **jamais décrémentée directement**.

La quantité **réellement disponible** est toujours **recalculée dynamiquement** à partir des commandes actives :

```
restant = quota − Σ(quantités des commandes NI annulées NI en échec)
```

Ce calcul est effectué à la fois dans `POST /orders` (avec un **verrou de ligne** `SELECT ... FOR UPDATE` pour empêcher deux commandes simultanées de survendre les dernières places) et dans `GET /tickets/categories` (pour affichage), garantissant que les deux endpoints renvoient toujours des chiffres cohérents entre eux.

Le champ `sold` (nombre de billets réellement émis après paiement confirmé) est une statistique **purement informative**, distincte du calcul du restant.

---

## 🌍 Multilinguisme (FR / EN)

Le contenu éditorial est stocké en **français par défaut**. Les traductions anglaises sont stockées séparément dans une table générique `translations` :

| Colonne | Rôle |
|---|---|
| `entity_type` | Type de contenu (`article`, `session`, `speaker`) |
| `entity_id` | Identifiant de l'entité concernée |
| `language` | Langue de la traduction (`en`) |
| `field` | Nom du champ traduit (`title`, `bio`, ...) |
| `value` | Texte traduit |

### Déclenchement

- **Automatique** : dès qu'un article, une session ou un profil intervenant est créé ou modifié, la traduction anglaise est générée via l'**API DeepL** et stockée automatiquement — à condition que `DEEPL_API_KEY` soit configurée. Sans clé, l'opération est silencieusement ignorée.
- **Manuel** : les traductions peuvent aussi être créées, modifiées ou supprimées directement via `POST /translations/`, `PUT /translations/{id}`, `DELETE /translations/{id}` (réservé aux administrateurs).

### Consultation (publique, sans authentification)

```
GET /translations/?entity_type=article&entity_id=1&language=en
```

### Contenus actuellement couverts

| Entité | Champs traduits |
|---|---|
| Article | `title`, `content`, `excerpt` |
| Session | `title`, `description`, `topic`, `level` |
| Speaker | `bio` |

---

## 🛡 Sécurité

| Mesure | Détail |
|---|---|
| **Rate limiting** | `POST /auth/login` et `/auth/register` : 5 requêtes/minute par IP · `POST /conduct-reports/` : 3 requêtes/heure par IP |
| **Validation stricte** | Longueurs minimales et maximales sur les champs sensibles (ex. signalements : 10 à 3000 caractères) |
| **Taille des requêtes** | Corps de requête limité à 1 Mo, rejeté avec `413` au-delà |
| **CORS** | Origines strictement limitées via `ALLOWED_ORIGINS`, jamais de wildcard combiné aux identifiants |
| **Contrôle d'accès** | Chaque commande n'est consultable que par son propriétaire ou un compte admin/staff |
| **Mots de passe** | Hachage **bcrypt**, jamais stockés ni renvoyés en clair |
| **Webhooks de paiement** | Vérification de signature, fenêtre de validité du timestamp (5 minutes) |

---

## 💾 Sauvegardes automatisées

Un conteneur dédié (`pyconci_backup`) exécute quotidiennement à **3h du matin** un `pg_dump` compressé de la base, avec purge automatique des sauvegardes de plus de **7 jours**.

Les fichiers sont accessibles directement depuis le dossier local `./backups/` (bind mount).

### Déclencher une sauvegarde manuelle

```bash
docker exec -it pyconci_backup /usr/local/bin/backup.sh
```

### Restaurer une sauvegarde (vérification / environnement de secours)

```bash
docker exec -it pyconci_db psql -U pycon_admin -d pyconci -c "CREATE DATABASE pyconci_restore;"
docker exec -it pyconci_backup sh -c "zcat /backups/<fichier>.sql.gz | PGPASSWORD=<mot_de_passe> psql -h db -U pycon_admin -d pyconci_restore"
```

---

## 🧪 Tests automatisés

Le projet dispose d'une suite de tests d'intégration couvrant les modules critiques : **authentification**, **CFP**, **paiement**.

- Base de données PostgreSQL **entièrement séparée** (`pyconci_test_suite`), recréée à chaque test
- Le service de paiement externe **GeniusPay est simulé** (mock), aucun test ne dépend d'une vraie clé API
- Le limiteur de débit est réinitialisé automatiquement avant chaque test

### Lancer toute la suite

```bash
docker exec -it pyconci_api pytest -v
```

### Lancer un module précis

```bash
docker exec -it pyconci_api pytest tests/test_auth.py -v
docker exec -it pyconci_api pytest tests/test_cfp.py -v
docker exec -it pyconci_api pytest tests/test_payments.py -v
```

---

## 🔄 Migrations de base de données

Les migrations sont gérées avec **Alembic**.

### Générer une migration après modification des modèles

```bash
docker exec -it pyconci_api alembic revision --autogenerate -m "description du changement"
```

### Appliquer les migrations

```bash
docker exec -it pyconci_api alembic upgrade head
```

### Revenir à une migration précédente

```bash
docker exec -it pyconci_api alembic downgrade <revision>
```

---

## 🔗 Intégration front-end

- **Base URL locale** : `http://localhost:8000`
- **Authentification** : header `Authorization: Bearer <access_token>`
- **CORS** : autoriser l'origine du front dans `ALLOWED_ORIGINS` (déjà configuré pour `http://localhost:3000`, `http://localhost:5173` et `https://pyconci.ci`)
- **Formats de date** : ISO 8601, UTC
- **Langue du contenu** : le contenu principal (`title`, `content`, etc.) est en français ; la version anglaise s'obtient via `GET /translations/` avec l'`entity_type` et l'`entity_id` concernés

---

## 📋 Liste complète des endpoints

### Auth
| Méthode | Route | Accès |
|---|---|---|
| POST | `/auth/register` | Public |
| POST | `/auth/login` | Public |
| POST | `/auth/refresh` | Public |
| GET | `/auth/me` | Authentifié |

### CFP
| Méthode | Route | Accès |
|---|---|---|
| POST | `/cfp/submissions` | Authentifié |
| GET | `/cfp/submissions` | Admin / Modérateur / Staff |
| GET | `/cfp/submissions/{id}` | Authentifié |
| PATCH | `/cfp/submissions/{id}/status` | Admin / Modérateur / Staff |

### Back-office CFP
| Méthode | Route | Accès |
|---|---|---|
| GET | `/admin/cfp/` | Admin |
| GET | `/admin/cfp/{id}` | Admin |
| PUT | `/admin/cfp/{id}/status` | Admin |

### Billetterie
| Méthode | Route | Accès |
|---|---|---|
| GET | `/tickets/categories` | Public |
| POST | `/tickets/categories` | Admin |
| PUT | `/tickets/categories/{id}` | Admin |
| GET | `/tickets/{qr_code}/verify` | Admin / Staff |
| POST | `/orders` | Public / Authentifié optionnel |
| GET | `/orders/{id}` | Propriétaire / Admin / Staff |
| POST | `/payments` | Public |
| GET | `/payments/{reference}` | Public |
| POST | `/payments/webhook/geniuspay` | Prestataire (signature vérifiée) |

### Programme
| Méthode | Route | Accès |
|---|---|---|
| POST | `/program/rooms` | Admin / Staff |
| POST | `/program/sessions` | Admin / Staff |
| GET | `/program` | Public |

### Speakers
| Méthode | Route | Accès |
|---|---|---|
| GET | `/speakers/` | Public |
| POST | `/speakers/` | Admin |
| GET | `/speakers/{id}` | Public |
| PUT | `/speakers/{id}` | Admin |
| DELETE | `/speakers/{id}` | Admin |

### Sponsors
| Méthode | Route | Accès |
|---|---|---|
| GET | `/sponsors/niveaux` | Public |
| POST | `/sponsors/niveaux` | Admin |
| GET | `/sponsors/` | Public |
| POST | `/sponsors/` | Admin |
| GET | `/sponsors/{id}` | Public |
| PUT | `/sponsors/{id}` | Admin |
| DELETE | `/sponsors/{id}` | Admin |

### Articles (blog)
| Méthode | Route | Accès |
|---|---|---|
| GET | `/articles/` | Public (articles publiés uniquement) |
| POST | `/articles/` | Admin |
| GET | `/articles/{slug}` | Public (si publié) |
| PUT | `/articles/{id}` | Admin |
| DELETE | `/articles/{id}` | Admin |

### Code de conduite
| Méthode | Route | Accès |
|---|---|---|
| POST | `/conduct-reports/` | Public (formulaire anonyme) |
| GET | `/conduct-reports/` | Admin |
| GET | `/conduct-reports/{id}` | Admin |
| PUT | `/conduct-reports/{id}` | Admin |

### Traductions
| Méthode | Route | Accès |
|---|---|---|
| GET | `/translations/` | Public |
| POST | `/translations/` | Admin |
| PUT | `/translations/{id}` | Admin |
| DELETE | `/translations/{id}` | Admin |

### Statistiques
| Méthode | Route | Accès |
|---|---|---|
| GET | `/admin/stats/` | Admin |

---

## 📌 État du projet

Développement réalisé sur un chronogramme de **deux semaines** (02 → 16 août 2026), couvrant successivement : mise en place du projet, authentification, CFP, billetterie, paiement, programme, intervenants, sponsors, blog, code de conduite, back-office, multilinguisme, sécurité, sauvegardes, tests automatisés, puis une phase finale de **revue de code et de préparation à l'intégration front-end**.

> ✅ 20 tests automatisés passants · Documentation Swagger complète · Sauvegardes automatisées validées · CORS et modèle de quotas consolidés pour l'intégration front-end.

---

<p align="center">
  Fait  pour la communauté Python de Côte d'Ivoire 🇨🇮
</p>