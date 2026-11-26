from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq

DEFAULT_ROOT = Path("/content/drive/MyDrive/BugPredictor/defectors_v2")
ALLOWED_SPLITS = frozenset(("train", "val"))
REQUIRED_COLUMNS = frozenset(("source", "file_defective"))


def _partition_path(split, root=None):
    if split not in ALLOWED_SPLITS:
        raise ValueError(
            f"split doit être train ou val; {split!r} est refusé. "
            "Ce chargeur BUG-24 n'ouvre pas test, réservé à l'audit/évaluation indépendante."
        )
    dataset_root = Path(root) if root is not None else DEFAULT_ROOT
    return dataset_root / "processed" / "time" / f"{split}_prepared.parquet"


def _validate_table(table, split="dataset"):
    missing = REQUIRED_COLUMNS - set(table.schema.names)
    if missing:
        raise ValueError(f"Colonnes requises absentes dans {split}: {sorted(missing)}")

    source_type = table.schema.field("source").type
    if not (pa.types.is_string(source_type) or pa.types.is_large_string(source_type)):
        raise TypeError(f"source doit être de type chaîne; type reçu: {source_type}")

    target_type = table.schema.field("file_defective").type
    if not pa.types.is_integer(target_type):
        raise TypeError(f"file_defective doit être entier; type reçu: {target_type}")

    source_column = table.column("source")
    target_column = table.column("file_defective")
    if source_column.null_count:
        raise ValueError(f"{split}: {source_column.null_count} source(s) null(s)")
    if target_column.null_count:
        raise ValueError(f"{split}: {target_column.null_count} label(s) null(s)")

    labels = target_column.to_pylist()
    invalid = sorted({value for value in labels if value not in (0, 1)})
    if invalid:
        raise ValueError(f"{split}: file_defective doit être binaire {{0,1}}; valeurs invalides: {invalid[:10]}")

    if "row_id" in table.schema.names and table.column("row_id").null_count:
        raise ValueError(f"{split}: row_id contient des valeurs nulles")
    return table


def load_split(split, root=None):
    """Charge tout un split train ou val; n'ouvre volontairement jamais test."""
    path = _partition_path(split, root=root)
    if not path.is_file():
        raise FileNotFoundError(f"Fichier préparé introuvable: {path}. Exécutez d'abord le notebook 03.")
    return _validate_table(pq.read_table(path), split=split)


def iter_split_batches(split, batch_size=512, root=None):
    """Itère train ou val par lots pour limiter la mémoire; test est refusé."""
    if not isinstance(batch_size, int) or batch_size <= 0:
        raise ValueError("batch_size doit être un entier strictement positif")
    path = _partition_path(split, root=root)
    if not path.is_file():
        raise FileNotFoundError(f"Fichier préparé introuvable: {path}. Exécutez d'abord le notebook 03.")
    parquet_file = pq.ParquetFile(path)
    missing = REQUIRED_COLUMNS - set(parquet_file.schema_arrow.names)
    if missing:
        raise ValueError(f"Colonnes requises absentes dans {split}: {sorted(missing)}")
    for batch in parquet_file.iter_batches(batch_size=batch_size):
        yield _validate_table(batch, split=split)


def to_xy(table):
    """Retourne uniquement X=source et y=file_defective; les métadonnées sont ignorées."""
    _validate_table(table)
    X = table.column("source").to_pylist()
    y = [int(value) for value in table.column("file_defective").to_pylist()]
    return X, y


def iter_xy(split, batch_size=512, root=None):
    """Itère des couples (X, y) pour train/val, sans charger le split entier."""
    for batch in iter_split_batches(split, batch_size=batch_size, root=root):
        yield to_xy(batch)


def load_train_validation(root=None):
    """Charge les seuls splits autorisés pour le travail train/validation de Sprint 2."""
    return load_split("train", root=root), load_split("val", root=root)
