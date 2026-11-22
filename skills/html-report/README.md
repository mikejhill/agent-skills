# html-report

Builds one self-contained, interactive HTML file (linked d3 charts, what-if sliders, live demos, 3D scenes) that explains a plan, design, decision, incident, or status faster than prose. The file works offline and can be shared by email, chat, or disk.

## Use

Loads automatically for requests such as:

- "Make a report on the options for the database migration."
- "Show me how the ingestion pipeline works."

## Requirements

- Python 3.9+ to build and lint the report (stdlib only). d3, three.js, and lil-gui are bundled in `assets/vendor/`.
- Optional: a headless browser, for the agent to check layout and console errors.

## Results

`report.html` (built, about 330 KB to 1.1 MB) and `report.src.html` (editable source) where you choose. Reports include a Light / Auto / Dark theme switch, and estimates are labelled as such.
