# Skill: `file-saver`

## Purpose
Provides safe, atomic file writing and path verification on the host filesystem.

---

## Operating Principles
1. Accepts destination file path and payload content.
2. Validates directory existence and write permissions.
3. Performs atomic file write with encoding safety checks.
