# Local publication package

Prepared for **Krzysztof Jakóbczyk**, with no inferred affiliation, email, or ORCID. This is a research preprint draft and local repository tree. The GitHub repository has been created at https://github.com/kjakobczyk/venue5055-battery-research. The paper has not been submitted to arXiv.

## Included deliverables

- `paper/main.pdf`: compiled review copy.
- `paper/main.tex`, `references.bib`, and `main.bbl`: conventional LaTeX/BibTeX sources.
- Three original figures, each in PDF/SVG/PNG.
- A detailed English root README, protocol description, evidence map, and limitations.
- 63 exported source artifacts, including the 25 acquired gauge-state blocks and intervention before/after data.
- Offline verification, extraction, rendering, and source-packaging tools.
- Historical device-facing instruments, separated from all default build targets.
- Author-selected MIT code and CC BY 4.0 manuscript/data licenses, attribution notices, and `CITATION.cff`.

`dist/venue5055-arxiv-source.tar.gz` contains only the TeX source, bibliography/BBL, and figure PDFs. `dist/venue5055-github-review.zip` contains the review repository, compiled paper, and evidence. `work/`, virtual environments, and vendor inputs are excluded.

## arXiv preparation

The source package follows the ordinary [arXiv TeX guidance](https://info.arxiv.org/help/submit_tex.html): source plus local figure inputs and bibliography output, without dependence on a proprietary class or external build service. Local compilation is checked; acceptance, endorsement, category suitability, and server-side compilation are not claimed.

Suggested subject area to consider during author review: Computer Science / Hardware Architecture (`cs.AR`), given the platform/EC reverse engineering focus. This is a suggestion, not a confirmed classification or endorsement. The paper explicitly does not claim a security vulnerability.

The metadata file `paper/arxiv-metadata.txt` supplies the title, author, abstract, and selected manuscript license. It includes the actual GitHub URL and has no invented publication identifier, DOI, affiliation, or ORCID. An author should review the AI-assistance statement and scientific limitations before submission.

## GitHub preparation

The local Git repository uses branch `main` and targets the owner-provided remote `https://github.com/kjakobczyk/venue5055-battery-research.git`. The actual URL is included in the paper, README, and citation metadata. No arXiv submission is performed by a Git push.

Vendor executables, complete EC/BIOS images, embedded update scripts, and boardview originals remain outside the release. The download/extraction instructions and pinned hashes let a reader obtain those inputs separately where available.

## What the completed experiment changed

The final device state in the recorded experiment has Qmax0=8794 mAh. There is no claim that documentation creation changed the device or repeated the experiment. The manuscript does not claim that a cycle reset, resistance reset, learning cycle, runtime-capacity test, or rollback was performed.
