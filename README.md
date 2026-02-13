# Langchain Scamming Protector

**Projet pédagogique réalisé par** :

- Léa DRUFFIN
- Satya MINGUEZ
- Adrien FOUQUET
- Amaury TISSOT

---

## 1. Présentation du projet

### Concept

Langchain Scamming Protector est une simulation interactive d'arnaque téléphonique à visée pédagogique. L'application met en scène Jeanne Dubois, une personne âgée de 78 ans, confrontée à un arnaqueur téléphonique. L'ensemble de la conversation est généré par des agents LLM (Large Language Models) orchestrés via LangChain.

### Vue d'ensemble fonctionnelle

L'utilisateur assiste à une conversation téléphonique simulée entre Jeanne et un arnaqueur. Toutes les deux répliques, le public peut intervenir en choisissant parmi quatre actions (raccrocher, donner ses informations bancaires, simuler un malaise, continuer la conversation). Un agent directeur analyse la situation en temps réel et adapte le comportement de Jeanne. La conversation est accompagnée de synthèse vocale (voix distinctes pour chaque personnage) et d'effets sonores immersifs (aboiement de chien, sonnette, toux, etc.).

---

## 2. Architecture du projet

### Architecture globale

Le projet suit une architecture **client-serveur** avec une séparation frontend/backend :

```
┌─────────────────────┐         HTTP (REST)         ┌──────────────────────────┐
│   Frontend React     │ ◄─────────────────────────► │   Backend FastAPI         │
│   (port 5173)        │                             │   (port 8000)             │
│                      │                             │                           │
│  - Interface chat    │                             │  ┌─────────────────────┐  │
│  - Lecture audio     │                             │  │   Agent Victime     │  │
│  - Modal intervention│                             │  │   (Jeanne Dubois)   │  │
│                      │                             │  ├─────────────────────┤  │
│                      │                             │  │   Agent Arnaqueur   │  │
│                      │                             │  ├─────────────────────┤  │
│                      │                             │  │   Agent Directeur   │  │
│                      │                             │  ├─────────────────────┤  │
│                      │                             │  │   Modérateur Public │  │
│                      │                             │  └─────────────────────┘  │
└─────────────────────┘                              └──────────────────────────┘
                                                               │
                                                     ┌─────────┴─────────┐
                                                     │  Groq API (LLM)   │
                                                     │  Google TTS        │
                                                     └───────────────────┘
```

### Briques techniques principales

| Composant       | Technologie                  | Rôle                                                                 |
| --------------- | ---------------------------- | -------------------------------------------------------------------- |
| Backend API     | FastAPI + Uvicorn            | Expose les endpoints REST, gère les sessions                         |
| Agents IA       | LangChain + Groq (LLaMA 3.1) | Génération des dialogues (victime, arnaqueur, directeur, modérateur) |
| Synthèse vocale | Google Cloud TTS             | Voix françaises distinctes pour chaque personnage                    |
| Frontend        | React 19 + TypeScript + Vite | Interface utilisateur, lecture audio, interactions                   |
| Styles          | Tailwind CSS 4               | Mise en forme de l'interface                                         |

### Organisation du projet

```
langchain_scamming_protector/
├── app/
│   ├── agents/                  # Agents LLM (victime, arnaqueur, directeur, modérateur)
│   ├── api/                     # Routes FastAPI, modèles Pydantic, gestion de sessions
│   ├── core/                    # Configuration (clés API, credentials)
│   └── tools/                   # Outils sonores et fichiers MP3
│       └── sounds/              # Fichiers audio (aboiement, sonnette, toux, etc.)
├── frontend/
│   └── src/
│       ├── components/          # Composants React (chat, bulles, modal, barre de saisie)
│       ├── hooks/               # Hook de lecture audio séquentielle
│       ├── App.tsx              # Composant principal
│       ├── api.ts               # Client HTTP vers le backend
│       └── types.ts             # Interfaces TypeScript
├── tests/                       # Tests unitaires (pytest)
├── server.py                    # Point d'entrée FastAPI
├── main.py                      # Point d'entrée console (legacy)
├── docker-compose.yml           # Orchestration Docker
├── Dockerfile.backend           # Image Docker du backend
├── Dockerfile.frontend          # Image Docker du frontend
└── requirements.txt             # Dépendances Python
```

---

## 3. Installation et démarrage

### 3.1 Prérequis

- **Docker** et **Docker Compose**
- Un compte **Groq** avec une clé API valide
- _(Optionnel)_ Un compte **Google Cloud** avec l'API Text-to-Speech activée et un compte de service

### 3.2 Configuration du fichier `.env`

Le fichier `.env` contient les secrets nécessaires au fonctionnement de l'application.

**1. Créer le fichier à partir du template**

```bash
cp .env.example .env
```

**2. Renseigner les variables**

Le fichier `.env` contient deux variables :

#### `GROQ_API_KEY` (obligatoire)

Clé d'API pour accéder aux modèles LLM via Groq. Sans cette clé, l'application ne peut pas démarrer.

