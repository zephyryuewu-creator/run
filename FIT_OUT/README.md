# Import running FIT files

Upload original `.fit` files for the runs you want to publish here. A commit to
`master` starts **Publish GitHub Pages**. To rerun it yourself, go to **Actions →
Publish GitHub Pages → Run workflow**, select `master`, and confirm.

Keep historical FIT files in this folder. Each build scans all files and merges
them with the Excel and Nike records. Copies of the same file count once, even
if renamed. A run with GPS can appear in **Tracks**; a run without GPS still
appears in **Run Log** and the totals. Check the **Merge running FIT files** step
for possible duplicates or decoding errors. A damaged file stops that
publication, leaving the last successful site live.

This is a public repository. Upload only files whose contents, including any
precise location or heart-rate data, you want to make public.
