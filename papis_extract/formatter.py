from collections.abc import Callable

from papis_extract.annotation import AnnotatedDocument

Formatter = Callable[[list[AnnotatedDocument]], str]


def format_markdown(docs: list[AnnotatedDocument] = []) -> str:
    template = (
        "{{#tag}}#{{tag}}\n{{/tag}}"
        "{{#quote}}> {{quote}}{{/quote}} {{#page}}[p. {{page}}]{{/page}}"
        "\n{{#note}}  NOTE: {{note}}{{/note}}"
    )
    output = ""
    for entry in docs:
        if not entry.annotations:
            continue

        title_decoration = (
            f"{'=' * len(entry.document.get('title', ''))}   "
            f"{'-' * len(entry.document.get('author', ''))}"
        )
        output += (
            f"{title_decoration}\n"
            f"{entry.document['title']} - {entry.document['author']}\n"
            f"{title_decoration}\n\n"
        )
        for a in entry.annotations:
            output += a.format(template)
            output += "\n"

        output += "\n\n\n"

    return output


def format_count(docs: list[AnnotatedDocument] = []) -> str:
    output = ""
    for entry in docs:
        if not entry.annotations:
            continue

        count = 0
        for _ in entry.annotations:
            count += 1

        d = entry.document
        output += (
            f"{d['author'] if 'author' in d else ''}"
            f"{' - ' if 'author' in d else ''}"  # only put separator if author
            f"{entry.document['title'] if 'title' in d else ''}: "
            f"{count}\n"
        )

    return output


def format_csv(docs: list[AnnotatedDocument] = []) -> str:
    header: str = "type,tag,page,quote,note,author,title,ref,file"
    template: str = (
        '{{type}},{{tag}},{{page}},"{{quote}}","{{note}}",'
        '"{{doc.author}}","{{doc.title}}","{{doc.ref}}","{{file}}"'
    )
    output = f"{header}\n"
    for entry in docs:
        if not entry.annotations:
            continue

        d = entry.document
        for a in entry.annotations:
            output += a.format(template, doc=d)
            output += "\n"

    return output
