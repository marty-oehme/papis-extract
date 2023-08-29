# papis-extract

[![status-badge](https://ci.martyoeh.me/api/badges/Marty/papis-extract/status.svg)](https://ci.martyoeh.me/Marty/papis-extract)
<!-- TODO have to set up pypi badge
![PyPI](https://img.shields.io/pypi/v/papis-extract)
-->

Quickly extract annotations from your pdf files with the help of the [papis](https://github.com/papis/papis) bibliography manager.\
Easily organize all your highlights and thoughts next to your documents and references.\

## Installation:

<!-- TODO set up pypi repository / explain git install path -->
You can install from pypi with `pip install git+https://git.martyoeh.me/Marty/papis-extract.git`.

That's it! If you have papis and papis-extract installed in the same environment (whether virtual or global),
everything should now be set up.

I am currently working towards the first release for pypi, see the below roadmap;
when that is done you will also be able to install in the usual pypi way.

To check if everything is working you should now see the `extract` command listed when running `papis --help`.
You will be set up with the default options but if you want to change anything, read on in configuration below.

> **Note**
> This plugin is still in fairly early development. It does what I need it to do, but if you have a meticulously organized library *please* make backups before doing any operation which could affect your notes, or make use of the papis-included git options.
## Usage:

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

## Configuration

### Basic configuration
Add `extract` plugin settings to your papis `config` file (usually `~/.config/papis/config`):
You will rarely have to set everything explained in the next few paragraphs -
in fact you can use the plugin without having to set up any of it if you are happy with the defaults.

The full default settings look as follows:

```yaml
[plugins.extract]
on_import: False
tags = {"important": "red", "toread": "blue"}
minimum_similarity = 0.75         # for checking against existing annotations
minimum_similarity_content = 0.9  # for checking if highlight or note
minimum_similarity_color = 0.833  # for matching tag to color
```

### Automatic extraction

```yaml
[plugins.extract]
on_import: True
```

If you set `on_import` to `True`,
extraction into notes is automatically run whenever a new document is added to the library,
if `False` extraction only happens when you explicitly invoke it.

Extraction will *not* happen automatically when you add new annotations to an existing document,
regardless of this setting.

#### Automatic tagging

By supplying the tags option with a valid python dictionary of the form `{"tag": "color", "tag2": "color2"}`, 
you can enable automatic tagging for your annotations.

You thus ascribe specific meanings to the colors you use in highlighting. 

For example, if you always highlight the most essential arguments and findings in red and always highlight things you have to follow up on in blue, you can assign the meanings 'important' and 'todo' to them respectively as follows:

```yaml
[plugins.extract]
tags = {"red": "important", "blue": "toread"}
```

Currently recognized colors are: `red` `green` `blue` `yellow` `purple` `orange`.

Since these meanings are often highly dependent on personal organization and reading systems,
no defaults are set here.

### Advanced configuration

```yaml
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

## Roadmap to first release

Known issues to be fixed:

- [x] if both content and text are empty, do not extract an annotation
- [x] Speed?
    - should be fine, on my machine (old i5 laptop) it takes around 90s for ~1000 documents with ~4000 annotations
- [x] ensure all cmdline options do what they should
- [ ] annotations carry over color object from fitz, should just be Color object or simple tuple with rgb vals
- [ ] docstrings, docstrings!
- [ ] testing testing testing!!
    - [ ] refactor into some better abstractions (e.g. Exporter Protocol -> stdout/markdown implementations; Extractor Protocol -> PDF implementation)

features to be implemented:

- [ ] CICD
    - [x] static analysis (lint, typecheck etc) on pushes
    - [x] test pipeline on master pushes
    - [ ] release pipeline to pypi on tags
- [ ] add page number if available
    - exists in Annotation, just need to place in output
- [ ] show overall amount of extractions at the end
- [ ] custom formatting decided by user
    - in config as { "myformatter": ">{tag}\n{quote}\n{note}\n{page} etc"}
- [ ] improved default exporters
    - markdown into notes
    - pretty display on stdout (rich?)
    - csv/tsv to stdout
    - table fmt stdout?
- [ ] allow custom colors -> tag name settings not dependent on color name existing (e.g. {"important": (1.0,0.0,0.0)})
- [ ] `--overwrite` mode where existing annotations are not dropped but overwritten on same line of note
- [ ] `--force` mode where we simply do not drop anything
- [ ] `--format` option to choose from default or set up a custom formatter
- [ ] on_add hook to extract annotations as files are added
    - needs upstream help, 'on_add' hook, and pass-through of affected documents

upstream changes:

- [ ] need a hook for adding a document/file
- [ ] need hooks to actually pass through information on the thing they worked on (i.e. their document)

## Issues

A note on the extraction: Highlights in pdfs can be somewhat difficult to parse
(as are most things in them). Sometimes they contain the selected text that is written on the
page, sometimes they contain the annotators thoughts as a note, sometimes they contain nothing.
This plugin makes an effort to find the right combination and extract the written words,
as well as any additional notes made - but things *will* slip through or extract weirdly every now
and again.

The easiest extraction is provided if your program writes the selection itself into the highlight
content, because then we can just use that. It is harder to parse if it does not and will sometimes
get additional words in front or behind (especially if the highlight ends in the middle of a line)
or even cut a few off.

I am not sure if there is much I can do about this.

---

If you spot a bug or have an idea feel free to open an issue.\
I might be slow to respond but will consider them all!

Pull requests are warmly welcomed.\
If they are larger changes or additions let's talk about them in an issue first.

Thanks for using my software ❤️
