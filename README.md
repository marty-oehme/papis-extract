# papis-extract

![GitHub Release](https://img.shields.io/github/v/release/marty-oehme/papis-extract)
![PyPI - Version](https://img.shields.io/pypi/v/papis-extract)
![GitHub Actions Test Workflow Status](https://img.shields.io/github/actions/workflow/status/marty-oehme/papis-extract/test.yml?label=tests)
[![status-badge](https://ci.martyoeh.me/api/badges/Marty/papis-extract/status.svg)](https://ci.martyoeh.me/Marty/papis-extract)
![GitHub Actions Release Workflow Status](https://img.shields.io/github/actions/workflow/status/marty-oehme/papis-extract/release.yml?label=release)

Quickly extract annotations from your files with the help of the [papis](https://github.com/papis/papis) bibliography manager.\
Easily organize all your highlights and thoughts next to your documents and references.\
Extract from PDFs, a variety of ebook formats, or implement your own exporters for any other format.

> **Warning**
> Papis v0.15.0 has been released. This plugin now tracks that version and
> will _not_ support any older papis version going forward. For the time being
> v0.14.x may still work fine but it will receive no support.
>
> If you really want to keep using it for older papis versions, change the minimum
> dependency versioning of papis in `pyproject.toml` in the repository root.

## Installation

The plugin is available on [PyPI](https://pypi.org/project/papis-extract/). Install it with pip:

```bash
pip install papis-extract
```

If you have papis and papis-extract installed in the same environment (whether virtual or global),
everything should now be set up.

If you manage your python environments with `uv`, you can also inject it into the papis environment:

```bash
uv tool install --with papis-extract papis
```

Or if you manage your python environments with `pipx`:

```bash
pipx inject papis papis-extract
```

### Installing from source

You can also install directly from the repository to track the latest changes:

```bash
pip install git+https://git.martyoeh.me/Marty/papis-extract.git
```

Or, for `pipx` users:

```bash
pipx inject --spec 'git+https://git.martyoeh.me/Marty/papis-extract.git' papis
```

To check if everything is working you should now see the `extract` command listed when running `papis --help`.
You will be set up with the default options.
If you want to change anything, read on in configuration below.

## Usage

> **Note**
> This plugin is still in fairly early development.
> It does what I need it to do, but if you have a meticulously organized library _please_ make backups before doing any operation which could affect your notes, or make use of the papis-included git options.
> Take care to read the Issues section of this README if you intend to run it over a large collection.

`papis extract [OPTIONS] [QUERY]`

You can get additional help on the plugin command line options with the usual `papis extract --help` command.

The basic command above, `papis extract` without any options or queries,
will allow you to select an entry in your library,
go through all the files associated with this entry and extract the annotations from all files it
can parse.
A list of available extractors is provided [below](#extractors).

Add a query to limit the search, as you do with papis.

```bash
papis extract "author:Einstein"
```

This will print the extracted annotations to the commandline through stdout.

If you invoke the command with the `--write` option, it will write it into your notes instead:

```bash
papis extract --write "author:Einstein"
```

The above command will create notes for the entry you select and fill them with the annotations.
If a note already exists for any of the entries, it will instead append the annotations to the end of it,
**dropping all those that it already finds in the note**.
With this duplication detection you should be able to run extract as often as you wish without doubling up your existing annotations.

**PLEASE** Heed the note above and exercise caution with the `--write` option.
It is not intended to be destructive, but nevertheless create backups or version control your files.

If you wish to invoke the extraction process on all notes included in the query,
use `--all` as usual with papis:

```bash
papis extract --all "author:Einstein"
```

The above command will print out your annotations made on _all_ papers by Einstein.

You can invoke the command with `--manual` to instantly edit the notes in your editor:

```bash
papis extract --write --manual "author:Einstein"
```

Will create/append annotations and drop you into the selected Einstein note.
Take care that it will be fairly annoying if you use this option with hundreds
of entries being annotated as it will open one entry after another for editing.

To extract the annotations for all your existing entries in one go, you can use:

```bash
papis extract --write --all
```

However, the warning for your notes' safety goes doubly for this command since it will touch
_most_ or _all_ of your notes, depending on how many entries in your library have pdfs with annotations attached.

While I have not done extensive optimizations the process should be relatively quick even for larger libraries:
On my current laptop, extracting ~4000 annotations from ~1000 library documents takes around 90 seconds,
though this will vary with the length and size of the PDFs you have.
For smaller workloads the process should be almost instant.

You can change the format that you want your annotations in with the `--format` option.
To output annotations in a markdown-compatible syntax (the default), do:

```bash
papis extract --format markdown
```

There are sub-variants of the formatter for atx-style headers, with `--format markdown-atx` (`# Headings`),
or setext-style with `--format markdown-setext` (the default style).

To instead see them in a csv syntax simply invoke:

```bash
papis extract --format csv
```

And if you only want to know how many annotations exist in the documents, you can invoke:

```bash
papis extract --format count
```

For now, these are the only formatters the plugin knows about.

Be aware that if you re-write to your notes using a completely different output format than the original the plugin will _not_ detect old annotations and drop them,
so you will be doubling up your annotations.
See the `minimum_similarity` configuration option for more details.

## Configuration

### Basic configuration

Add `extract` plugin settings to your papis `config` file (usually `~/.config/papis/config`):
You will rarely have to set everything explained in the next few paragraphs -
in fact you can use the plugin without having to set up any of it if you are happy with the defaults.

The full default settings look as follows:

```conf
[plugins.extract]
on_import: False
tags = {"important": "red", "toread": "blue"}
minimum_similarity = 0.75         # for checking against existing annotations
minimum_similarity_content = 0.9  # for checking if highlight or note
minimum_similarity_color = 0.833  # for matching tag to color
```

### Automatic extraction

```conf
[plugins.extract]
on_import: True
```

If you set `on_import` to `True`,
extraction into notes is automatically run whenever a new document is added to the library,
if `False` extraction only happens when you explicitly invoke it.

Extraction will _not_ happen automatically when you add new annotations to an existing document,
regardless of this setting.

> **Note**
> This option does not work yet due to currently missing upstream features.

### Automatic tagging

By supplying the `tags` option with a valid Python dictionary, you can enable
automatic tagging for your annotations. The dictionary maps colors to tags:

```conf
[plugins.extract]
tags = {"red": "important", "blue": "toread"}
```

You can thus ascribe specific meanings to the colors you use in highlighting.

For example, if you always highlight the most essential arguments and findings
in red and always highlight things you have to follow up on in blue, you can
assign the meanings `"important"` and `"toread"` to them respectively.

Colors can be specified as **named colors** or as **hex values** (prefixed
with `#`):

```conf
[plugins.extract]
tags = {"red": "important", "#00ff00": "review", "#f90": "todo"}
```

Named colors currently recognized are:
`red` `green` `blue` `yellow` `purple` `orange`.

Since these meanings are often highly dependent on personal organization and
reading systems, no defaults are set here.

### Advanced configuration

```conf
[plugins.extract]
minimum_similarity: 0.75,  # for checking against existing annotations
minimum_similarity_content: 0.9,  # for checking if highlight or note
minimum_similarity_color: 0.833,  # for matching tag to color
```

`minimum_similarity` sets the required similarity of an annotation with existing annotations in your notes to be dropped.
Annotations you have in notes might change if you, for example, fix small spacing mistakes or a letter/punctuation that has been falsely recognized in the PDF or change similar things.
Generally, this should be fine as it is but you should change this value if you either get new annotations dropped though they should be added (decrease the value) or annotations are added duplicating existing ones (increase the value).

---

`minimum_similarity_content` sets the required similarity of an annotation's note and in-pdf written words to be viewed as one. Any annotation that has both and is _under_ the minimum similarity will be added in the following form:

```markdown
> my annotation
> Note: my additional thoughts
```

That is, the extractor detects additional written words by whoever annotated and adds them to the extraction.
The option should generally not take too much tuning, but it is there if you need it.

---

`minimum_similarity_color` sets the required similarity of highlight/annotation colors to be recognized as the 'pure' versions of themselves for color mapping (see 'automatic tagging'). With a low required similarity dark green and light green, for example, will both be recognized simply as 'green' while a high similarity will not match them, instead only matching closer matches to a pure (0, 255, 0) green value.

This should generally be an alright default but is here to be changed for example if you work with a lot of different annotation colors (where dark purple and light purple may different meanings) and get false positives in automatic tag recognition, or no tags are recognized at all.

## Extractors

In this early state, the plugin supports four annotation extractors
(largely due to me using the associated applications).

Over time there will be changes to the way this plugin interacts with extractors to make it more
extensible and easier to use for your own use-case.

### `pdf`

Takes highlights and annotations embedded in any PDF file.
It should work with most PDF styles, as long as annotations are marked as such
(does not work if e.g. highlights are baked onto text, or there is no text in the file).

### `readera`

Takes annotations exported from the [ReadEra](https://readera.org/) book reading app (Android, iOS).
ReadEra can export annotations as `.txt` files with a specific format: a title and author header,
`*****` separators between entries, and optional notes prefixed with `--`.
Import the exported file into your library using `papis add` (or `papis addto` to attach it to an
existing document reference) and run extract to transfer those annotations into your notes.

> **Note**
> Annotation color information is only available from the premium version of ReadEra.
> I don't have access to the premium version, so there is no color extraction implemented yet.
> If you use ReadEra and have the premium version, pull requests warmly welcomed.

### `readest`

Takes annotations exported from the [Readest](https://readest.com/) open-source book reading app
(Windows, macOS, Linux, iOS, Android).
Readest recently introduced custom formatting for their annotation exports. Ensure that you
export to `markdown`, with only the following format options enabled:

- [ ] Title
- [ ] Author
- [x] Export Date (important to allow papis-extract to detect `**Exported from Readest**` header)
- [ ] Chapter Titles
- [ ] Chapter Separator
- [x] Highlights
- [x] Notes
- [x] Page Number
- [ ] Note Date

> **Note**
> Other options can be enabled here, but they will just be seen as 'additional annotations'.
> We can extend the extractor in the future to parse more of these options,
> but with the rapid development pace of Readest I am waiting for the format to settle first.

### `pocketbook`

Takes bookmarks exported from the mobile [PocketBook](https://pocketbook.ch/en-ch/app) reader applications.
You can export bookmarks by opening a book, going to the notes list and selecting `Export notes...`.
Then import the resulting `.html` file into the library like any other document using `papis add`
(or `papis addto` to add it to existing document references).
You are then ready to use extract to get those annotations from the exported list into your notes.

This extractor requires the additional packages to function, so install the correct optional group
with `pip install 'papis-extract[pocketbook]'`.

## Issues

### Data safety

This plugin can run over your whole library in a single command and make permanent changes to it.
This is intentional - batch operations are a core feature of CLI tools after all - but it also means
things can go wrong. The extractors use heuristics to determine which files they can operate on, but
they are not fail-safe.

**Before any large operation, ensure you have backups** (or use papis' built-in git integration).
The warning at the top of this README bears repeating.

### Extraction quality

Highlights in PDFs are notoriously difficult to parse. An annotation entry content field may
contain:

- the selected text as it appears on the page,
- the annotator's own notes or thoughts,
- both, or
- nothing at all.

This plugin makes a best-effort attempt to find the right combination and extract both the
highlighted text and any associated notes - but things _will_ slip through or extract oddly
from time to time. If you encounter consistently bad extractions for a particular document,
please open an issue with the details.

### Page numbers

The plugin uses the page number reported by the mupdf library. Sometimes this matches the
printed page number on the document; other times it reports the internal PDF page number,
which can differ if the document has frontmatter (roman numerals, unnumbered sections, etc.).
Always double-check page numbers in your extracted annotations, _especially_ for books or articles
with non-standard pagination.

### Reporting problems

If you run into any of the above issues - or discover new ones - don't hesitate to open an issue.
Include the document format, the reader app used to create annotations, and (if possible)
a minimal example file. This helps a lot with debugging.

## For developers

### Architecture

The codebase is organized around four building blocks that form a pipeline:

```ascii
document file
↓
EXTRACTOR
↓
ANNOTATION objects
↓
FORMATTER
↓
EXPORTER
↓
output
```

- **`Extractor`** (`papis_extract/extractors/`): reads a source file attached to a papis document
  and returns a list of `Annotation` objects. Each extractor knows how to parse a specific file
  format (PDF, ReadEra export, Readest export, PocketBook export). No side-effects.
- **`Annotation`** (`papis_extract/annotation.py`): a data class holding the extracted text,
  note, page number, color, type, and file reference.
- **`Formatter`** (`papis_extract/formatters/`): converts annotations into a string representation
  (markdown, CSV, count-only). Formatters are classes that implement `__call__` - they
  can be pure functional classes, but some carry internal data. No side-effects.
- **`Exporter`** (`papis_extract/exporters/`): writes the formatted output somewhere (stdout
  or into papis notes). Exporters implement `run()` as an effectful operation.

Splitting the pipeline this way makes it easy to recombine pieces — for example, saving highlights
as CSV in your notes, or adding a new extractor for a different reading app without touching the
rest of the code.

New extractors and formatters register themselves in the respective `__init__.py` module
(`papis_extract/extractors/__init__.py` or `papis_extract/formatters/__init__.py`).

### Development setup

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
# Clone the repository
git clone <repo-url>
cd papis-extract

# Create a virtual environment and install dependencies
uv sync

# Run the test suite
uv run pytest -v

# Run the linter
uv run ruff check .
```

To test the plugin with an actual papis instance, you have two options:

1. **Inject papis into your dev venv** — simple, keeps everything in one place:

   ```bash
   uv run pip install papis
   uv run papis extract --help
   ```

2. **Inject the plugin into a pipx-managed papis** — keeps your dev environment clean
   and lets you test changes immediately (my preferred approach):

   ```bash
   uv tool install --with-editable /path/to/your/repo/of/papis-extract papis
   ```

### Contributing

Bug reports and feature ideas are welcome — please open an issue.
I may be slow to respond but will consider them all.

Pull requests are warmly welcomed. For larger changes or additions,
please open an issue first so we can discuss the direction.

Thanks for using this software ❤️
