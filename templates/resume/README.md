# Resume layouts

Your resume is a LaTeX file built into a PDF. You can use one of the two layouts below, or keep the layout of the resume you have now if it passes the checks in the next section. Setup asks which one you want; `/job-hunt-studio:tailor-resume base` then fills it with facts from your Ledger.

| Layout | Look | Based on | License |
|---|---|---|---|
| `classic` | Charter 10 pt, dark blue name and headings, one line per job with the dates at the right margin | the "engineeringresumes" theme of [RenderCV](https://github.com/rendercv/rendercv) v1.18 | MIT, notice in [`classic/LICENSE`](classic/LICENSE) |
| `jakes` | Computer Modern 11 pt, small-caps headings, two lines per job (title and dates, then employer and place) | [Jake's Resume](https://github.com/jakegut/resume) | MIT, notice in [`jakes/LICENSE`](jakes/LICENSE) |

Both are one column, one page, and pass the ATS check with both text engines. Both are filled with the fictional example candidate, so you can see them before choosing: [classic](classic/preview.png), [jakes](jakes/preview.png).

## Keeping your own layout

If your current resume already looks good and meets these criteria, keep it. `/job-hunt-studio:tailor-resume base` checks it when it builds your base resume and shows the result:

1. **Text, not an image.** A PDF made from a word processor or LaTeX, not a scan. Every character comes out of the PDF as text.
2. **One column** for the main content: no side columns, text boxes or tables used for layout.
3. **Standard headings**: Experience, Education and Skills, plus Summary, Projects or Publications if you use them.
4. **Dates next to each job**, on the job's line or the line after it.
5. **Contact details in the page itself**, not in a header or footer area.
6. **Length** that fits `resume.pages` in `jhs.yaml` (one page by default).
7. **Readable**: a body font of 10 to 11 pt, visible space between entries, at most one accent colour.

What happens next depends on the file you have:
- **A LaTeX resume:** it is used as it is. Claude adds one comment line naming the command your file uses for each job (see below), so the checks can compare titles and dates with your Ledger.
- **A Word, Google Docs or PDF resume:** the tools build resumes from LaTeX, so Claude recreates your layout in LaTeX (fonts, spacing, headings, order), builds it, and shows you the two side by side. You confirm it looks right before anything else uses it.

If your resume misses a criterion, you see which one and why it matters, and you choose: fix it in the LaTeX copy, or switch to `classic` or `jakes`.

## Markers in a template (for template authors)

- `% JHS-EXAMPLE-CONTENT: ...` on the first line means the file still holds example content. The checks report it and approval is refused until it is removed.
- `% jhs-entry: \jobline{title}{organization}{dates}` names the command that prints a job or degree and what each argument holds (`title`, `organization`, `dates`, `location`, or `ignore`). The fact check compares each entry with Ledger `[roles]`. If one command means different things in different sections, add the section name: `% jhs-entry[Education]: \resumeSubheading{organization}{location}{title}{dates}`.
- Right-aligned dates use `\datefill`, which keeps the date in reading order for pdfTeX text extraction.
