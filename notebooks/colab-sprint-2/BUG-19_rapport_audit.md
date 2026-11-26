# BUG-19 — Rapport d’audit de qualité et de recouvrement

**Projet :** Bug Predictor — Defectors v2<br>
**Sprint :** Sprint 2 — Données & prétraitement<br>
**Date du rapport :** 25 novembre 2026<br>
**Source des preuves :** sorties des notebooks Colab 01, 02 et 03 fournis dans `notebooks.zip` par l’utilisatrice.

## 1. Objet et périmètre

Ce document consigne les résultats observés lors de l’exécution de `02_auditer_partitions_time.ipynb` sur la famille temporelle `line_bug_prediction_splits/time` de Defectors v2, puis les résultats de préparation train/validation du notebook 03. L’audit porte sur les trois fichiers présents dans cette famille : train, validation et test. Il ne couvre pas les autres familles de partitions du ZIP Zenodo (par exemple `random` ou `jit_bug_prediction_splits`).

Le split test a été lu **uniquement pour l’audit**. Il n’a pas été utilisé pour entraîner, ajuster ou préparer un modèle. Aucun modèle ni résultat de performance n’a été produit.

## 2. Méthode exécutée

Le notebook 02 a ouvert les fichiers Parquet par lots, vérifié les champs logiques de premier niveau avec `schema_arrow.names`, puis calculé les statistiques de contenu et de labels. Pour les contenus non nuls, il a contrôlé les valeurs de `lines` comme indices de lignes 1-based dans le texte décodé. Il a aussi calculé des SHA-256 du contenu exact et repéré les couples `(repo, filepath)` présents dans plusieurs splits.

La cible fichier utilisée par le notebook 03 est dérivée ainsi : `file_defective = 1` si `lines` est non vide, sinon `0`. Les lignes dont `content` est nul sont écartées de train et validation, car le modèle textuel exige un code source disponible. Les métadonnées `repo`, `filepath`, `datetime`, `commit` et `row_id` ne sont pas des caractéristiques du modèle.

## 3. Schéma et interprétation des labels

Le schéma logique Parquet observé dans les trois splits expose les champs suivants :

| Champ | Type observé | Rôle/documentation |
|---|---|---|
| `datetime` | timestamp UTC, précision microseconde | Date de l’observation/commit; métadonnée pour l’audit temporel |
| `commit` | chaîne | Identifiant du commit; métadonnée |
| `repo` | chaîne | Dépôt source; métadonnée |
| `filepath` | chaîne | Chemin du fichier; métadonnée |
| `content` | binaire | Source décodée en UTF-8 avec remplacement des octets invalides |
| `methods` | liste de chaînes | Méthodes détectées dans le fichier |
| `lines` | liste d’entiers `int64` | Indices de lignes associés au défaut dans le split inspecté |
| `__index_level_0__` | entier `int64` | Index sérialisé |

L’article nomme la liste d’indices de lignes fautives `induce_bug`, tandis que les fichiers Parquet examinés l’appellent `lines`; le champ littéral `induce_bug` n’est pas présent dans ce schéma. L’audit a traité `lines` comme la liste de labels de lignes et a dérivé `file_defective = 1` lorsque cette liste est non vide, sinon `0`. La règle a été appliquée dans le notebook 03 et les sorties train/validation ont été vérifiées comme binaires.

Les sorties indiquent zéro label nul et n’affichent pas de compteurs non nuls pour les valeurs de label non entières ou hors bornes, pour les lignes où `content` est disponible. Les listes vides sont comptées comme négatives; les listes non vides comme positives. L’absence du champ publié sous le nom `induce_bug` est une différence de nom documentée, non une preuve d’absence de labels.

### Origine et bruit potentiel des labels

Selon l’article Defectors, les étiquettes proviennent d’une analyse historique des commits correcteurs et de l’application de méthodes de type SZZ/PyDriller pour identifier des lignes potentiellement à l’origine de défauts. Des filtres visent à réduire certains faux positifs, mais le présent audit n’a pas rejoué cette chaîne de labellisation ni vérifié chaque commit et chaque filtre pour tous les dépôts. La liste publiée doit donc être traitée comme une annotation historique susceptible de bruit, et non comme une preuve qu’un bug est présent ou futur. Les distributions ci-dessous proviennent des fichiers effectivement audités, pas des statistiques globales publiées.

## 4. Résultats de qualité

### Lignes et contenu

| Split | Lignes lues | Contenu non nul | Contenu nul |
|---|---:|---:|---:|
| train | 185 369 | 182 680 | 2 689 |
| validation | 10 000 | 9 768 | 232 |
| test | 10 000 | 9 956 | 44 |
| **Total audité** | **205 369** | **202 404** | **2 965** |

### Répartition des labels

| Split | Labels non vides (positifs) | Labels vides (négatifs) |
|---|---:|---:|
| train | 83 139 | 102 230 |
| validation | 1 246 | 8 754 |
| test | 1 246 | 8 754 |
| **Total audité** | **85 631** | **119 738** |

