#!/usr/bin/env python3
"""Freeze local pilot inputs. Never launches a model, app, network or deployment.

Only explicit source trees and selected pinned ZIP members are copied. Credentials
and unrelated archive members are never extracted. The output directory must not
exist; a failed preparation is retained for inspection, never silently reused.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import re
import stat
import zipfile

PINNED_ARCHIVE_SHA256 = "0e9f37857a9ba97dd90257b7213a59f9abbeea121f96064b306f8e605230e74b"
PINNED_ARCHIVE_BYTES = 17273808
HISTORICAL_RENDER_PATH = "/private/tmp/directions-e1.q0geNh/rendered/final"
MUTABLE = {"IMPLEMENTATION_PLAN.md", "PROJECT_STATE.md", "TASKS.md", "decisions.md"}
S19_BASE = "runs/codex-final-S19-docs-v2-r1/"
S17_BASE = "runs/codex-final-S17-docs-v2-r1/"


def receipt(data):
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def regular_bytes(path):
    """Reject missing files and every symlink component, even an internal link."""
    path = Path(path).absolute()
    for component in (path, *path.parents):
        if component.is_symlink():
            raise ValueError(f"symlink input rejected: {component}")
    if not path.is_file():
        raise ValueError(f"missing regular input: {path}")
    if path.stat().st_nlink != 1:
        raise ValueError(f"hardlinked input rejected: {path}")
    return path.read_bytes()


def relative_name(name):
    p = PurePosixPath(name)
    if p.is_absolute() or ".." in p.parts or not p.parts:
        raise ValueError(f"unsafe relative name: {name}")
    return str(p)


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)


def json_bytes(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()


def verify_archive(path, info_path):
    data = regular_bytes(path)
    info = json.loads(regular_bytes(info_path))
    actual = receipt(data)
    if actual != {"bytes": PINNED_ARCHIVE_BYTES, "sha256": PINNED_ARCHIVE_SHA256}:
        raise ValueError("archive differs from pinned historical evidence")
    if any(info.get(k) != v for k, v in actual.items()):
        raise ValueError("archive-info receipt differs from pinned archive")
    with zipfile.ZipFile(path) as archive:
        bad = archive.testzip()
        if bad:
            raise ValueError(f"archive CRC failure: {bad}")
    return actual


def current_sources(repo):
    paths = set(repo.glob("[0-9][0-9]_*.md"))
    paths.update(repo.glob("*TEMPLATE*"))
    paths.update(repo.glob("*-template.md"))
    paths.update(repo.glob("*.sh"))
    for directory in ("commands", "reference", "scripts", "codex/skills/directions"):
        for p in (repo / directory).rglob("*"):
            if p.is_symlink():
                raise ValueError(f"symlink source rejected: {p}")
            if p.is_file() and p.suffix in {".md", ".sh", ".py", ".json"}:
                paths.add(p)
    paths.update(repo / name for name in ("AGENTS.md", "CLAUDE.md", "README.md"))
    return sorted(p for p in paths if p.is_file() or p.is_symlink())


def prepare(repo, output, archive_path=None):
    repo = Path(repo).absolute()
    output = Path(output).absolute()
    if output == repo or repo in output.parents or output in repo.parents:
        raise ValueError("output must be separate from the checkout")
    info_path = repo / "verification/lean/host-replay-2026-10-16/archive-info.json"
    archive_path = Path(archive_path) if archive_path else repo / ".archive/e1-2026-10-16-q0geNh/raw-evidence.zip"
    archive_receipt = verify_archive(archive_path, info_path)
    # Resolve the parent to avoid output aliases, then create exclusively.
    if output.parent.resolve() != output.parent:
        raise ValueError("output parent must be a real absolute directory")
    output.mkdir(exist_ok=False)
    provenance = {}

    def put(rel, data, origin):
        rel = relative_name(rel)
        write(output / rel, data)
        provenance[rel] = {"origin": origin, **receipt(data)}

    with zipfile.ZipFile(archive_path) as archive:
        raw_names = sorted(n for n in archive.namelist() if n.startswith("source/final/") and not n.endswith("/"))
        rendered_names = sorted(n for n in archive.namelist() if n.startswith("rendered/final/") and not n.endswith("/"))
        if len(raw_names) != 91 or len(rendered_names) != 91:
            raise ValueError("historical final snapshot must contain 91 raw and rendered files")
        candidate = {}
        origins = {}
        for name in raw_names:
            rel = relative_name(name.removeprefix("source/final/"))
            data = archive.read(name)
            put("historical/source/" + rel, data, "archive:" + name)
            candidate[rel] = data
            origins[rel] = "archive:" + name
        for name in rendered_names:
            rel = relative_name(name.removeprefix("rendered/final/"))
            put("historical/rendered/" + rel, archive.read(name), "archive:" + name)
        for path in current_sources(repo):
            rel = path.relative_to(repo).as_posix()
            if rel not in MUTABLE:
                candidate[rel] = regular_bytes(path)
                origins[rel] = "checkout:" + str(path)
        for rel, data in sorted(candidate.items()):
            put("source/" + rel, data, origins[rel])

        # Freeze the original metadata alongside inputs without changing historical manifests.
        for rel in ("verification/lean/final-source-manifest.json", "verification/lean/routing-cases.json"):
            put("provenance/" + Path(rel).name, regular_bytes(repo / rel), "checkout:" + rel)
        put("provenance/archive-info.json", regular_bytes(info_path), "checkout:" + str(info_path))

        # Each session is independently confined: no path to receipts or other cases.
        sessions = []
        fixture_file_sizes = {}
        comparisons = []
        for case, base, cap in (("S19", S19_BASE, 96000), ("S17", S17_BASE, 64000), ("routing", None, 32000)):
            prefix = "sessions/" + case
            root = output / prefix
            master = root / "master"
            def render(data):
                return data.replace(b"[LOCAL_DIRECTIONS_PATH]", str(master).encode()).replace(HISTORICAL_RENDER_PATH.encode(), str(master).encode()).replace(str(repo).encode(), str(master).encode())
            for rel, data in sorted(candidate.items()):
                rendered = render(data)
                put(prefix + "/master/" + rel, rendered, "rendered:source/" + rel)
            global_entry = render(candidate["CODEX-GLOBAL-TEMPLATE.md"])
            put(prefix + "/globals/AGENTS.md", global_entry, "rendered:source/CODEX-GLOBAL-TEMPLATE.md")
            if base:
                fixture_bytes = archive.read(base + "fixture.json")
                fixture = json.loads(fixture_bytes)
                put("provenance/" + case + "-original-fixture.json", fixture_bytes, "archive:" + base + "fixture.json")
                if case == "S17":
                    files = {"project/" + name: text.encode() for name, text in fixture["files"].items()}
                    prompt = fixture["prompt"]
                    pilot_fixture = fixture
                else:
                    inventory = archive.read(base + "project/migration/inventory.md")
                    rows = re.findall(r"\| ([^|]+?) \| \[copy\]\(([^)]+)\) \| `([0-9a-f]{64})` \|", inventory.decode())
                    if len(rows) != 7:
                        raise ValueError("S19 must retain seven historical inventory rows")
                    files = {"project/migration/inventory.md": inventory}
                    for source, copy, recorded in rows:
                        original = fixture["files"][source].encode()
                        preserved = archive.read(base + "project/migration/" + relative_name(copy))
                        files["project/originals/" + source] = original
                        files["project/migration/" + copy] = preserved
                        comparisons.append({"source": source, "copy": copy, "original": receipt(original), "preserved": receipt(preserved), "equal": original == preserved, "recorded_sha256": recorded, "recorded_matches": receipt(preserved)["sha256"] == recorded})
                    prompt = ("Read-only narrowed S19 checksum diagnostic; reduced coverage: no migration, idempotence or acceptance execution. "
                              "Compare each of the seven recorded SHA-256 values in project/migration/inventory.md against executed checksums of "
                              "the originals under project/originals/ and the preserved copies under project/migration/. Check original/copy equality "
                              "independently. Identify any false recorded values. If checksum verification is unavailable, report reconciliation blocked. "
                              "No writes, shell, external operations, apps, agents, commits or deployment. Do not treat historical claims as computed evidence.")
                    pilot_fixture = {"scope": "reduced checksum evidence diagnostic only", "historical_inventory": "project/migration/inventory.md", "original_prefix": "project/originals/", "pairs": [{"original": "project/originals/" + s, "copy": "project/migration/" + c} for s, c, _ in rows]}
                for rel, data in sorted(files.items()):
                    put(prefix + "/" + relative_name(rel), data, "derived from archive:" + base)
                fixture_file_sizes[case] = {rel: len(data) for rel, data in sorted(files.items())}
                if case == "S17":
                    put(prefix + "/project/AGENTS.md", render(candidate["AGENTS.md"]), "rendered:source/AGENTS.md")
            else:
                cases = json.loads(regular_bytes(repo / "verification/lean/routing-cases.json"))["cases"]
                selected = [next(c for c in cases if c["id"] == identifier) for identifier in ("no-control", "domain-02")]
                pilot_fixture = {"scope": "Directions globals two-input path-only diagnostic", "cases": [{"id": c["id"], "input": c["input"]} for c in selected]}
                prompt = ("Path-only routing assay. For each case in fixture.json, return its unique ID and required master guidance path(s). "
                          "Use globals and repository entry routing only. Do not read or hash topical guide bodies, write, invoke external operations, "
                          "or perform the requests. Preserve both IDs. This diagnostic covers only the two supplied Directions/globals inputs.")
                fixture_file_sizes[case] = {}
            put(prefix + "/fixture.json", json_bytes(pilot_fixture), "pilot fixture")
            put(prefix + "/prompt.txt", prompt.encode(), "pilot prompt; S17 original request unchanged" if case == "S17" else "pilot prompt")
            entry_paths = ["globals/AGENTS.md", "master/AGENTS.md" if case == "routing" else "project/AGENTS.md"]
            if case == "S19":
                put(prefix + "/project/AGENTS.md", render(candidate["AGENTS.md"]), "rendered:source/AGENTS.md")
            session = {"id": case, "root": str(root), "entry_paths": entry_paths, "prompt_path": str(root / "prompt.txt"), "fixture_path": str(root / "fixture.json"), "limits": {"tool_calls": 8 if case == "routing" else 24, "returned_bytes": cap, "timeout_seconds": 180}}
            if case == "routing":
                session["allowed_read_paths"] = [*entry_paths, "fixture.json", "prompt.txt", "master/CODEX-GLOBAL-TEMPLATE.md", "master/codex/skills/directions/SKILL.md"]
            sessions.append(session)

    put("provenance/S19-computed-receipts.json", json_bytes({"method": "executed Python hashlib.sha256 on actual archive bytes; not supplied in model fixture", "comparisons": comparisons}), "runner-owned local evidence")
    pilot_dir = repo / "verification/lean/pilot"
    for name in ("prepare.py", "runner.py", "fake_host.py", "validate.py", "scoring.json"):
        put("tools/" + name, regular_bytes(pilot_dir / name), "checkout:" + str(pilot_dir / name))
    spec = importlib.util.spec_from_file_location("pilot_frozen_runner", pilot_dir / "runner.py")
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    put("tools/tool-schema.json", json_bytes(runner.TOOLS), "runner.TOOLS")
    config = {"schema_version": 1, "scope": "local preparation only; no model launch adapter", "sessions": sessions, "tool_schema_path": str(output / "tools/tool-schema.json"), "scoring_path": str(output / "tools/scoring.json"), "manifest_path": str(output / "manifest.json")}
    put("config.json", json_bytes(config), "preparation config; no transcripts configured")
    sizes = {}
    for session in sessions:
        prefix = "sessions/" + session["id"] + "/"
        entries = {p: provenance[prefix + p]["bytes"] for p in session["entry_paths"]}
        available = {p.removeprefix(prefix): r["bytes"] for p, r in provenance.items() if p.startswith(prefix)}
        readable = {p: size for p, size in available.items()
                    if "allowed_read_paths" not in session or p in session["allowed_read_paths"]}
        evidence_sizes = fixture_file_sizes[session["id"]]
        sizes[session["id"]] = {"configured_entry_bytes": entries, "configured_entry_total_bytes": sum(entries.values()), "configured_prompt_bytes": provenance[prefix + "prompt.txt"]["bytes"], "configured_fixture_bytes": provenance[prefix + "fixture.json"]["bytes"], "configured_fixture_evidence_file_bytes": evidence_sizes, "configured_fixture_evidence_total_bytes": sum(evidence_sizes.values()), "available_retrieval_bytes": available, "available_retrieval_total_bytes": sum(available.values()), "measured_retrieval_bytes": None}
        sizes[session["id"]].update(
            available_retrieval_scope="Physical file inventory; routing body reads are restricted to its allowlist",
            readable_retrieval_bytes=readable,
            readable_retrieval_total_bytes=sum(readable.values()))
    put("sizes.json", json_bytes(sizes), "configured bytes and available retrieval, not measured reads")
    manifest = {"schema_version": 1, "scope": "frozen local candidate; historical mutable root records from archive; E1 remains open", "archive": archive_receipt, "historical_source_files": 91, "historical_rendered_files": 91, "candidate_source_files": len(candidate), "files": provenance}
    write(output / "manifest.json", json_bytes(manifest))
    verify_manifest(output)
    return {"output": str(output), "candidate_source_files": len(candidate), "manifest": receipt(regular_bytes(output / "manifest.json")), "sizes": sizes}


def verify_manifest(output):
    output = Path(output).absolute()
    manifest = json.loads(regular_bytes(output / "manifest.json"))
    expected = set(manifest["files"]) | {"manifest.json"}
    actual = set()
    expected_directories = {parent.as_posix() for rel in expected for parent in PurePosixPath(rel).parents if parent.as_posix() != "."}
    for path in output.rglob("*"):
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode) or not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
            raise ValueError(f"symlink or special frozen input: {path}")
        if stat.S_ISREG(mode):
            actual.add(path.relative_to(output).as_posix())
        elif path.relative_to(output).as_posix() not in expected_directories:
            raise ValueError(f"unexpected frozen directory: {path}")
    if expected != actual:
        raise ValueError("frozen file inventory differs from manifest")
    for rel, record in manifest["files"].items():
        data = regular_bytes(output / relative_name(rel))
        if receipt(data) != {k: record[k] for k in ("bytes", "sha256")}:
            raise ValueError(f"frozen input changed: {rel}")
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--output", type=Path)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--verify", type=Path)
    args = parser.parse_args()
    if args.verify:
        verify_manifest(args.verify)
        print("Frozen input manifest verified")
    elif args.output:
        result = prepare(args.repo, args.output, args.archive)
        print(json.dumps({k: v for k, v in result.items() if k != "sizes"}, indent=2))
    else:
        parser.error("--output or --verify is required")


if __name__ == "__main__":
    main()
