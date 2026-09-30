# Manuscript build and inspection

The authoritative source is source/manuscript.md and source/supplement.md, including the explicitly named auxiliary and joint sections. Tables, references and figure files are expanded by prepare_document.py. Root Markdown, DOCX and PDF files are derived and must not be edited independently.

The pipeline reuses the working Windows build: project Python for saved-record figures and Markdown preparation; bundled Python for python-docx; Microsoft Word COM for PDF export; bundled Poppler for page images. LibreOffice was unavailable in the established environment. The equivalent Word-to-Poppler render is retained rather than installing a new global renderer. Skill render-and-inspect requirements apply to every final page.

Commands run from the repository root:

```powershell
.\.venv\Scripts\python.exe paper/paper_revision_20260929_final/prepare_document.py
& 'C:\Users\CJ\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' paper/paper_revision_20260929_final/build_docx.py
& paper/paper_revision_20260929_final/render_documents.ps1
```

The final build/dependencies.json records actual runtime versions, source identities and output counts. build/visual-review.json records only inspections actually completed. Source and numeric consistency checks precede the formal five-question decision and first export. Late data-availability changes are restricted to the relevant paragraphs and receive a targeted rebuild/review.

The immutable historical figures and formula rasters remain valid scientific inputs. Existing equation images may be reused by exact formula content; links are not independent backups and must not be overwritten. Final figures, formula inputs, sources, DOCX/PDF, verification records and reproducibility inputs are retained. Only this task's checked temporary page images may be cleaned after review. Frozen historical outputs and unrelated workspace files are outside cleanup scope.

This build does not run training, checkpoint inference, a physical solver, reference generation or a GPU task. New delivery files are local and await a later authorized remote synchronization opportunity; no instance is started for these artifacts.
