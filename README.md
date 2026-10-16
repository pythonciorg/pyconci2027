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
- [Code de vérification par email](#-code-de-vérification-par-email)
- [Mot de passe oublié](#-mot-de-passe-oublié)
- [Propositions CFP](#-propositions-cfp)
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
| `PASSWORD_RESET_TOKEN_EXPIRE_MINUTES` | Durée de validité du lien de réinitialisation du mot de passe | `30` |
| `OTP_EXPIRE_MINUTES` | Durée de validité du code de connexion envoyé par email | `10` |
| `FRONTEND_URL` | Adresse du site, utilisée dans le lien de réinitialisation | `https://pycon.ci` |
| `SMTP_HOST` | Serveur SMTP ; vide = emails affichés dans la console | `smtp.gmail.com` |
| `SMTP_PORT` | Port SMTP | `587` |
| `SMTP_USER` | Compte d'envoi | `adresse@gmail.com` |
| `SMTP_PASSWORD` | Mot de passe SMTP (mot de passe d'application pour Gmail) | *(secret)* |
| `SMTP_FROM` | Expéditeur affiché (par défaut : `SMTP_USER`) | `PyCon CI <adresse@gmail.com>` |
| `SMTP_STARTTLS` | Chiffrement STARTTLS (port 587) | `true` |
| `SMTP_USE_SSL` | Connexion SSL directe (port 465) | `false` |
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

Chaque route peut être testée directement depuis `/docs`, y compris les routes protégées via le bouton **Authorize** (coller l'`access_token` obtenu via `/auth/login` puis `/auth/otp/verify`).

---

## 🧩 Modules fonctionnels

| Module | Description |
|---|---|
| **Auth** | Inscription, connexion, rafraîchissement de token, mot de passe oublié, profil courant |
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

1. `POST /auth/register` — création de compte (rôle `participant` par défaut) ; un code à 6 chiffres est envoyé par email et un `otp_token` est renvoyé
2. `POST /auth/login` — vérifie l'email et le mot de passe ; un code à 6 chiffres est envoyé par email et un `otp_token` est renvoyé
3. `POST /auth/otp/verify` — échange l'`otp_token` et le code contre un `access_token` (courte durée) et un `refresh_token` (longue durée)
4. `POST /auth/otp/resend` — renvoie un nouveau code à partir de l'`otp_token` (bouton « Renvoyer le code »)
5. `POST /auth/refresh` — renouvelle les tokens sans ressaisir le mot de passe ni de code
6. `GET /auth/me` — profil de l'utilisateur connecté

Les tokens ne sont jamais renvoyés par `/auth/register` ni `/auth/login` : il faut toujours passer par le code (voir [Code de vérification par email](#-code-de-vérification-par-email)).

### Rôles disponibles

| Rôle | Usage |
|---|---|
| `participant` | Utilisateur standard (par défaut à l'inscription) |
| `staff` | Accès à certaines opérations opérationnelles (vérification de billets, programme) |
| `moderator` | Accès à la modération du CFP |
| `admin` | Accès complet au back-office |

Les routes protégées utilisent la dépendance `require_role(...)`, qui accepte un ou plusieurs rôles autorisés.

---

## 📩 Code de vérification par email

À l'**inscription** comme à chaque **connexion**, un **code à 6 chiffres** est envoyé par email. C'est ce code, et non le mot de passe seul, qui donne accès aux tokens. L'utilisateur ne saisit **que le code**, pas son email.

### Parcours de l'utilisateur

1. **Inscription** : il remplit le formulaire, le site appelle `POST /auth/register`. **Connexion** : il saisit email et mot de passe, le site appelle `POST /auth/login`.
2. Les deux routes renvoient un `otp_token`. Le site le **garde en mémoire sans l'afficher** : il indique au serveur à quel compte appartient le code.
3. Le site affiche un écran « Saisissez le code reçu par email ». L'utilisateur reçoit un email « Votre code de connexion PyCon CI ».
4. Il saisit le code. Le site appelle `POST /auth/otp/verify` avec l'`otp_token` et le code, et reçoit `access_token` et `refresh_token`.
5. S'il n'a pas reçu le code, il clique sur **« Renvoyer le code »**. Le site appelle `POST /auth/otp/resend` avec l'`otp_token` gardé, et **remplace** l'`otp_token` par celui de la réponse. Il faut attendre **60 secondes** entre deux envois.
6. Si l'`otp_token` a expiré (plus de 10 minutes), le renvoi est refusé : l'utilisateur se reconnecte (`/auth/login`). C'est aussi valable juste après l'inscription, puisque le compte existe déjà.

### Appels API

| Route | Corps de la requête | Réponse |
|---|---|---|
| `POST /auth/register` | `{"email": "...", "full_name": "...", "password": "..."}` | `200` avec `{"message": "...", "otp_token": "..."}` · `400` si l'email est déjà utilisé |
| `POST /auth/login` | `{"email": "...", "password": "..."}` | `200` avec `{"message": "...", "otp_token": "..."}` · `401` si email ou mot de passe incorrect |
| `POST /auth/otp/verify` | `{"otp_token": "...", "code": "123456"}` | `200` avec `access_token` et `refresh_token` |
| `POST /auth/otp/resend` | `{"otp_token": "..."}` | `200` avec `{"message": "...", "otp_token": "..."}` (**nouveau** `otp_token`) · `429` si moins de 60 s depuis le dernier envoi · `400` si l'`otp_token` est invalide ou expiré |

Exemple côté site :

```js
// 1. Connexion (ou inscription) : on garde l'otp_token sans l'afficher
const res = await fetch(`${API_URL}/auth/login`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ email, password }),
});
const { otp_token } = await res.json();

// 2. L'utilisateur saisit uniquement le code reçu par email
const verify = await fetch(`${API_URL}/auth/otp/verify`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ otp_token, code }),
});
const { access_token, refresh_token } = await verify.json();

// 3. Bouton « Renvoyer le code » : on remplace l'otp_token gardé par le nouveau
const resend = await fetch(`${API_URL}/auth/otp/resend`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ otp_token }),
});
if (resend.ok) {
  otp_token = (await resend.json()).otp_token;
} else if (resend.status === 429) {
  const secondes = resend.headers.get("Retry-After"); // ex. « Renvoyer le code (45 s) »
} else if (resend.status === 400) {
  // otp_token expiré : renvoyer vers la page de connexion
}
```

Codes d'erreur à gérer côté site pour `otp/verify` :

| Code | Signification | Quoi afficher |
|---|---|---|
| `400` | Code faux, expiré, déjà utilisé, ou trop d'essais | « Code invalide ou expiré » ; après plusieurs échecs, renvoyer vers la connexion |
| `422` | Le code n'est pas composé de 6 chiffres | Message de validation |
| `429` | Trop de tentatives | Demander de patienter une minute |

Codes d'erreur à gérer côté site pour `otp/resend` :

| Code | Signification | Quoi afficher |
|---|---|---|
| `400` | `otp_token` invalide ou expiré (« Demande expirée, veuillez vous reconnecter ») | Renvoyer vers la page de connexion |
| `429` | Moins de 60 secondes depuis le dernier envoi (l'en-tête `Retry-After` donne le nombre de secondes restantes), ou plus de 3 demandes par minute | Désactiver le bouton et afficher un compte à rebours |

### Règles de sécurité

- Le code et l'`otp_token` expirent au bout de **10 minutes** (`OTP_EXPIRE_MINUTES`).
- Le code ne fonctionne **qu'une seule fois**, et chaque nouvel envoi (connexion ou renvoi) annule le code précédent.
- Après **5 codes faux**, le code est annulé : il faut en redemander un (« Renvoyer le code ») ou se reconnecter.
- **60 secondes minimum** entre deux renvois, pour éviter d'inonder la boîte mail de l'utilisateur.
- Le code est stocké haché (HMAC avec la clé secrète), jamais en clair.
- Le code d'un compte ne peut pas ouvrir un autre compte : l'`otp_token` désigne le compte, le code doit être le sien.
- L'`otp_token` ne donne accès à rien d'autre : il ne remplace ni l'`access_token`, ni le `refresh_token`.

### Envoi du code par email

#### Quand le code est-il envoyé ?

| Action de l'utilisateur | Route appelée par le site | Code envoyé ? |
|---|---|---|
| Il crée son compte | `POST /auth/register` | ✅ Oui, à l'adresse saisie |
| Il se connecte avec le **bon** mot de passe | `POST /auth/login` | ✅ Oui, à l'adresse du compte |
| Il se connecte avec un **mauvais** mot de passe | `POST /auth/login` | ❌ Non (réponse `401`) |
| Il s'inscrit avec un email **déjà utilisé** | `POST /auth/register` | ❌ Non (réponse `400`) |
| Il clique sur « Renvoyer le code » (60 s après le dernier envoi) | `POST /auth/otp/resend` | ✅ Oui, un nouveau code ; l'ancien est annulé |
| Il clique sur « Renvoyer le code » **trop tôt** | `POST /auth/otp/resend` | ❌ Non (réponse `429` avec le délai restant) |
| Il saisit le code | `POST /auth/otp/verify` | ❌ Non, le code est vérifié |

#### Ce que fait le serveur, étape par étape

```
  Site                         API                                      Base de données       Boîte mail
   │                            │                                              │                   │
   │ POST /auth/login           │                                              │                   │
   │ {email, password} ───────► │ 1. vérifie le mot de passe                   │                   │
   │                            │ 2. tire un code au hasard : 482913           │                   │
   │                            │ 3. enregistre le code HACHÉ, l'expiration ─► │ otp_code_hash     │
   │                            │    (+10 min) et remet les essais à 0         │ otp_expires_at    │
   │                            │                                              │ otp_attempts = 0  │
   │ ◄───────────────────────── │ 4. répond {message, otp_token}               │                   │
   │                            │ 5. APRÈS la réponse, envoie l'email ──────────────────────────► │ « Votre code… »
   │                            │                                              │                   │
   │ POST /auth/otp/verify      │                                              │                   │
   │ {otp_token, code} ───────► │ 6. retrouve le compte grâce à l'otp_token    │                   │
   │                            │ 7. compare le code au hash ◄───────────────► │                   │
   │                            │ 8. efface le code (usage unique) ──────────► │ otp_* vidés       │
   │ ◄───────────────────────── │ 9. répond {access_token, refresh_token}      │                   │
```

Points importants :

- Le code en clair **n'existe que dans l'email**. La base ne contient que son empreinte (HMAC-SHA256 avec `JWT_SECRET_KEY`) : même quelqu'un qui lirait la base ne pourrait pas retrouver le code.
- Chaque nouvel envoi **remplace** le code précédent : seul le dernier code reçu fonctionne.
- L'email part **en tâche de fond**, après la réponse (étape 5). L'API répond donc immédiatement, même si le serveur SMTP est lent.

#### Exemple complet (requêtes et réponses)

**1. Connexion**

```http
POST /auth/login
Content-Type: application/json

{"email": "awa@exemple.com", "password": "MotDePasse123"}
```

```json
{
  "message": "Un code de connexion a été envoyé par email.",
  "otp_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**2. Email reçu par l'utilisateur**

```
De      : PyCon CI <adresse@gmail.com>          (valeur de SMTP_FROM)
À       : awa@exemple.com
Objet   : Votre code de connexion PyCon CI

Votre code de connexion est : 482913
Il expire dans 10 minutes et ne peut être utilisé qu'une seule fois.
Si vous n'êtes pas à l'origine de cette demande, ignorez cet email.
```

**3. Saisie du code** (l'utilisateur tape `482913`, le site ajoute l'`otp_token` qu'il a gardé)

```http
POST /auth/otp/verify
Content-Type: application/json

{"otp_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", "code": "482913"}
```

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

L'inscription fonctionne exactement pareil : `POST /auth/register` avec `{"email", "full_name", "password"}` renvoie aussi `{message, otp_token}`.

#### Configurer l'envoi (SMTP)

L'envoi passe par le SMTP configuré dans `.env`, le même que pour le mot de passe oublié.

**Avec Gmail**, pas à pas :

1. Activer la **validation en deux étapes** sur le compte Gmail d'envoi : https://myaccount.google.com/security
2. Créer un **mot de passe d'application** : https://myaccount.google.com/apppasswords (nom libre, par exemple « PyCon CI »). Google affiche 16 lettres.
3. Renseigner `.env` :

   ```env
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=adresse@gmail.com
   SMTP_PASSWORD=abcdefghijklmnop     # les 16 lettres, pas le mot de passe Gmail
   SMTP_FROM=PyCon CI <adresse@gmail.com>
   SMTP_STARTTLS=true
   SMTP_USE_SSL=false
   OTP_EXPIRE_MINUTES=10              # optionnel, 10 par défaut
   ```

4. **Redémarrer le serveur** : le `.env` n'est lu qu'au démarrage, et le rechargement automatique (`--reload`) ne surveille pas ce fichier ; le modifier seul ne suffit donc pas.

**En développement, sans SMTP** : laisser `SMTP_HOST` vide. Aucun email ne part ; le code s'affiche dans la console du serveur :

```
[Email] À: awa@exemple.com, sujet: Votre code de connexion PyCon CI
Votre code de connexion est : 482913
Il expire dans 10 minutes et ne peut être utilisé qu'une seule fois.
Si vous n'êtes pas à l'origine de cette demande, ignorez cet email.
```

**Pendant les tests automatisés** : aucun email n'est jamais envoyé, quelle que soit la configuration. `tests/conftest.py` vide `SMTP_HOST` et capture les emails d'authentification dans une boîte de test (`OUTBOX` dans `tests/helpers.py`), où les tests lisent le code.

#### Si l'utilisateur ne reçoit pas le code

Un échec d'envoi **ne bloque pas** l'API : `register` et `login` répondent quand même `200`, et l'erreur est écrite dans les logs du serveur :

```
Échec de l'envoi de l'email à awa@exemple.com (sujet: Votre code de connexion PyCon CI)
```

Il faut donc **regarder les logs du serveur** pour comprendre :

| Ce que montrent les logs | Cause | Solution |
|---|---|---|
| Une ligne `[Email] À: ...` et rien d'autre | `SMTP_HOST` est vide : mode développement | Renseigner le SMTP dans `.env` et redémarrer |
| `535 5.7.8 Username and Password not accepted` | Identifiants Gmail refusés | Utiliser un **mot de passe d'application**, pas le mot de passe du compte |
| `Connection unexpectedly closed` ou `WinError 10053` | Un antivirus intercepte le SMTP (ex. « Mail Shield » d'AVG / Avast) | Exception pour `smtp.gmail.com` et le Python du projet, ou désactiver l'analyse des emails sortants |
| `CERTIFICATE_VERIFY_FAILED` | Même cause : antivirus qui intercepte la connexion | Même solution |
| Aucune erreur | L'email est parti | Vérifier les **spams** de l'utilisateur et l'orthographe de son adresse |

Côté utilisateur : cliquer sur **« Renvoyer le code »** (après 60 secondes), ou se reconnecter si plus de 10 minutes se sont écoulées.

### Tester sans le site

Dans Swagger (http://localhost:8000/docs) :

1. Ouvrir `POST /auth/login` → **Try it out** → saisir `{"email": "...", "password": "..."}` → **Execute**.
2. Dans la réponse, copier la valeur de `otp_token` (sans les guillemets).
3. Récupérer le code à 6 chiffres :
   - dans la boîte mail du compte si le SMTP est configuré ;
   - sinon dans la console du serveur, sur la ligne qui suit `[Email] À: ...`.
4. Ouvrir `POST /auth/otp/verify` → **Try it out** → saisir `{"otp_token": "<collé à l'étape 2>", "code": "<les 6 chiffres>"}` → **Execute**.
5. Copier l'`access_token` de la réponse, cliquer sur **Authorize** en haut de la page, le coller, puis valider.
6. Les routes protégées (`GET /auth/me`, `POST /cfp/submissions`, …) sont maintenant accessibles.

Pour tester le renvoi : après l'étape 2, attendre 60 secondes, ouvrir `POST /auth/otp/resend` et saisir `{"otp_token": "<collé à l'étape 2>"}`. Un nouveau code arrive ; utiliser l'`otp_token` de **cette** réponse à l'étape 4.

> ⏱ Les étapes 1 à 4 doivent tenir en **10 minutes**. Au-delà, recommencer à l'étape 1. Après 5 codes faux, utiliser le renvoi ou recommencer à l'étape 1.

---

## 🔁 Mot de passe oublié

La réinitialisation se fait par un **lien envoyé par email**. Le lien contient un token ; l'utilisateur ne le voit et ne le copie jamais, c'est la page du site qui le lit dans l'adresse.

### Parcours de l'utilisateur

1. Sur la page de connexion, il clique sur « Mot de passe oublié ? ».
2. Sur la page `/forgot-password`, il saisit son email. Le site appelle `POST /auth/forgot-password`.
3. Il reçoit un email avec un lien `{FRONTEND_URL}/reset-password?token=...`.
4. Il clique. La page `/reset-password` récupère le `token` dans l'URL et lui demande son nouveau mot de passe.
5. Le site appelle `POST /auth/reset-password` avec le token et le nouveau mot de passe, puis redirige vers la connexion.

### Appels API

| Route | Corps de la requête | Réponse |
|---|---|---|
| `POST /auth/forgot-password` | `{"email": "..."}` | `200` avec un message générique, que l'email existe ou non |
| `POST /auth/reset-password` | `{"token": "...", "new_password": "..."}` | `200` si le mot de passe est changé |

Codes d'erreur à gérer côté site pour `reset-password` :

| Code | Signification | Quoi afficher |
|---|---|---|
| `400` | Lien invalide, expiré ou déjà utilisé | Proposer de redemander un lien |
| `422` | Mot de passe trop court (moins de 8 caractères) ou JSON mal formé | Message de validation |
| `429` | Trop de tentatives | Demander de patienter une minute |

Exemple pour la page `/reset-password` :

```js
const token = new URLSearchParams(window.location.search).get("token");

const res = await fetch(`${API_URL}/auth/reset-password`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ token, new_password: password }),
});

if (res.ok) {
  // succès → rediriger vers /login
} else if (res.status === 400) {
  // lien invalide ou expiré → proposer d'en redemander un
}
```

### Règles de sécurité

- Le lien expire au bout de **30 minutes** (`PASSWORD_RESET_TOKEN_EXPIRE_MINUTES`).
- Il ne fonctionne **qu'une seule fois** : dès que le mot de passe change, il est rejeté.
- Il ne sert qu'à changer le mot de passe, pas à se connecter.
- `forgot-password` renvoie toujours la même réponse, pour ne pas révéler quels emails ont un compte. Le site doit afficher le même message dans tous les cas.
- Les sessions déjà ouvertes ne sont pas déconnectées : les anciens tokens restent valables jusqu'à leur expiration.

### Envoi des emails (SMTP)

Les emails partent par SMTP dès que `SMTP_HOST` est renseigné dans `.env`. Si `SMTP_HOST` est vide, ils sont simplement affichés dans la console du serveur, ce qui suffit en développement.

Exemple avec Gmail :

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=adresse@gmail.com
SMTP_PASSWORD=mot_de_passe_d_application
SMTP_FROM=PyCon CI <adresse@gmail.com>
```

Pour Gmail, `SMTP_PASSWORD` doit être un **mot de passe d'application** (https://myaccount.google.com/apppasswords, validation en deux étapes requise), pas le mot de passe du compte. Si l'envoi échoue, l'erreur est écrite dans les logs du serveur et la requête de l'utilisateur n'échoue pas.

Si les logs affichent `Connection unexpectedly closed` ou `WinError 10053` alors que les identifiants sont bons, un antivirus intercepte probablement le SMTP (par exemple le « Mail Shield » d'AVG ou d'Avast). Ajouter une exception pour `smtp.gmail.com` et pour le Python du projet, ou désactiver l'analyse des emails sortants.

### Tester sans le site

Tant que la page `/reset-password` n'existe pas, le parcours se teste dans Swagger : appeler `forgot-password`, copier ce qui suit `token=` dans le lien reçu, puis le coller dans `reset-password`.

---

## 🎤 Propositions CFP

Un speaker connecté soumet une proposition (talk ou atelier) avec `POST /cfp/submissions`. Elle suit ensuite ce cycle, piloté par les reviewers (admin, modérateur, staff) via `PATCH /cfp/submissions/{id}/status` :

```
soumis → en_revue → accepté / refusé
```

Le speaker reçoit un email à chaque changement de statut.

### Modifier une proposition

L'auteur peut modifier sa proposition avec `PATCH /cfp/submissions/{id}`, **tant qu'elle est au statut `soumis`**. Dès qu'un reviewer la passe `en_revue`, elle est figée, pour que l'évaluation porte sur une version stable.

Seuls les champs envoyés sont modifiés :

```json
{ "title": "Nouveau titre", "format": "atelier" }
```

Champs modifiables : `title`, `description`, `topic`, `level`, `format`. Le `status` n'est pas modifiable par cette route ; s'il est envoyé, il est ignoré.

| Code | Signification |
|---|---|
| `200` | Proposition modifiée |
| `403` | L'utilisateur n'est pas l'auteur de la proposition |
| `404` | Proposition introuvable |
| `409` | Proposition déjà en revue, acceptée ou refusée : modification impossible |
| `422` | Champ invalide (ex. titre de plus de 255 caractères) |

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
| **Rate limiting** | `POST /auth/login`, `/auth/register`, `/auth/reset-password` et `/auth/otp/verify` : 5 requêtes/minute par IP · `POST /auth/forgot-password` et `/auth/otp/resend` : 3 requêtes/minute par IP (et 60 s minimum entre deux codes renvoyés) · `POST /conduct-reports/` : 3 requêtes/heure par IP |
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
| POST | `/auth/forgot-password` | Public |
| POST | `/auth/reset-password` | Public (token reçu par email) |
| POST | `/auth/otp/verify` | Public (`otp_token` + code reçu par email) |
| POST | `/auth/otp/resend` | Public (`otp_token`) |
| GET | `/auth/me` | Authentifié |

### CFP
| Méthode | Route | Accès |
|---|---|---|
| POST | `/cfp/submissions` | Authentifié |
| GET | `/cfp/submissions` | Admin / Modérateur / Staff |
| GET | `/cfp/submissions/{id}` | Authentifié |
| PATCH | `/cfp/submissions/{id}` | Auteur de la proposition, tant qu'elle est `soumis` |
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

> ✅ 41 tests automatisés passants · Documentation Swagger complète · Sauvegardes automatisées validées · CORS et modèle de quotas consolidés pour l'intégration front-end.

---

<p align="center">
  Fait  pour la communauté Python de Côte d'Ivoire 🇨🇮
</p>