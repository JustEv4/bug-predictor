# Bug Predictor — Contrat des données (v2, dataset Defectors)

## 1. Source et unité d'analyse

**Dataset :** Defectors: A Large Scale Python Dataset for Defect Prediction  
**Zenodo :** https://zenodo.org/records/7708984  
**DOI :** 10.5281/zenodo.7708984  
**Format :** archive ZIP contenant des données au format Apache Parquet et des fichiers YAML complémentaires.

Defectors permet des travaux de prédiction au niveau ligne et Just-In-Time. Pour notre MVP, l'équipe retient la **prédiction au niveau fichier Python**. L'unité d'analyse exacte doit être vérifiée dans les fichiers Parquet : une observation est associée à un fichier/contenu et à un contexte de commit.

## 2. Champs documentés

Les champs ci-dessous sont décrits dans la documentation de Defectors. Vérifier les noms et types réels dans les fichiers téléchargés avant d'implémenter le chargeur.

| Champ       | Type documenté | Signification                                           | Rôle envisagé                      |
|-------------|----------------|--------------------------------------------------------------------|-------------------------|
| `datetime`  | DateTime     | Date/heure du committeur avec fuseau horaire                         |   Métadonnée temporelle |
| `commit`    | chaîne       | Hash du commit                                      | Identifiant / regroupement pour le split |
| `repo`      | chaîne       | Nom du dépôt/projet                                  | Métadonnée / regroupement pour le split |
| `filepath`  | chaîne       | Chemin du fichier modifié                                             | Identifiant du fichier |
| `content`   | chaîne       | Diff pour JIT ; contenu du fichier après commit pour la prédiction fichier | Entrée principale |
| `methods`   | liste de chaînes | Méthodes du fichier concernées par le commit | Métadonnée ou caractéristique expérimentale |
| `induce bug`| liste d'entiers | Numéros des lignes associées au code défectueux | Source candidate du label fichier |

`induce bug` est une annotation au niveau ligne, pas une colonne binaire prête à l'emploi. La règle de conversion en label fichier doit être définie et vérifiée.

## 3. Deux schémas d'utilisation

### 3.1 Données d'entraînement

Le jeu d'entraînement est construit à partir de Defectors :
- `content` sert à extraire les caractéristiques du code ;
- `induce bug` sert à construire la cible fichier ;
- `repo`, `commit`, `filepath` et `datetime` servent au traçage et à l'organisation du découpage ;
- `methods` peut être conservé comme information complémentaire. Son usage comme variable d'entrée doit être justifié et reproductible à l'inférence.

**Règle candidate à valider :**
- liste `induce bug` non vide → label positif (défectueux) ;
- liste `induce bug` vide → label négatif (non défectueux) ;
- valeur manquante, invalide ou ambiguë → observation à examiner/exclure, pas automatiquement négative.

Cette règle doit être confrontée à la documentation de l'article et à des exemples réels avant de figer les labels.

### 3.2 Données de prédiction

Pour le MVP, l'utilisateur fournit un fichier source Python `.py` :
- son contenu est lu et validé ;
- les mêmes caractéristiques que pendant l'entraînement sont extraites ;
- aucun `induce bug` ni label n'est requis ;
- le nom du fichier est conservé pour rattacher le résultat à l'entrée.

Le dataset Parquet sert à l'entraînement et à l'évaluation. L'utilisateur final n'a pas à fournir un Parquet pour chaque prédiction.

## 4. Construction des caractéristiques

Le champ `content` contient le contenu du fichier pour la prédiction au niveau fichier. L'équipe doit choisir et documenter une représentation :
- métriques statiques calculées à partir du code ;
- caractéristiques syntaxiques extraites avec l'AST Python ;
- représentation textuelle (par exemple TF-IDF) ;
- embeddings de code ;
- ou combinaison justifiée.

Le code d'extraction, le vocabulaire, les encodeurs, les paramètres de normalisation et le modèle doivent être identiques entre entraînement et prédiction et sauvegardés dans un pipeline reproductible.

Par défaut, `repo`, `commit`, `filepath` et `datetime` ne sont pas des variables prédictives : ils peuvent créer des raccourcis ou des fuites. Leur utilisation éventuelle doit être justifiée. Ils restent utiles pour le traçage et le découpage.

## 5. Règles de validation

1. Les fichiers Parquet doivent être lisibles et conformes au schéma attendu.
2. `content` et `induce bug` doivent être présents pour construire le jeu d'entraînement.
3. Les types doivent correspondre aux types documentés ; les valeurs non conformes sont signalées.
4. Les contenus Python vides ou illisibles sont exclus ou traités selon une règle documentée.
5. Les valeurs manquantes de `induce bug` ne sont pas assimilées automatiquement à une liste vide.
6. Les doublons et versions successives d'un même fichier doivent être examinés.
7. Le jeu de test ne sert pas à ajuster les transformations, choisir les variables ou régler les seuils.
8. Un fichier `.py` soumis en prédiction doit être lisible, non vide et respecter les limites de taille définies.
9. Un fichier invalide ne produit aucune prédiction.

## 6. Découpage et prévention des fuites

Un même dépôt, commit ou fichier peut apparaître dans plusieurs observations. Un découpage aléatoire ligne par ligne peut donc produire des performances artificiellement optimistes.

L'équipe doit identifier les relations entre observations, choisir un split groupé (par dépôt/commit) ou temporel adapté à l'objectif, vérifier l'absence de groupes interdits entre train et test et ajuster le prétraitement uniquement sur train. La stratégie et ses limites doivent être documentées.

## 7. Sortie de prédiction

Pour chaque fichier :
- nom du fichier ;
- classe prédite (défectueux / non défectueux), si disponible ;
- score/probabilité estimée, si disponible ;
- niveau de risque faible/moyen/élevé, uniquement après validation et justification des seuils.

Le score est une estimation statistique, pas une certitude qu'un défaut existe.

## 8. Cohérence entraînement / prédiction

Le même code d'extraction, le même schéma, le même ordre de variables et les mêmes transformations doivent être utilisés dans les deux phases. Les transformations sont ajustées uniquement sur train, sauvegardées avec le modèle, puis réutilisées sans réapprentissage en prédiction.

## 9. Informations à compléter après exploration

- Version exacte du dataset et date de téléchargement :
- Noms des fichiers Parquet utilisés :
- Schéma réel vérifié (colonnes et types) :
- Règle définitive de construction du label fichier :
- Traitement des annotations manquantes :
- Méthode d'extraction des caractéristiques :
- Variables effectivement retenues :
- Stratégie train/validation/test et regroupement :
- Traitement des doublons et versions successives :
- Métriques et seuils de décision :
- Licence et conditions de réutilisation vérifiées sur Zenodo :
