# WAVsToALE v1.0.1 — 2025-12-02

This release clarifies the GUI wording for UCS inference and adds CLI aliases for consistency.

## Changes
- GUI: Checkbox label now reads: "Infer UCS category/subcategory if filename lacks a UCS ID".
- CLI: Added aliases `--ucs-inference` and `--no-ucs-inference` alongside legacy flags (`--allow-ucs-guess` / `--no-ucs-guess`).
- Version: Bumped to `1.0.1` in code and `docs/version_info.txt`.

## Usage
- GUI: Launch and toggle the UCS inference checkbox as needed.
- CLI examples:
  - Enable inference:
    ```zsh
    ./dist/WAVsToALE/WAVsToALE --ucs-inference /path/to/file.wav /path/to/output
    ```
  - Disable inference:
    ```zsh
    ./dist/WAVsToALE/WAVsToALE --no-ucs-inference /path/to/folder /path/to/output
    ```

## Build & Bundle
- macOS app bundle is produced via `./build.sh`.
- UCS CSV is bundled under `dist/WAVsToALE/_internal/data/UCS_v8.2.1_Full_List.csv`.

## Notes
- Backward compatibility maintained for previous CLI flags.
- No change to ALE output format; only matching behavior and labeling improved.

