# .ocr-standards/ — CI self-test fixture marker

A non-empty `.ocr-standards/` directory so `universal-checks` (U-5) sees
that standards have been propagated into this fixture spoke.

In a real spoke this directory is populated by the OCR-docs
propagate-standards workflow. Here a single marker file is enough for the
self-test — U-5 reports the directory present and warns that VISION.md is
absent, which does not fail the check.
