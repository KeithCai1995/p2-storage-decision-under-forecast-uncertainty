# Presentation-only follow-up - 21 October 2026

Fifteen published text records contained machine-specific absolute workspace paths.
The original workspace prefix is now displayed as the explicit `<WORKSPACE>`
placeholder. The remaining relative suffix and slash style are retained. This is
not a real filesystem location and is not a claim that execution took place in a
different environment.

The affected records are twelve `run_manifest.json` files (eleven corrected runs
and the baseline `outputs/` mirror), two environment logs and the retained initial
temporary-failure log. Original dates, software versions, source/data hashes,
numerical results and the original execution scope are not changed. Unredacted
originals are backed up outside the Git repository and are not included in this
public update. New runs may record their actual local paths again.

These displayed implementation paths are not executable inputs. The release
checker and study cache checks still use the unchanged data hash, input contract,
configuration and method/version fields. The mirrored baseline manifests remain
byte-identical to each other after the same path-prefix redaction.

The README also replaces the obsolete description of the 21 October quality
update as uncommitted work with links to merged PR #4 and its successful six-job
post-merge workflow. Those CI results belong only to the cited merge commit;
they are not evidence that this later presentation follow-up has run remotely.

No scheduling code, risk parameters, saved CSVs, figures or PDFs are changed.
