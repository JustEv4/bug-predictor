# Bug Predictor — labs Colab du Sprint 2

Ce dossier regroupe les notebooks de préparation des données et de validation du chargeur réalisés pour le Sprint 2, ainsi que les copies exécutées disponibles et les livrables BUG-19/BUG-24. Le jeu de données est **Defectors v2** (Zenodo, DOI [10.5281/zenodo.7708984](https://doi.org/10.5281/zenodo.7708984)).

## Ordre d’exécution

1. `01_telecharger_defectors_v2.ipynb` — télécharger et inventorier le jeu de données officiel.
2. `02_auditer_partitions_time.ipynb` — examiner les schémas, labels et partitions temporelles `train`, `val`, `test`.
3. `03_preparer_train_validation.ipynb` — préparer les exports d’entraînement et de validation; le contenu du split `test` n’est pas exporté.
4. `04_chargeur_tests_bug24.ipynb` — construire et tester le chargeur sur train/validation, sans utiliser le split test.

Les versions exécutées sont sous `executed/`, avec le module et les tests de validation BUG-24. `BUG-19_rapport_audit.md` et `BUG-19_rapport_audit_corrige.pdf` consignent l’audit qualité disponible.

## Prudence sur les partitions

L’audit a signalé 98 hashes de contenu exacts et 5 379 couples `(repo, filepath)` présents dans plusieurs partitions. Ces agrégats constituent un risque à examiner, mais ne prouvent pas à eux seuls une fuite. Avant l’entraînement ou l’évaluation finale, examiner les recouvrements et documenter la décision de séparation. Le split `test` doit rester réservé à l’évaluation finale, après verrouillage du modèle et du seuil sur validation.

## Limites

Le label historique indique une association avec des défauts passés; il ne certifie pas qu’un fichier contient actuellement un bug ni qu’il en aura un. La provenance, les limites des labels SZZ/PyDriller et les règles de préparation sont détaillées dans le rapport BUG-19.
