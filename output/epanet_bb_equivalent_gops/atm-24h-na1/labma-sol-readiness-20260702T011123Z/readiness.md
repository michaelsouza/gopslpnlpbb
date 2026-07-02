# labma-sol GOPS readiness

Issue: `michaelsouza/gopslpnlpbb#13`

Generated: `2026-07-02T01:55:29Z`

Status: `ready`

Contract manifest:
`output/epanet_bb_equivalent_gops/atm-24h-na1/labma-sol-readiness-20260702T011123Z/run.json`

This is an environment-readiness smoke run. It uses `atm-24h-na1` with
`NA_max = 1` as the representative contract case and records
`applies_to_cases` for all three EPANET-BB-equivalent GOPS cases. It does not
solve a model, export a schedule, or run an audit.

## Remote repository

- SSH alias: `labma-sol`
- Remote host name: `sol`
- Repository path: `/home/michael/gitrepos/gopslpnlpbb`
- Branch: `bonvin-atm-audit`
- Remote: `git@github.com:michaelsouza/gopslpnlpbb.git`
- Commit at smoke time: `0865c9a61f2ae8969aa7c896259018901850cbd1`
- Dirty worktree recorded by GOPS import probe: `true`
- Dirty detail: `git status --short --branch` showed only the untracked
  generated artifact namespace, `?? output/epanet_bb_equivalent_gops/`.

The branch was pushed to `origin/bonvin-atm-audit` and the `labma-sol` clone
was fast-forwarded to `0865c9a61f2ae8969aa7c896259018901850cbd1` before the
smoke probe ran. The dirty flag is caused by the remote smoke artifact written
under `output/epanet_bb_equivalent_gops/`; no tracked code changes were reported
by the remote status check.

## Runtime smoke

- Local manifest: `output/epanet_bb_equivalent_gops/atm-24h-na1/labma-sol-readiness-20260702T011123Z/run.json`
- Remote smoke copy: `/home/michael/gitrepos/gopslpnlpbb/output/epanet_bb_equivalent_gops/atm-24h-na1/labma-sol-readiness-20260702T011123Z/remote_probe.json`
- Selected Python: `/home/michael/gitrepos/gopslpnlpbb/.venv/bin/python`
- Python version: `3.13.5`
- `gurobipy`: `13.0.2`
- GOPS imports: `Instance`, `convexrelaxation`, `lpnlpbb`
- Python package imports: `pandas 3.0.4`, `numpy 2.5.0`
- Gurobi version: `13.0.2`
- Gurobi license status: `valid`

The smoke check imports the GOPS modules used by `tools/run_candidate_anytown.py`
and starts a `gurobipy.Env(empty=True)` with `OutputFlag=0`. It records license
status only; it does not read, print, copy, or commit license file contents.
Python emitted non-blocking `SyntaxWarning` messages for invalid escape
sequences in `src/primalheuristic.py` docstrings during `lpnlpbb` import; the
imports completed successfully.

## Commands run

```sh
git push origin bonvin-atm-audit
```

```sh
ssh -o BatchMode=yes -o ConnectTimeout=8 labma-sol 'set -eu; repo="$HOME/gitrepos/gopslpnlpbb"; test -d "$repo/.git"; test -z "$(git -C "$repo" status --porcelain)"; git -C "$repo" fetch origin bonvin-atm-audit; git -C "$repo" switch bonvin-atm-audit >/dev/null; git -C "$repo" merge --ff-only origin/bonvin-atm-audit >/dev/null; echo "branch=$(git -C "$repo" branch --show-current)"; echo "commit=$(git -C "$repo" rev-parse HEAD)"; echo "dirty=$(test -n "$(git -C "$repo" status --porcelain)" && echo true || echo false)"'
```

```sh
ssh -o BatchMode=yes -o ConnectTimeout=8 labma-sol 'cd "$HOME/gitrepos/gopslpnlpbb" && mkdir -p output/epanet_bb_equivalent_gops/atm-24h-na1/labma-sol-readiness-20260702T011123Z && ./.venv/bin/python -c '"'"'import importlib, json, os, platform, subprocess, sys; from datetime import datetime, timezone; from pathlib import Path; repo=Path.cwd(); src=repo/"src"; sys.path.insert(0, str(src)); os.chdir(src); names=["gurobipy","instance","convexrelaxation","lpnlpbb","pandas","numpy"]; labels={"gurobipy":"gurobipy","instance":"Instance","convexrelaxation":"convexrelaxation","lpnlpbb":"lpnlpbb","pandas":"pandas","numpy":"numpy"}; mods={name: importlib.import_module(name) for name in names}; gp=mods["gurobipy"]; env=gp.Env(empty=True); env.setParam("OutputFlag",0); env.start(); modules={labels[name]: {"module": name, "file": getattr(mod, "__file__", None), "version": getattr(mod, "__version__", None)} for name, mod in mods.items()}; payload={"generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"), "host": {"ssh_alias":"labma-sol", "hostname": platform.node(), "platform": platform.platform()}, "repository": {"path": str(repo), "branch": subprocess.check_output(["git","branch","--show-current"], text=True).strip(), "commit": subprocess.check_output(["git","rev-parse","HEAD"], text=True).strip(), "dirty": bool(subprocess.check_output(["git","status","--porcelain"], text=True).strip()), "remote_origin_url": subprocess.check_output(["git","remote","get-url","origin"], text=True).strip()}, "python": {"executable": sys.executable, "version": sys.version, "prefix": sys.prefix}, "solver": {"name":"Gurobi", "gurobipy_version": ".".join(map(str, gp.gurobi.version())), "gurobi_version":".".join(map(str, gp.gurobi.version())), "license_status":"valid"}, "gops_import_surface": {"source_path": str(src), "modules": modules}}; path=repo/"output/epanet_bb_equivalent_gops/atm-24h-na1/labma-sol-readiness-20260702T011123Z/remote_probe.json"; path.write_text(json.dumps(payload, indent=2, sort_keys=True)+"\n", encoding="utf-8"); print(json.dumps(payload, indent=2, sort_keys=True))'"'"''
```

```sh
ssh -o BatchMode=yes -o ConnectTimeout=8 labma-sol 'cd "$HOME/gitrepos/gopslpnlpbb" && git status --short --branch'
```

## Next action

`labma-sol` is ready for later EPANET-BB-equivalent GOPS final-run issues. Use
the selected `.venv` Python and keep final run manifests under
`output/epanet_bb_equivalent_gops/<case_id>/<run_id>/`.
