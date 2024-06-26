# papis-extract

[![status-badge](https://ci.martyoeh.me/api/badges/Marty/papis-extract/status.svg)](https://ci.martyoeh.me/Marty/papis-extract)
<!-- TODO have to set up pypi badge
![PyPI](https://img.shields.io/pypi/v/papis-extract)
-->

Quickly extract annotations from your pdf files with the help of the [papis](https://github.com/papis/papis) bibliography manager.\
Easily organize all your highlights and thoughts next to your documents and references.\

## Installation

<!-- TODO set up pypi repository / explain git install path -->
You can install through pip with `pip install git+https://git.martyoeh.me/Marty/papis-extract.git`.

That's it! If you have papis and papis-extract installed in the same environment (whether virtual or global),
everything should now be set up.

I am currently working towards the first release for pypi, see the below roadmap;
when that is done you will also be able to install in the usual pypi way.

If you manage your python environments with `pipx`, you can also `pipx inject --spec 'git+git+https://git.martyoeh.me/Marty/papis-extract.git` to add it to your specific papis environment.

To check if everything is working you should now see the `extract` command listed when running `papis --help`.
You will be set up with the default options but if you want to change anything, read on in configuration below.

> **Note**
> This plugin is still in fairly early development.
> It does what I need it to do, but if you have a meticulously organized library *please* make backups before doing any operation which could affect your notes, or make use of the papis-included git options.
> Take care to read the Issues section of this README if you intend to run it over a large collection.

## Usage

`papis extract [OPTIONS] [QUERY]`

You can get additional help on the plugin command line options with the usual `papis extract --help` command.

The basic command above, `papis extract` without any options or queries will allow you to select an entry in your library from which it will extract all annotations (from all PDF files associated).

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

The above command will print out your annotations made on *all* papers by Einstein.

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
*most* or *all* of your notes, depending on how many entries in your library have pdfs with annotations attached.

While I have not done extensive optimizations the process should be relatively quick even for larger libraries:
On my current laptop, extracting ~4000 annotations from ~1000 library documents takes around 90 seconds,
though this will vary with the length and size of the PDFs you have.
For smaller workloads the process should be almost instant.

You can change the format that you want your annotations in with the `--template` option.
To output annotations in a markdown-compatible syntax (the default), do:

```bash
papis extract --template markdown
```

There are sub-variants of the formatter for atx-style headers, with `--template markdown-atx` (`# Headings`),
or setext-style with `--template markdown-setext` (the default style).

To instead see them in a csv syntax simply invoke:

```bash
papis extract --template csv
```

And if you only want to know how many annotations exist in the documents, you can invoke:

```bash
papis extract --template count
```

For now, these are the only formatters the plugin knows about.

Be aware that if you re-write to your notes using a completely different template than the original the plugin will *not* detect old annotations and drop them,
so you will be doubling up your annotations.
See the `minimum_similarity_color` configuration option for more details.

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

Extraction will *not* happen automatically when you add new annotations to an existing document,
regardless of this setting.

> **Note**
> This option does not work yet due to currently missing upstream features.

### Automatic tagging

By supplying the tags option with a valid python dictionary of the form `{"tag": "color", "tag2": "color2"}`,
you can enable automatic tagging for your annotations.

You thus ascribe specific meanings to the colors you use in highlighting.

For example, if you always highlight the most essential arguments and findings in red and always highlight things you have to follow up on in blue, you can assign the meanings 'important' and 'todo' to them respectively as follows:

```conf
[plugins.extract]
tags = {"red": "important", "blue": "toread"}
```

Currently recognized colors are: `red` `green` `blue` `yellow` `purple` `orange`.

Since these meanings are often highly dependent on personal organization and reading systems,
no defaults are set here.

### Advanced configuration

```conf
[plugins.extract]
minimum_similarity: 0.75,  # for checking against existing annotations
minimum_similarity_content: 0.9,  # for checking if highlight or note
minimum_similarity_color: 0.833,  # for matching tag to color
```

`minimum_similarity` sets the required similarity of an annotation with existing annotations in your notes to be dropped.
Annotations you have in notes might change if you for example fix small spacing mistakes or a letter/punctuation that has been falsely recognized in the PDF or change similar things.
Generally, this should be fine as it is but you should change this value if you either get new annotations dropped though they should be added (decrease the value) or annotations are added duplicating existing ones (increase the value).

---

`minimum_similarity_content` sets the required similarity of an annotation's note and in-pdf written words to be viewed as one. Any annotation that has both and is *under* the minimum similarity will be added in the following form:

```markdown
> my annotation
Note: my additional thoughts
```

That is, the extractor detects additional written words by whoever annotated and adds them to the extraction.
The option should generally not take too much tuning, but it is there if you need it.

---

`minimum_similarity_color` sets the required similarity of highlight/annotation colors to be recognized as the 'pure' versions of themselves for color mapping (see 'automatic tagging'). With a low required similarity dark green and light green, for example, will both be recognized simply as 'green' while a high similarity will not match them, instead only matching closer matches to a pure (0, 255, 0) green value.

This should generally be an alright default but is here to be changed for example if you work with a lot of different annotation colors (where dark purple and light purple may different meanings) and get false positives in automatic tag recognition, or no tags are recognized at all.

## Extractors

Currently, the program supports two annotation extractors:

A **`pdf` extractor**, which takes highlights and annotations embedded in any PDF file.
It should work with most PDF styles, as long as annotations are marked as such 
(does not work if e.g. highlights are baked onto text, or there is no text in the file).

A `pocketbook` extractor, which takes bookmarks exported from the mobile [PocketBook](https://pocketbook.ch/en-ch/app) reader applications.
You can export bookmarks by opening a book, going to the notes list and selecting `Export notes...`.
Then import the resulting `.html` file into the library using `papis add`
(or `papis addto` to add it to existing documents).
You are then ready to use extract to get those annotations from the exported list into your notes.

## TODO: Roadmap to first release

Known issues to be fixed:

- [x] if both content and text are empty, do not extract an annotation
- [x] Speed?
    - should be fine, on my machine (old i5 laptop) it takes around 90s for ~1000 documents with ~4000 annotations
- [x] ensure all cmdline options do what they should
- [x] annotations carry over color object from fitz, should just be Color object or simple tuple with rgb vals
- [x] docstrings, docstrings!
- [ ] testing testing testing!!
    - [ ] refactor into some better abstractions (e.g. Exporter Protocol -> stdout/markdown implementations; Extractor Protocol -> PDF implementation)
- [ ] dependency injection for extractor/exporter/formatter/annotation modules
    - [ ] any call to papis.config should start from init and be injected?

features to be implemented:

- [ ] CICD
    - [x] static analysis (lint, typecheck etc) on pushes
    - [x] test pipeline on master pushes
    - [ ] release pipeline to pypi on tags
- [x] add page number if available
    - exists in Annotation, just need to place in output
- [ ] show overall amount of extractions at the end
    - implemented for writing to notes (notes exporter)
    - KNOWN ISSUE: currently returns number of annotation rows (may be multiple per annot)
- [ ] custom formatting decided by user
    - in config as { "myformatter": ">{tag}\n{quote}\n{note}\n{page} etc"}
- [ ] improved default exporters
    - [x] markdown into notes
    - [ ] pretty display on stdout (rich?)
    - [x] csv/tsv to stdout
    - [ ] table fmt stdout?
- [ ] allow custom colors -> tag name settings not dependent on color name existing (e.g. {"important": (1.0,0.0,0.0)})
- [ ] `--overwrite` mode where existing annotations are not dropped but overwritten on same line of note
- [x] `--force` mode where we simply do not drop anything
- [x] `--format` option to choose from default or set up a custom formatter
    - called `--template` in current implementation
- [ ] on_add hook to extract annotations as files are added
    - needs upstream help, 'on_add' hook, and pass-through of affected documents
- [ ] target same minimum Python version as papis upstream (3.8 as of papis 0.13)

upstream changes:

- [ ] need a hook for adding a document/file
- [ ] need hooks to actually pass through information on the thing they worked on (i.e. their document)

## Issues

First, a note in general: There is the functionality to run this plugin over your whole library in a single command and also in a way that makes permanent changes to that library.
This is intended and, in my view, an important aspect of what this plugin provides and the batch functionality of cli programs in general.
However, it can also lead to frustrating clean-up time if something messes up or, in the worst case, data loss.
The extractors attempt to ascertain what files they can operate on with certain heuristics but will not be fail-safe.
Take the note at the top of this README to heart and always have backups on hand before larger operations.

A note on the extraction: Highlights in pdfs can be somewhat difficult to parse
(as are most things in them). Sometimes they contain the selected text that is written on the
page, sometimes they contain the annotators thoughts as a note, sometimes they contain nothing.
This plugin makes an effort to find the right combination and extract the written words,
as well as any additional notes made - but things *will* slip through or extract weirdly every now
and again.

Secondly, a note on the pages: I use the page number that the mupdf library gives me when it
extracts anything from the pdf file. Sometimes that number will be correct for the document,
sometimes it will however be the number of the *pdf document* internally. This can happen if
e.g. an article or a book has frontmatter without numbering scheme or with a different one.
Sometimes the correct pages will still be embedded in the pdf and everything will work,
others it won't. So always double check your page numbers!

I am not sure if there is much I can do about these issues for now.

## For developers

and for myself whenever I forget. The basic building blocks currently in here are three:

- extractors
: Extract data from a source file attached to a papis document. 
  Crawls the actual files attached to documents to put them into annotation-friendly formats.

- annotations
: The actual extracted blocks of text, containing some metadata
  info as well, such as their color, type, page.

- exporters
: Put the extracted data somewhere. For now stdout or into your notes.

- formatters
: Make sure the exporter saves the annotation data according to your preferred layout,
  such as a markdown syntax or csv-structure.

Splitting it into those building blocks makes it easier to recombine them in any way,
should someone want to save highlights as csv data in their notes,
or to include additional extractors or formatters.

To develop it together with an isolated `papis` instance you can simply inject papis into your 
development environment, e.g. invoking the poetry environment shell and then manually installing:

```bash
poetry shell
pip install papis
```

This will leave you with `papis` installed in the same virtual environment as your development.
However, what I do on my system instead to enable quick testing is inject it into a 
system-wide (but isolated with `pipx`) papis setup:

```bash
pipx install papis # create an isolated papis installation reachable form anywhere
pipx inject --editable papis . # inject this folder into the environment and keep up with any changes
```

This for me provides the ideal compromise of clean dev environment (papis is not directly part of it)
but quickly reachable installation to test my changes.

---

If you spot a bug or have an idea feel free to open an issue.\
I might be slow to respond but will consider them all!

Pull requests are warmly welcomed.\
If they are larger changes or additions let's talk about them in an issue first.

Thanks for using my software ❤️
