"""Conservative output handling: never delete a directory or its contents."""
from __future__ import annotations

import json
from pathlib import Path


def prepare_output(output: str | Path, root: str | Path, overwrite: bool = False,
                   kind: str = "experiment") -> Path:
    """Refuse non-empty destinations unless explicitly permitted.

    Overwrite permission replaces only files subsequently written by the caller;
    it does not remove unrelated or stale files. Repository roots, their parents,
    and Git metadata are never valid destinations, even with permission.
    """
    root = Path(root).resolve()
    destination = Path(output).resolve()
    archive = False
    if destination == root or destination in root.parents or any(part.casefold() == ".git" for part in destination.parts):
        raise ValueError("Output must not be the repository root, an ancestor, or Git metadata")
    if destination.is_relative_to(root):
        relative = destination.relative_to(root)
        protected = {"src", "scripts", "tests", "configs", "data", "report", "historical_v102",
                     "evidence", "outputs", "reference", ".github"}
        if relative.parts[0].casefold() in protected:
            raise ValueError("Source, historical evidence and supplied reference folders are protected outputs")
        if relative.parts[0].casefold() == "corrected_v110" and (
                len(relative.parts) < 2 or not relative.parts[1].casefold().startswith("supplementary_")):
            raise ValueError("Existing corrected reference runs are frozen; choose local_runs/ or supplementary_*")
        archive = relative.parts[0].casefold() == "corrected_v110"
    if destination.exists():
        if not destination.is_dir():
            raise ValueError("Output destination must be a directory")
        if any(destination.iterdir()):
            if not overwrite:
                raise FileExistsError(f"Output directory is not empty: {destination}. Use --overwrite explicitly.")
            if archive:
                raise ValueError("An archived supplementary result is frozen; rerun under local_runs/ instead")
            marker = destination / ".p2_output.json"
            recognised = False
            if marker.is_file():
                try:
                    recognised = json.loads(marker.read_text(encoding="utf-8")) == {"project": "P2", "kind": kind}
                except (ValueError, OSError):
                    pass
            elif kind == "experiment" and (destination / "run_manifest.json").is_file():
                try:
                    old = json.loads((destination / "run_manifest.json").read_text(encoding="utf-8"))
                    recognised = isinstance(old, dict) and old.get("project") == "P2_forecast_to_storage"
                except (ValueError, OSError):
                    pass
            if not recognised:
                raise ValueError("Overwrite requires a recognized output directory of the same experiment type; use a new destination")
    destination.mkdir(parents=True, exist_ok=True)
    (destination / ".p2_output.json").write_text(json.dumps({"project": "P2", "kind": kind}), encoding="utf-8")
    return destination
