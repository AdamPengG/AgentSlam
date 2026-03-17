# Clone And Index Checklist

## Before Prompt 3

- confirm `refs/` is ignored by `.gitignore`
- confirm `scripts/clone_refs.sh` exists and is executable
- confirm `npx` is available
- confirm network access is available for GitHub cloning
- confirm there is enough disk space for upstream repositories and GitNexus artifacts

## During Prompt 3

- clone or fetch each planned upstream into `refs/`
- keep `refs/` read-only from the perspective of the main repo
- record clone failures individually instead of stopping the whole run
- attempt GitNexus indexing on the main repo and key refs
- record index failures as blockers without hiding clone results

## After Prompt 3

- validate which upstreams cloned successfully
- validate which upstreams require submodules
- validate that indexing status was written to a report
- validate that `docs/upstream/` received repo-specific analysis files
