# labma-sol GOPS readiness

Issue: `michaelsouza/gopslpnlpbb#13`

Generated: `2026-07-01T23:47:26.874424Z`

Status: `ready`

## Remote repository

- SSH alias: `labma-sol`
- Remote host name: `sol`
- Repository path: `/home/michael/gitrepos/gopslpnlpbb`
- Branch: `bonvin-atm-audit`
- Remote: `git@github.com:michaelsouza/gopslpnlpbb.git`
- Commit: `f77cfeea82879137ddc877ca2ffe86427ad92762`
- Dirty worktree after smoke probe: `false`

The remote clone was initially on `master` at
`34654f4edb6bd2ad6a41206e594594b01af082f4`. Its clean worktree was switched to
`bonvin-atm-audit` and fast-forwarded to `origin/bonvin-atm-audit`.

## Runtime smoke

- Smoke artifact: `output/epanetbb_gops_labma_sol_smoke.json`
- Remote smoke copy: `/tmp/epanetbb_gops_labma_sol_smoke.json`
- Selected Python: `/home/michael/gitrepos/gopslpnlpbb/.venv/bin/python`
- Python version: `3.13.5`
- `gurobipy`: `13.0.2`
- Gurobi version: `13.0.2`
- Gurobi license status: `valid`
- `gurobi_cl` on `PATH`: not present

The smoke check starts a `gurobipy.Env(empty=True)` with `OutputFlag=0`. It
records license status only; it does not read, print, copy, or commit license
file contents.

## Commands run

```sh
ssh -o BatchMode=yes -o ConnectTimeout=8 labma-sol 'printf "host="; hostname; printf "user="; id -un; printf "pwd="; pwd'
```

```sh
ssh -o BatchMode=yes -o ConnectTimeout=8 labma-sol 'for d in "$HOME/gitrepos/gopslpnlpbb" "$HOME/gopslpnlpbb" "$HOME/src/gopslpnlpbb" "$HOME/git/gopslpnlpbb"; do if [ -d "$d/.git" ]; then echo "repo_path=$d"; git -C "$d" branch --show-current; git -C "$d" remote -v; git -C "$d" rev-parse HEAD; git -C "$d" status --porcelain; fi; done; echo "python_path=$(command -v python3 || true)"; python3 --version 2>&1 || true; echo "gurobi_cl_path=$(command -v gurobi_cl || true)"'
```

```sh
ssh -o BatchMode=yes -o ConnectTimeout=8 labma-sol 'set -eu; repo="$HOME/gitrepos/gopslpnlpbb"; test -d "$repo/.git"; test -z "$(git -C "$repo" status --porcelain)"; git -C "$repo" fetch origin bonvin-atm-audit; if git -C "$repo" show-ref --verify --quiet refs/heads/bonvin-atm-audit; then git -C "$repo" switch bonvin-atm-audit; git -C "$repo" merge --ff-only origin/bonvin-atm-audit; else git -C "$repo" switch --track -c bonvin-atm-audit origin/bonvin-atm-audit; fi; echo "branch=$(git -C "$repo" branch --show-current)"; echo "commit=$(git -C "$repo" rev-parse HEAD)"; echo "dirty=$(test -n "$(git -C "$repo" status --porcelain)" && echo true || echo false)"'
```

```sh
ssh -o BatchMode=yes -o ConnectTimeout=8 labma-sol 'cd "$HOME/gitrepos/gopslpnlpbb" && python3 -' > output/epanetbb_gops_labma_sol_smoke.json
```

The final command used an inline Python probe to inspect the remote repository,
candidate Python interpreters, `gurobipy`, and Gurobi license startup status,
then wrote the same JSON to `/tmp/epanetbb_gops_labma_sol_smoke.json` on
`labma-sol`.

## Next action

`labma-sol` is ready for later EPANET-BB-equivalent GOPS final-run issues. Use
the selected `.venv` Python on commit
`f77cfeea82879137ddc877ca2ffe86427ad92762` unless a later issue updates the
target branch or commit.