- Créer un compte sur [console.groq.com](https://console.groq.com)
- Aller dans **API Keys** et générer une nouvelle clé
- Copier la clé dans le fichier `.env` :

```env
GROQ_API_KEY="gsk_xxxxxxxxxxxxxxxxxxxxxxxxx"
```

#### `GOOGLE_CREDENTIALS` (optionnel)

Credentials d'un compte de service Google Cloud au format JSON, sur **une seule ligne**. Cette variable active la synthèse vocale (TTS) pour les voix de Jeanne et de l'arnaqueur. Sans cette variable, l'application fonctionne mais **sans audio vocal**.

- Copier le contenu JSON complet dans le fichier `.env`, sur une seule ligne :

```env
GOOGLE_CREDENTIALS='{"type": "service_account", "project_id": "mon-projet", "private_key_id": "abc123", "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n", "client_email": "tts@mon-projet.iam.gserviceaccount.com", "client_id": "123456", "auth_uri": "https://accounts.google.com/o/oauth2/auth", "token_uri": "https://oauth2.googleapis.com/token", "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs", "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/tts%40mon-projet.iam.gserviceaccount.com", "universe_domain": "googleapis.com"}'
```

> **Attention** : le JSON doit tenir sur une seule ligne. Ne pas ajouter de retour à la ligne à l'intérieur de la valeur.

**3. Exemple de fichier `.env` complet**

```env
GROQ_API_KEY="gsk_xxxxxxxxxxxxxxxxxxxxxxxxx"
GOOGLE_CREDENTIALS='{"type": "service_account", "project_id": "...", ...}'
```

### 3.3 Installation avec Docker

**1. Configurer le fichier `.env`** (voir section ci-dessus)

**2. Lancer l'application**

```bash
docker-compose up -d
```

Cette commande construit les images et démarre deux conteneurs :

- **backend** sur le port `8000`
- **frontend** sur le port `5173`

---

## 4. Utilisation de l'application

### Accès

Une fois les conteneurs démarrés, ouvrir un navigateur et accéder à :

```
http://localhost:5173
```

### Déroulement d'une session

1. **Créer une session** : cliquer sur le bouton de démarrage pour initier une nouvelle conversation
2. **Observer la conversation** : l'arnaqueur engage la discussion, Jeanne répond automatiquement avec synthèse vocale et effets sonores
3. **Intervenir** : toutes les 2 répliques, une fenêtre modale propose 4 choix :
    - Raccrocher le téléphone
    - Donner les informations bancaires
    - Simuler un malaise / urgence santé
    - Continuer la conversation normalement
4. La conversation se poursuit jusqu'à un maximum de **15 tours** (pour limiter les appels à l'API)

### Captures d'écran

Exemple de conversation :
![Capture d'écran 1](https://i.imgur.com/QYQo7vN.png)

Modale affichant les différents choix :
![Capture d'écran 2](https://i.imgur.com/Zq6oL6D.png)

---

## 6. Pistes d'évolution

- Persistance des sessions en base de données (actuellement en mémoire)
- Migration vers WebSocket pour du streaming temps réel
- Migration vers LangGraph pour l'orchestration des agents
- Métriques de résistance aux arnaques

---

## 7. Documentation technique

### Technologies utilisées

**Backend :**

| Technologie                | Version    | Usage                                               |
| -------------------------- | ---------- | --------------------------------------------------- |
| Python                     | 3.10+      | Langage backend                                     |
| FastAPI                    | >= 0.110.0 | Framework API REST                                  |
| Uvicorn                    | >= 0.27.0  | Serveur ASGI                                        |
| LangChain                  | 0.1.16     | Framework d'orchestration d'agents LLM              |
| LangChain-Groq             | -          | Intégration du provider Groq (LLaMA 3.1 8B Instant) |
| LangChain-Google-Community | -          | Intégration Google Cloud TTS                        |
| python-dotenv              | 1.0.1      | Chargement des variables d'environnement            |
| pytest                     | >= 7.0.0   | Framework de tests                                  |

**Frontend :**

| Technologie  | Version | Usage                                  |
| ------------ | ------- | -------------------------------------- |
| React        | 19      | Bibliothèque UI                        |
| TypeScript   | 5.9     | Typage statique                        |
| Vite         | 7       | Build tool et serveur de développement |
| Tailwind CSS | 4       | Framework CSS utilitaire               |

### Configuration des agents

Chaque agent utilise le modèle `llama-3.1-8b-instant` via Groq avec des températures adaptées à son rôle :

| Agent            | Température | Justification                                  |
| ---------------- | ----------- | ---------------------------------------------- |
| Victime (Jeanne) | 0.7         | Réponses naturelles et variées                 |
| Arnaqueur        | 0.8         | Créativité dans les techniques de manipulation |
| Directeur        | 0.2         | Analyse cohérente et déterministe              |
| Modérateur       | 0.4         | Choix d'intervention équilibrés                |

### Endpoints API

| Méthode  | Route                          | Description                                  |
| -------- | ------------------------------ | -------------------------------------------- |
| `POST`   | `/api/sessions`                | Créer une nouvelle session                   |
| `GET`    | `/api/sessions/{id}`           | Récupérer les informations d'une session     |
| `DELETE` | `/api/sessions/{id}`           | Supprimer une session                        |
| `POST`   | `/api/chat`                    | Envoyer un message avec analyse du directeur |
| `POST`   | `/api/auto-conversation/start` | Démarrer une conversation automatique        |
| `POST`   | `/api/auto-conversation/next`  | Tour suivant de la conversation              |
| `POST`   | `/api/auto-conversation/stop`  | Arrêter la conversation en cours             |

---

## 7. Décharge de responsabilité

Les développeurs de ce projet déclinent toute responsabilité quant à :

L'utilisation abusive ou détournée de cette application
Les conséquences juridiques découlant d'une utilisation inappropriée
Les dommages directs ou indirects causés par l'utilisation de ce logiciel

En utilisant ce projet, vous acceptez de le faire dans le strict respect des lois en vigueur et dans un cadre exclusivement éducatif et préventif.
