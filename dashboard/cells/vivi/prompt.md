# Vivi Andersson cell — maintenance note

This cell is implemented and hand-tuned. **Do not regenerate, redesign, or
replace `index.html` from this file.** When Vivi requests a change, edit the
existing implementation minimally and preserve all unrelated details.

The current behavior is intentional:

- even Stockholm-time minutes show the self-reseeding Conway automaton;
- odd minutes show a rotating embedded Tilde illustration;
- Tilde levitates gently and her dialogue panel links to and says `vivi365.github.io`;
- the layout adapts from a small dashboard tile to a fullscreen monitor;
- all CSS, JavaScript, and images remain inside the single HTML file;
- no external libraries, imports, `fetch()`, or `localStorage` are used.

Before accepting a maintenance change, verify both timed scenes, small and
fullscreen layouts, JavaScript syntax, and the sandboxed dashboard preview.
