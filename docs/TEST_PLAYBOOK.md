# Test Playbook

## Validation Layers

### Build Validation

- build the ROS workspace packages that currently exist
- if a package cannot build, document the exact reason and next step

### Unit Validation

- test projection, fusion, export, and query logic with deterministic fixtures
- keep these tests free of GUI and simulator dependencies

### Fixture Or Replay Validation

- require at least one offline data path for Phase 1
- store fixture inputs and generated artifacts in predictable locations

### Smoke Validation

- verify launch/config/script entrypoints exist
- verify topic contracts, asset choices, and no-LiDAR assumptions are documented

### Visual Review Material

- produce JSON or other human-readable artifacts for semantic map outputs
- make it easy for a reviewer to inspect object positions, counts, and query results

## Regression Discipline

- do not mark missing validation as pass
- if a validation path is skipped, record why and what should run next
