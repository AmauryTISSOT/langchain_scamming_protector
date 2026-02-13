# langchain_scamming_protector

Simulation interactive d'arnaque telephonique mettant en scene Jeanne Dubois, 78 ans, qui resiste aux arnaqueurs grace a un agent LangChain avec synthese vocale et effets sonores.

## Etudiants

- Lea DRUFFIN
- Satya MINGUEZ
- Adrien FOUQUET
- Amaury TISSOT

## Installation

```bash
# Cloner le projet
git clone https://github.com/AmauryTISSOT/langchain_scamming_protector.git
cd langchain_scamming_protector

# Creer et activer l'environnement virtuel
python -m venv .venv
.\.venv\Scripts\activate        # Windows
# source .venv/bin/activate     # Linux/Mac

# Installer les dependances backend
pip install -r requirements.txt

# Configurer les variables d'environnement
cp .env.example .env
# Editer .env et ajouter :
#   GROQ_API_KEY=votre_cle
#   GOOGLE_CREDENTIALS={"type":"service_account",...}  (optionnel, pour la TTS)

# Installer les dependances frontend
cd frontend
npm install
cd ..
```

## Lancement

### Mode web (recommande)

Ouvrir deux terminaux :

```bash
# Terminal 1 : Backend FastAPI
uvicorn server:app --reload --port 8000
```

```bash
# Terminal 2 : Frontend React
cd frontend
npm run dev
```

Puis ouvrir http://localhost:5173 dans le navigateur.

### Mode console

```bash
python main.py
```

## Tests

```bash
pytest tests/ -v
```
