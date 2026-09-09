# Media Organizer Plugin Workflow (`plugins/media_organizer`)

## 📋 Overview
This document describes the media scanning, metadata classification, and database storage workflows utilized by the `plugins/media_organizer` plugin in AI Breadboard.

---

## 🔄 Main Scanning & Organization Pipeline

```
1. Initiate Scan (/api/media/scan or CLI)
   ↓
2. Initialize Subsystems (TMDBClient, MediaDatabase, MediaScanner)
   ↓
3. Base Directory Traversal (movies and TV series root directories)
   ↓
4. Metadata Classification via TMDB + Gemini (PersistentGenreClassifier)
   ↓
5. Cross-Disk Duplicate Detection (db.update_duplicates)
   ↓
6. Sequential Media Indexing (db.assign_numbers)
   ↓
7. TV Series Deep Inspection (seasons & episodes parsing)
   ↓
8. Torrent Matching and Path Reconciliation
   ↓
9. Report Generation (JSON and Markdown summaries)
   ↓
10. Storage Audit (physical disk reconciliation)
   ↓
11. Category & Label Assignment
   ↓
12. Duplicate Analysis & Reporting
```

---

## 📦 Core Plugin Modules

| Module | Location | Purpose |
| :--- | :--- | :--- |
| `media_scanner.py` | `plugins/media_organizer/` | Filesystem traversal and TMDB API metadata extraction |
| `media_auditor.py` | `plugins/media_organizer/` | Database vs. physical disk consistency verification |
| `genre_classifier.py` | `plugins/media_organizer/` | Genre classification and enrichment via TMDB & Gemini |
| `report_generator.py` | `plugins/media_organizer/` | Markdown and JSON catalog export utilities |
| `media_rebuild.py` | `plugins/media_organizer/` | Database and RAG index reconstruction and deduplication |
| `media_tracker.py` | `plugins/media_organizer/` | Path sanitization, torrent matching, and categorization |

---

## 🗄️ Database Schema & Data Model

**Primary Rule:** Record structure is governed by `type` — `[movie, series, season, episode]`.

**Logical Hierarchy:** `episode → season → series` (an episode belongs to a season, a season belongs to a series).

**Relationships:**
- For `season`: `parent_id` points to the `id` of the parent `series`.
- For `episode`: `parent_id` points to the `id` of the parent `season`.
- For `movie` and `series`: `parent_id` is `0` or `NULL`.

### `media` Table Structure:

| Field | Type | Description |
| :--- | :--- | :--- |
| `disk_name` | TEXT | Storage disk identifier / label |
| `path` | TEXT | Absolute file or directory path |
| `number` | INTEGER | Sequential library identifier |
| `title` | TEXT | Primary title |
| `title_orig` | TEXT | Original international title |
| `title_ru` | TEXT | Localized title |
| `type` | TEXT | Entity type: `movie`, `series`, `season`, `episode` |
| `year` | INTEGER | Release year |
| `main_category` | TEXT | Primary categorization tag |
| `country` | TEXT | Country of origin |
| `genres` | TEXT | JSON array of genre strings |
| `directors` | TEXT | JSON array of director names |
| `cast` | TEXT | JSON array of primary cast members |
| `num_of_seasons` | INTEGER | Total season count (series only) |
| `num_episodes_per_season` | TEXT | JSON array of episode counts per season |
| `status` | TEXT | Production status (e.g. `Returning Series`, `Ended`) |
| `rating` | TEXT | JSON object with IMDb / TMDB score metrics |
| `awards` | TEXT | JSON array of accolades and awards |
| `plot` | TEXT | Comprehensive plot summary (100–150 words) |
| `atmosphere` | TEXT | Atmospheric / tonal keywords (~15 words) |
| `why_watch` | TEXT | Curated recommendation rationale |
| `mood` | TEXT | Mood descriptor tags |
| `final_verdict` | TEXT | Concluding editorial summary |
| `can_stop_at` | TEXT | Natural stopping point recommendation |
| `quote` | TEXT | Key memorable quote |
| `facts` | TEXT | JSON array of trivia facts |
| `similar` | TEXT | JSON array of related titles |
| `parent_id` | INTEGER | Foreign key ID to parent entity |
| `episode_scan_skipped` | INTEGER | `1` if episode drill-down was skipped for large series, `0` otherwise |

---

## 🤖 Gemini AI Enrichment Protocol

### 1. Movie Request (`movie`)
- Prompt: `"Write a detailed media card for the movie [title]"`
- Output Schema: JSON formatted according to media card template.

### 2. Series Request (`series`)
- Prompt: `"Write a detailed media card for the TV series [title] (all seasons)"`
- Output Schema: JSON with embedded `seasons` and episode overview metadata.

### 3. Adaptive Scanning for Long Shows
- TMDB season and episode counts are checked prior to requesting full episode cards.
- If seasons count > 15 OR total episode count > 100 (e.g., daily soaps or long-running animation):
  - Deep per-episode LLM generation is skipped to preserve tokens and execution time.
  - Record flagged with `episode_scan_skipped = 1`.