### Décodage UTF-8

| Split | Lignes nécessitant un remplacement UTF-8 |
|---|---:|
| train | 122 |
| validation | 4 |
| test | 0 |
| **Total audité** | **126** |

Les comptes de labels positifs et négatifs totalisent les lignes de chaque split; aucun label nul n’apparaît dans les sorties de l’audit. Le code de l’audit contrôle le type entier et les bornes de `lines` lorsque le contenu est disponible; aucun compteur d’étiquette non entière ou hors bornes n’est présent dans les résultats imprimés. Les lignes à contenu nul ne permettent pas une vérification de bornes par rapport au code, mais aucune ligne positive à contenu nul n’a été signalée.

### Résultat de la préparation

Le notebook 03 a écrit les exports suivants :

| Export | Lignes d’entrée | Lignes écrites | Contenu nul écarté | Positifs écrits | Négatifs écrits |
|---|---:|---:|---:|---:|---:|
| train préparé | 185 369 | 182 680 | 2 689 | 83 139 | 99 541 |
| validation préparée | 10 000 | 9 768 | 232 | 1 246 | 8 522 |

Le notebook 03 n’a pas exporté le split test. Les sorties confirment la règle `X = source` et `y = file_defective`; elles ne constituent pas une évaluation de modèle.

## 5. Résultats de recouvrement

| Contrôle | Résultat observé | Unité comptée |
|---|---:|---|
| Contenus exacts dont le SHA-256 apparaît dans plusieurs splits | 98 | Hashes uniques de contenus non nuls partagés entre splits, pas nombre de lignes |
| Couples `(repo, filepath)` présents dans plusieurs splits | 5 379 | Couples uniques partagés entre splits, pas nombre de lignes |
| Doublons de contenu à l’intérieur de train | 3 157 | Lignes au-delà du nombre de hashes distincts, contenu non nul |
| Doublons de contenu à l’intérieur de validation | 147 | Idem |
| Doublons de contenu à l’intérieur de test | 282 | Idem; observation d’audit seulement |

### Interprétation

Les **98 hashes exacts partagés** sont le signal le plus direct de contenus identiques entre partitions et méritent un examen avant toute évaluation. Le rapport agrégé ne donne toutefois pas les identifiants de groupe, les labels associés, ni les dates/commits correspondants; il ne permet donc pas de conclure sur le nombre d’exemples affectés ni sur l’effet de ces recouvrements sur une métrique.

Les **5 379 couples dépôt-chemin partagés** ne démontrent pas, à eux seuls, une fuite de données. Dans un découpage temporel, un même fichier peut légitimement apparaître dans plusieurs périodes après des modifications. Il faut distinguer les versions distinctes d’un même chemin des duplications exactes de contenu, puis examiner l’ordre temporel des commits.

Les répétitions à l’intérieur d’un split indiquent également que plusieurs lignes de l’échantillon ont un contenu identique; elles ne signifient pas nécessairement des erreurs de données, mais devraient être décrites pour interpréter les analyses futures.

## 6. Conclusion et suites recommandées

L’exécution des notebooks 02 et 03 a confirmé le schéma logique, produit les statistiques sur les trois fichiers du split temporel et créé les exports train/validation. Les cellules correspondantes ont donc bien été exécutées dans le ZIP remis.

**Conclusion BUG-19 : audit calculé et documenté; recouvrements à examiner avant d’affirmer que le découpage est sans fuite.** Le résultat agrégé suffit à signaler un risque à examiner, mais pas à déclarer le jeu de test contaminé ni propre.

Avant l’évaluation indépendante prévue dans un sprint ultérieur :

1. conserver les 98 groupes de SHA-256 partagés avec les splits et labels associés; décider si les copies exactes doivent être exclues, regroupées ou traitées comme une limite;
2. analyser les 5 379 couples `(repo, filepath)` par split, date et commit afin de confirmer qu’il s’agit de versions temporelles attendues;
3. documenter la politique retenue et ne jamais utiliser le test pour l’entraînement, le réglage des hyperparamètres, la calibration ou le choix du seuil;
4. garder les contenus UTF-8 réparés et les lignes à contenu nul traçables dans le manifeste.

Ce document ne change pas l’état Jira de BUG-19. Il reflète les sorties d’exécution fournies et ne prétend pas que les recouvrements ont déjà été résolus.

## 7. Provenance

- Dataset : [Defectors v2 — Zenodo](https://zenodo.org/records/7708984), DOI [10.5281/zenodo.7708984](https://doi.org/10.5281/zenodo.7708984).
- Fichiers : `line_bug_prediction_splits/time/{train,val,test}.parquet.gzip`.
- Preuve d’exécution : `notebooks.zip` remis par l’utilisatrice le 25 novembre 2026; le rapport JSON est affiché par la dernière cellule de `02_auditer_partitions_time.ipynb`.
- Test : usage limité à l’audit; aucun entraînement ni réglage sur test.
