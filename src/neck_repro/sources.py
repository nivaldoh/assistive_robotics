"""Read the supplied MATLAB v7.3 data, including the pinned MCOS object layout.

This is deliberately a decoder for this dataset, not a general MATLAB object
reader. MCOS names and property records determine mappings; HDF reference names
and undocumented anatomical substring guesses do not. See docs/source_mapping.md.
"""
from hashlib import sha256
from pathlib import Path
import json
import subprocess
import zipfile

import h5py
import numpy as np

OBJECT_HASH = "fc5c00c6cf33c79432786e34e1d4fc92f6f70373bfb1d5688d55c4dc5eae7e26"
ARCHIVE_URL = "https://data.mendeley.com/public-api/zip/jm5dhwwmyd/download/2"


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def read_node(node):
    """Reverse MATLAB/HDF dimensions once; dereference cells and UTF-16 chars."""
    if isinstance(node, h5py.Group):
        return {k: read_node(v) for k, v in node.items() if not k.startswith("#")}
    a = node[()]
    if h5py.check_dtype(ref=node.dtype):
        values = np.empty(a.shape, dtype=object)
        for i in np.ndindex(a.shape):
            values[i] = read_node(node.file[a[i]])
        return values.T.squeeze().tolist()
    if node.attrs.get("MATLAB_class") == b"char":
        return a.T.astype("<u2").tobytes().decode("utf-16le")
    return a.T.squeeze()


def read_mat(path):
    with h5py.File(path) as f:
        return read_node(f)


def read_model_objects(path):
    if digest(path) != OBJECT_HASH:
        raise ValueError("ModelObjects.mat changed; inspect MCOS layout before decoding")
    with h5py.File(path) as f:
        refs = f["#subsystem#/MCOS"][()].ravel()
        raw = f[refs[0]][()].tobytes()
        header = np.frombuffer(raw[:40], dtype="<u4")
        if header[0] != 4:
            raise ValueError("Unsupported MCOS metadata version")
        names = raw[40:int(header[2])].rstrip(b"\0").decode().split("\0")
        if len(names) != header[1] or names[-1] != "ModelCase":
            raise ValueError("Unexpected serialized class")
        # Property section begins with two zero words, then 12 counted records.
        cursor = int(header[5]) + 8
        objects, audit = [], []
        while cursor < int(header[6]):
            count = int.from_bytes(raw[cursor:cursor + 4], "little")
            cursor += 4
            triples = np.frombuffer(raw[cursor:cursor + count * 12], "<u4").reshape(-1, 3)
            cursor += count * 12
            if count != 15 or not np.all(triples[:, 1] == 1):
                raise ValueError("Unexpected MCOS property encoding")
            obj, paths = {}, {}
            for name_id, _, value_id in triples:
                name = names[int(name_id) - 1]
                node = f[refs[int(value_id) + 2]]
                obj[name] = read_node(node)
                paths[name] = node.name
            objects.append(obj)
            audit.append(paths)
        if cursor != header[6] or len(objects) != 12:
            raise ValueError("Incomplete object decoding")
        # Cell payload: magic, version, rows, columns, object ID, class ID.
        cells = f["gobj"][()].T
        result = []
        for i in range(cells.shape[0]):
            row = []
            for j in range(cells.shape[1]):
                payload = read_node(f[cells[i, j]])
                if list(payload[:4]) != [3707764736, 2, 1, 1] or payload[5] != 1:
                    raise ValueError("Unexpected scalar ModelCase cell payload")
                obj_id = int(payload[4]) - 1
                row.append({**objects[obj_id], "source_paths": audit[obj_id]})
            result.append(row)
        return result


def fetch(root):
    """Cache official archive and paper artifacts; never replace differing originals."""
    root = Path(root)
    manifest = json.loads((root / "provenance/manifest.json").read_text())
    for artifact in manifest["downloads"]:
        path = root / artifact["path"]
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            temp = path.with_suffix(path.suffix + ".download")
            subprocess.run(["curl", "--fail", "--location", "--silent", "--show-error",
                            "--max-time", "90", artifact["url"], "-o", str(temp)], check=True)
            if artifact.get("sha256") and digest(temp) != artifact["sha256"]:
                temp.unlink()
                raise ValueError(f"Download checksum mismatch: {path.name}")
            temp.rename(path)
        if artifact.get("sha256") and digest(path) != artifact["sha256"]:
            raise ValueError(f"Cached original changed: {path}")
    with zipfile.ZipFile(root / "data/original/jm5dhwwmyd-v2.zip") as z:
        for name in z.namelist():
            rel = Path(*Path(name).parts[1:])
            if rel.is_absolute() or ".." in rel.parts:
                raise ValueError("Unsafe archive member")
            path = root / "data/original/jm5dhwwmyd-v2" / rel
            data = z.read(name)
            if path.exists() and path.read_bytes() != data:
                raise ValueError(f"Refusing to replace changed original: {path}")
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                path.write_bytes(data)
    verify_sources(root)


def verify_sources(root):
    manifest = json.loads((Path(root) / "provenance/manifest.json").read_text())
    for item in manifest["dataset_files"]:
        path = Path(root) / item["path"]
        if not path.exists():
            raise FileNotFoundError(f"Missing {path}; run: uv run neck-repro fetch")
        if digest(path) != item["sha256"]:
            raise ValueError(f"Original file checksum mismatch: {path}")
