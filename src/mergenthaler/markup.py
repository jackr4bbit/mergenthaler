from typing import Self, cast
import re
from pathlib import Path
from packaging.version import Version
import html

from .utils import validUrl, removeScheme
from . import files as parseModule
from .site import Site

class Markup:
    def __init__(self, elements: Element | list[Element]):
        if isinstance(elements, list):
            self.elements: list[Element] = elements
        else:
            self.elements: list[Element] = [elements]

    def __add__(self, other: Self) -> Self:
        if not isinstance(other, Markup):
            return NotImplemented # type: ignore

        return cast(Self, type(self)(self.elements + other.elements))

    def __radd__(self, other: Self) -> Self:
        if not isinstance(other, Markup):
            return NotImplemented # type: ignore

        return cast(Self, type(self)(other.elements + self.elements))

    def html(self, site: Site) -> str:
        return "".join(f"<p>{element.html(site)}</p>" if isinstance(element, Text) else element.html(site) for element in self.elements)

    @classmethod
    def parse(cls, text: str, path: Path, feed: parseModule.Feed, plugins: set[Plugin]) -> Markup:
        def parseParts(remaining: str) -> list[Element]: # type: ignore
            if not remaining:
                return []

            for elementType in [elementType for plugin in plugins for elementType in plugin.elements] + defaultElements:
                match = re.search(elementType.match, remaining, flags=re.DOTALL | re.MULTILINE)
                if match:
                    element = elementType.parse(remaining[match.start():match.end()], path, feed, {format for plugin in plugins for format in plugin.formats})
                    if element:
                        parts = []
                        parts += parseParts(remaining[:match.start()])
                        parts.append(element)
                        parts += parseParts(remaining[match.end():])
                        return parts

        return cls(parseParts(text))



class Element:
    match: str

    def __str__(self) -> str: ...

    @classmethod
    def parse(cls, text: str, path: Path, feed: parseModule.Feed, formats: set[type[Format]] | None = None) -> Self | None: ...

    def html(self, site: Site) -> str: ...

class Format:
    name: str
    start: str
    end: str

    def __init__(self, groups: dict[str | int, str]):
        self.groups = groups

    def html(self, text: Text, site: Site) -> str: ...

class Plugin:
    name: str
    version: Version
    formats: set[type[Format]] = set()
    elements: list[type[Element]] = []

class SimpleFormat(Format):
    name: str
    start: str
    end: str
    htmlStart: str
    htmlEnd: str | None = None

    def html(self, text: Text, site: Site) -> str:
        return type(self).htmlStart + text.html(site, noFormat=True) + (type(self).htmlEnd or type(self).htmlStart[:1] + "/" + type(self).htmlStart[1:])

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        for key, value in list(cls.__dict__.items()):
            match key:
                case "name":
                    setattr(cls, key, value.lower())
                case "start" | "end":
                    setattr(cls, key, re.escape(value))

class Header(SimpleFormat):
    name = "header"
    start = "[*"
    end = "*]"
    htmlStart = "<h2>"

class Italic(SimpleFormat):
    name = "italic"
    start = "/*"
    end = "*/"
    htmlStart = "<em>"

class Underline(SimpleFormat):
    name = "underline"
    start = "__"
    end = "__"
    htmlStart = "<span style=\"text-decoration: underline;\">"
    htmlEnd = "</span>"

class Bold(SimpleFormat):
    name = "bold"
    start = "<*"
    end = "*>"
    htmlStart = "<strong>"

class Strikethrough(SimpleFormat):
    name = "strikethrough"
    start = "--"
    end = "--"
    htmlStart = "<s>"

defaultFormats = {Header, Italic, Underline, Bold, Strikethrough}

class Text(Element):
    match = r".*"

    def __init__(self, text: str | Text, format: type[Format] | None = None, groups: dict[str | int, str] | None = None):
        self.__data: list[str | Text] = []

        if isinstance(text, str):
            self.__data = [text]
        elif isinstance(text, Text):
            self.__data = text.__data
        else:
            raise TypeError("You must pass a string or a Markup object")

        self.format = None if format is None else format(groups or {})

    def __add__(self, other: str | Self) -> Self:
        if isinstance(other, str):
            other = cast(Self, type(self)(other))
        elif not isinstance(other, Text):
            return NotImplemented # type: ignore

        output = type(self)(self)
        output.__data.append(other)
        return cast(Self, output)

    def __radd__(self, other: str | Self) -> Self:
        if isinstance(other, str):
            other = cast(Self, type(self)(other))
        elif not isinstance(other, Text):
            return NotImplemented # type: ignore

        output = type(self)(other)
        output.__data.append(self)
        return cast(Self, output)

    def __str__(self) -> str:
        return "".join(str(text) if isinstance(text, Text) else text for text in self.__data)

    def empty(self) -> bool:
        return len(self.__data) == 0

    @classmethod
    def parse(cls, text: str, path: Path, feed: parseModule.Feed, formats: set[type[Format]] | None = None) -> Self:
        if formats is None:
            formats = set()

        matches = []

        for format in defaultFormats | formats:
            for match in re.finditer(r"(.*?)" + format.start + r"(?P<content>.+)" + format.end + r"(.*)", text, flags=re.DOTALL):
                matches.append((format, match))

        if matches:
            format, match = max(matches, key=lambda x: x[1].start())

            return (
                cls.parse(match.group(1), path, feed, formats) +
                cls(
                    text = cls.parse(match.group("content"), path, feed, formats),
                    format = format,
                    groups = {
                        (key - 1 if isinstance(key, int) else key): match.group(key)
                        for key in range(1, len(match.groups()) + 1)
                        if key not in [1, 2, "content"]
                    }
                ) +
                cls.parse(match.groups()[-1], path, feed, formats)
            )

        return cls(text)

    def html(self, site: Site, noFormat=False) -> str:
        if self.format is None or noFormat:
            return "".join(text.html(site) if isinstance(text, Text) else html.escape(text).replace("\n", "<br>") for text in self.__data)
        else:
            return self.format.html(self, site)

