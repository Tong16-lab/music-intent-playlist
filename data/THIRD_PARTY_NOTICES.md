# Third-party data notices and use boundaries

This non-commercial PE6201 course demonstration displays the necessary metadata, project labels, and original Jamendo track-page links for 35 songs. The repository contains no song audio, preview clips, covers, or lyrics. A link opens a third-party page; availability or playback may change.

## MTG-Jamendo source

- Dataset: [MTG-Jamendo official page](https://mtg.github.io/mtg-jamendo-dataset/). Recorded source revision: [`cafd8e20c265ed84f1e61f1c875327971f43a62f`](https://github.com/MTG/mtg-jamendo-dataset/tree/cafd8e20c265ed84f1e61f1c875327971f43a62f). The project recorded a metadata and link review on 2026-10-01.
- Candidate tracks were selected from the revision's [`autotagging_moodtheme.tsv`](https://github.com/MTG/mtg-jamendo-dataset/blob/cafd8e20c265ed84f1e61f1c875327971f43a62f/data/autotagging_moodtheme.tsv). Titles, artists, and source links correspond to the dataset's [`raw.meta.tsv`](https://github.com/MTG/mtg-jamendo-dataset/blob/cafd8e20c265ed84f1e61f1c875327971f43a62f/data/raw.meta.tsv). The catalog retains original track IDs and source mood/theme tags; those are third-party metadata, not original contributions of this project.
- The dataset describes separate terms for code (Apache 2.0), metadata ([CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)), and individual audio tracks. A code license does not authorize reuse of metadata or audio on its own. Attribution, non-commercial, and share-alike conditions relevant to metadata should be respected. This classroom demonstration is not evidence of permission for commercial use.
- Dataset citation: Bogdanov, D., Won, M., Tovstogan, P., Porter, A., & Serra, X. (2019). *The MTG-Jamendo Dataset for Automatic Music Tagging*. Machine Learning for Music Discovery Workshop, ICML 2019. [Paper record](http://hdl.handle.net/10230/42015).

## Track links versus audio permission

The project source document records a check, on 2026-10-01, that the historical per-track license entries in that revision's [`audio_licenses.txt`](https://github.com/MTG/mtg-jamendo-dataset/blob/cafd8e20c265ed84f1e61f1c875327971f43a62f/audio_licenses.txt) matched the selected 35 track IDs. This is a historical dataset record, **not verification of current audio rights**. Current track-level audio permission has not been separately checked; `data/catalog.csv` therefore uses `current_audio_license_status=not_checked` for all 35 tracks. Any future downloading, embedding, redistribution, or commercial use would require permission checks for that specific use. This project only links outward.

`link_identity_status` records whether the source entry and linked page were judged to identify the same track: 32 `matched`, one `minor_spelling_variant`, and two `artist_variant_confirmed` cases, the latter confirmed by the author on 2026-10-02. This is a link-identity judgment, separate from audio permission and playback availability. Source titles and artist names are retained rather than silently replaced with current page spellings.

## Project-specific listening labels

`valence`, `arousal`, `melody_present`, `melodic_surprise`, and the accompanying melody-change notes are project-specific listening labels, not MTG-Jamendo mood/theme tags. The author listened to and reviewed the 35 tracks on 2026-10-01. `label_status=verified` refers to that single-author review; it does not mean multi-annotator agreement or proven recommendation quality. A later listening check disputed one arousal label, which remains visible as a limitation rather than an unrecorded post-evaluation change.

`scripts/export_catalog.py` joins the checked-in `catalog_source_snapshot.md` source and label tables by exact track ID. It does not scrape pages or download audio. Intent evaluation and track-label validation are distinct parts of this project.
