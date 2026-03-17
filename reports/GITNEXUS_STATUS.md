# GitNexus Status

## What Was Verified

- `bash scripts/run_gitnexus.sh analyze --help` confirms embeddings are still opt-in
- `refs/vision_opencv` remains indexed successfully
- `refs/slam_toolbox` appears in `gitnexus list`
- `/home/peng/AgentSlam` now appears in `gitnexus list`
- `gitnexus status .` reports the main repo as up to date

## Indexed Repository Evidence

- `vision_opencv`
  - `455` symbols
  - `984` edges
  - `80` clusters
  - `27` flows
- `slam_toolbox`
  - `1111` symbols
  - `1736` edges
  - `415` clusters
- `AgentSlam`
  - indexed path: `/home/peng/AgentSlam`
  - indexed commit: `3b8df71`
  - current commit: `3b8df71`
  - status: `up-to-date`

## Practical Conclusion

- GitNexus is usable for both the main repo and selected refs in the current environment.
- The current index reflects the latest committed tree, not the uncommitted Prompt 4 working tree.
- For future deep code tracing, the main repo no longer needs a separate indexing follow-up before use.

## Recommended Commands

```bash
cd /home/peng/AgentSlam
bash scripts/run_gitnexus.sh analyze .
npx -y gitnexus@latest status .
npx -y gitnexus@latest list
```
