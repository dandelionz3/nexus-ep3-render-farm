# nexus-ep3-render-farm

Render farm NEXUS ZERO Episode 3 "THE CHOICE" (60 dtk, 24 fps, 1440 frame).
Eevee via GitHub Actions (setting B7, samples 6). JANGAN dipakai untuk Ep 1
(repo Ep 1: `nexus-render-farm`) atau Ep 2 (`nexus-ep2-render-farm`).

- `pipeline-nexus/` — build_scene / plan / animate / plan.json (md5 identik
  dengan `~/workspace/shorts/nexus-zero-ep3/pipeline/`).
- `.github/workflows/render-nexus-ep3-test.yml` — tes 120 frame
  (S1 hook + S3 ambang + S4 aula memori + S6 scar_wave + S8 twist/end).
- `.github/workflows/render-nexus-ep3-full.yml` — full run 40 job × 72 frame
  (2880 frame 9:16+16:9), Release baru.
