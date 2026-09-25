# Build and reproduction

The authoritative body text is source/manuscript.md and source/supplement.md. Tables, references and saved figures are includes. The top-level Markdown, DOCX and PDF are derived deliverables, not separately maintained bodies.

Run prepare_document.py with the project Python to expand includes and render equations, then build_docx.py with the bundled documents-runtime Python. Export each resulting DOCX through the existing ../advisor_review_20260924/render_with_word.ps1. Copy its checked PDF to the delivery root. Full page images and render logs are retained under build/. The exact consumed inputs, identities, runtime dependencies and output checksums are in build-dependencies.json.

The bundled LibreOffice renderer was attempted once; Windows has no installed LibreOffice. The existing Microsoft Word renderer produced the actual PDF, so DOCX and PDF share typography and pagination. No dependency was installed globally.

Historical figure PNGs are unchanged inputs. Regenerating those figures from raw fields is a separate operation requiring the historical local arrays and original scripts named in build-dependencies.json. Full-array external access is still open. Current conditional figures and the report use the recovered numeric cache; the saved-array verification reproduces all accepted defects and comparison measures without model queries, propagation or training.

The initial preparation and editorial scripts document this revision. Once prepared, edit only the source/ Markdown and referenced tables; do not rerun preparation to overwrite the authoritative prose. Scientific execution is closed and is not part of the document build.

## Repository publication scope

The published build/ records retain visual QA, final render checks, build summary and renderer logs. Regenerable equation/page images and full render manifests remain local. Published PDF/DOCX and authoritative body sources are unchanged from the checked delivery; publication navigation links are maintained separately. Compact execution evidence is under [evidence/conditional-phase](evidence/conditional-phase/README.md); original manifests intentionally retain local execution paths. Full-array regeneration still requires the explicitly listed local inputs. Historical preparation/status scripts record the closed execution and must not be rerun to overwrite current publication state.
