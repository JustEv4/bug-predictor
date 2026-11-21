# Bug Predictor — Architecture MVP (v2, dataset Defectors)

## 1. Objectif et périmètre

Bug Predictor estime le risque qu'un fichier Python soit associé à des défauts, à partir du contenu du code source et d'un modèle de Machine Learning entraîné sur le dataset **Defectors: A Large Scale Python Dataset for Defect Prediction**.

- Dataset : https://zenodo.org/records/7708984
- DOI : https://doi.org/10.5281/zenodo.7708984
- Format distribué : archive ZIP contenant des données Apache Parquet.

Defectors contient environ 213 000 fichiers source Python. Les champs documentés comprennent notamment `datetime`, `commit`, `repo`, `filepath`, `content`, `methods` et `induce bug`.

**Périmètre du MVP :**
- entraînement hors ligne à partir des données Defectors ;
- construction d'une cible binaire au niveau fichier à partir des annotations ;
- extraction de caractéristiques à partir du contenu Python ;
- prédiction pour un nouveau fichier `.py` fourni par l'utilisateur ;
- affichage d'une classe et d'un score lorsque le modèle le permet.

Le MVP ne réalise pas l'analyse d'un dépôt Git complet et ne prédit pas les défauts au niveau ligne. Le résultat est une estimation statistique, pas une certitude qu'un défaut existe.

## 2. Architecture logique

### 2.1 Entraînement hors ligne

1. Le module de chargement lit les fichiers Parquet de Defectors.
2. Le validateur vérifie les colonnes et les types attendus.
3. Le préparateur construit le label fichier à partir de `induce bug`, selon la règle documentée dans le contrat des données.
4. Le contenu Python est transmis au pipeline d'extraction de caractéristiques.
5. Les données sont séparées en ensembles d'entraînement, validation et test, en tenant compte des dépôts/commits pour limiter les fuites.
6. Le prétraitement et le modèle sont ajustés uniquement sur les données d'entraînement.
7. Les modèles sont comparés avec Precision, Recall, F1-score et ROC-AUC.
8. Le pipeline complet (extraction, prétraitement, modèle et configuration) est sauvegardé et versionné.

### 2.2 Prédiction en ligne

1. L'utilisateur importe un fichier Python `.py` depuis l'interface.
2. L'API Flask vérifie le type, la taille et l'encodage du fichier.
3. Le composant d'extraction calcule les mêmes caractéristiques que pendant l'entraînement.
4. Le service de prédiction charge le pipeline sauvegardé et applique les transformations apprises.
5. Le modèle calcule la classe et, si disponible, un score/probabilité.
6. Le classificateur convertit le score en niveau faible, moyen ou élevé, selon des seuils validés.
7. L'interface affiche le résultat et les éventuels avertissements.

Un fichier illisible, vide, trop volumineux ou incompatible entraîne une erreur explicite et aucune prédiction.

## 3. Architecture physique Python

- `app/` : point d'entrée Flask, routes, réception des fichiers et réponses HTTP.
- `core/` : chargement du dataset, définition des modèles et interfaces communes.
- `data/raw/` : données Defectors originales (ne pas versionner les archives volumineuses).
- `data/processed/` : données nettoyées et jeux préparés (ne pas versionner les fichiers volumineux).
- `pipeline/` : entraînement, évaluation, extraction des caractéristiques et prédiction.
- `utils/` : validation, prétraitement, métriques et fonctions communes.
- `models/` : pipeline entraîné, paramètres et métadonnées de version.
- `notebooks/` : exploration du dataset et expérimentations.
- `tests/` : tests unitaires et d'intégration.
- `docs/` : documentation, contrat des données et diagrammes.

Les archives volumineuses sont exclues de Git. Le dépôt conserve les instructions de téléchargement, la référence Zenodo, la version utilisée et les informations de licence.

## 4. Flux Machine Learning

### 4.1 Entraînement

Dataset Defectors (Parquet) → validation du schéma → construction du label fichier → extraction des caractéristiques depuis `content` → séparation train/validation/test → ajustement du prétraitement sur train uniquement → entraînement et comparaison des modèles → évaluation → sauvegarde du pipeline complet.

Le découpage doit éviter qu'un même commit ou des observations fortement liées se retrouvent à la fois dans l'entraînement et le test. La stratégie exacte (par dépôt, par commit ou temporelle) doit être choisie et documentée.

### 4.2 Prédiction

Fichier `.py` → validation → extraction des mêmes caractéristiques → chargement du pipeline sauvegardé → transformation avec les paramètres appris → prédiction/score → classification du risque → résultat associé au nom du fichier.

Le pipeline d'extraction et de prétraitement utilisé à l'inférence doit être identique à celui de l'entraînement. Il ne doit jamais être réajusté sur le fichier soumis.

## 5. Contrat entre composants

- L'interface transmet un fichier `.py` à l'API.
- L'API délègue la validation au module correspondant.
- Le service de caractéristiques transforme le code en variables d'entrée selon une méthode documentée.
- Le service de prédiction reçoit les caractéristiques validées, dans le même ordre et avec le même schéma qu'à l'entraînement.
- Le modèle retourne une classe et, si disponible, un score/probabilité.
- L'API associe le résultat au nom du fichier fourni.
- Les erreurs de validation bloquent la prédiction et sont présentées clairement.
- Les artefacts chargés doivent correspondre à la version du schéma de caractéristiques attendu.

## 6. Hypothèses et décisions à confirmer

- Règle candidate : `induce bug` non vide → fichier positif ; liste vide → fichier négatif. Cette règle doit être vérifiée sur les données et avec la documentation de l'article avant de figer les labels.
- Une annotation manquante ou invalide n'est pas automatiquement considérée comme négative.
- La représentation du code reste à choisir : métriques statiques, AST, TF-IDF, embeddings ou combinaison justifiée.
- Les doublons et versions successives d'un même fichier doivent être examinés pour limiter les fuites.
- Les seuils de risque seront définis à partir des résultats de validation.
- L'entrée utilisateur du MVP est un fichier `.py`. Le dataset Parquet est utilisé pour l'entraînement, pas nécessairement par l'utilisateur final.

## 7. Référence

Defectors — https://zenodo.org/records/7708984