class Image(Element):
    match = r"\[#(.*?)#]\[(.*?)]"

    def __init__(self, name: str, path: Path, description: str = ""):
        self.name = name
        self.path = path
        self.description = description

    def __str__(self) -> str:
        return ""

    @classmethod
    def parse(cls, text: str, path: Path, feed: parseModule.Feed, formats: set[type[Format]] | None = None) -> Self | None:
        match = re.match(cls.match, text, flags=re.DOTALL)
        if match is None:
            raise SyntaxError(f"Unknown image syntax: {text}.")
        else:
            name = match.group(2)
            if name.startswith("/"):
                name = name[1:]
                image = feed.root / name
            else:
                image = path.parent / name
                name = str(image.relative_to(feed.root))

            if not image.is_file():
                raise ValueError(f"\"{image}\" doesn't exist.")

            return cls(name, image, match.group(1))

    def html(self, site: Site) -> str:
        return f"<img src=\"/{site.__class__.assetPath}/{self.name}\" alt=\"{self.description}\" title=\"{self.description}\">"

class WebImage(Image):
    def __init__(self, name: str, url: str, description: str = ""):
        self.name = name
        if not validUrl(url):
            raise ValueError(f"\"{url}\" is not a valid URL.")
        self.url = url
        self.description = description

    @classmethod
    def parse(cls, text: str, path: Path, feed: parseModule.Feed, formats: set[type[Format]] | None = None) -> Self | None:
        match = re.match(cls.match, text, flags=re.DOTALL)
        if match is None:
            raise SyntaxError(f"Unknown image syntax: {text}.")
        elif validUrl(match.group(2)):
            return cls(removeScheme(match.group(2)), match.group(2), match.group(1))

        return None


class Link(Element):
    match = r"\[(.*?)]\[(.*?)]"

    def __init__(self, text: str, url: str):
        self.text = text
        self.url = url

    def __str__(self) -> str:
        return self.text

    @classmethod
    def parse(cls, text: str, path: Path, feed: parseModule.Feed, formats: set[type[Format]] | None = None) -> Self:
        match = re.match(cls.match, text, flags=re.DOTALL)
        if match is None:
            raise SyntaxError(f"Unknown link syntax: {text}.")
        else:
            return cls(match.group(1), match.group(2))

    def html(self, site: Site) -> str:
        return f"<a href=\"{self.url}\">{self.text}</a>"

class Code(Element):
    match = r":::(.*?):::"

    def __init__(self, code: str):
        self.code = code

    def __str__(self) -> str:
        return self.code

    @classmethod
    def parse(cls, text: str, path: Path, feed: parseModule.Feed, formats: set[type[Format]] | None = None) -> Self:
        match = re.match(cls.match, text, flags=re.DOTALL)
        if match is None:
            raise SyntaxError(f"Unknown code block syntax: {text}.")
        else:
            return cls(match.group(1).strip("\n"))

    def html(self, site: Site) -> str:
        return f"<pre><code>{self.code}</code></pre>"

class Quote(Element):
    match = r"^(?:> [^\n]*(?:\n|$))+"

    def __init__(self, contents: str):
        self.contents = contents

    def __str__(self):
        return self.contents

    @classmethod
    def parse(cls, text: str, path: Path, feed: parseModule.Feed, formats: set[type[Format]] | None = None) -> Self:
        match = re.match(cls.match, text, flags=re.DOTALL)
        if match is None:
            raise SyntaxError(f"Unknown code block syntax: {text}.")
        else:
            return cls(match.group(0).strip().replace("> ", ""))

    def html(self, site: Site) -> str:
        return f"<blockquote>{self.contents.replace("\n", "<br>")}</blockquote>"

class List(Element):
    match = r"^(?:- [^\n]*(?:\n|$))+"

    def __init__(self, items: list[Text]):
        self.items = items

    def __str__(self) -> str:
        return "\n".join(f"- {item}" for item in self.items)

    @classmethod
    def parse(cls, text: str, path: Path, feed: parseModule.Feed, formats: set[type[Format]] | None = None) -> Self:
        match = re.match(cls.match, text, flags=re.DOTALL)
        if match is None:
            raise SyntaxError(f"Unknown code block syntax: {text}.")
        else:
            return cls([Text.parse(item, path, feed) for item in match.group(0).strip()[2:].replace("\n- ", "\n").splitlines()])

    def html(self, site: Site) -> str:
        return "<ul>"+"".join(f"<li>{item.html(site)}</li>" for item in self.items)+"</ul>"

defaultElements = [WebImage, Image, Link, List, Code, Quote, Text]