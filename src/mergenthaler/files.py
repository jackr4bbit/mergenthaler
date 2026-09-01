from typing import Self, Any, Union, get_origin, get_args
from pathlib import Path
import datetime
import re
import inspect
import math

from .utils import validUrl,removeScheme
from . import markup
from . import site
from . import defaultSite

class File:
    def __init__(self, name: str, feed: Feed, image: markup.Image | None = None, customId: str | None = None, plugins: set[type[markup.Plugin]] | None = None):
        self.name = name
        if isinstance(image, str):
            self.image = removeScheme(image)
        else:
            self.image = image
        self.feed = feed
        self.id = type(self).makeId(customId or name)
        self.plugins = [] if plugins is None else [plugin() for plugin in plugins]

    @classmethod
    def parse(cls, path: Path, feed: Feed) -> Self:
        with path.open(mode="r") as file:
            lines = file.read().splitlines()

        return cls(**cls.parseMetadata(lines, path, feed))

    @classmethod
    def parseMetadata(cls, lines: list[str], path, feed):
        typeHints = inspect.get_annotations(cls.__init__)

        args = {}
        for name, param in inspect.signature(cls.__init__).parameters.items():
            if name == "self":
                continue

            hint = typeHints.get(name)
            origin = get_origin(hint) or hint

            if origin is Union or hasattr(hint, "__metadata__") or (hasattr(hint, "__args__") and origin is not list and origin is not set):
                possible_types = get_args(hint)

                subOrigins = [get_origin(t) or t for t in possible_types]

                if list in subOrigins:
                    origin = list
                elif set in subOrigins:
                    origin = set

            if origin is list:
                args[name] = []
            elif origin is set:
                args[name] = set()
            else:
                args[name] = None

        args["name"] = lines[0]
        args["feed"] = feed

        for i, line in enumerate(lines[1:]):
            key, value = cls.parseMetadataLine(i + 1, line, path, feed)
            if isinstance(args.get(key), list):
                args[key].append(value)
            elif isinstance(args.get(key), set):
                args[key].add(value)
            else:
                args[key] = value

        return args

    @classmethod
    def parseMetadataLine(cls, i: int, line: str, path: Path, feed: Feed) -> tuple[str, Any]:
        if line.startswith("(") and line.endswith(")"):
            return "customId", cls.makeId(line[1:-1])
        elif line.startswith("[") and line.endswith("]"):
            image = line[1:-1]
            if validUrl(image):
                return "image", markup.WebImage(removeScheme(image), image)
            else:
                if image.startswith("/"):
                    name = image[1:]
                    image = feed.root / name
                else:
                    image = path.parent / image
                    name = str(image.relative_to(feed.root))

                if not image.exists():
                    raise ValueError(f"\"{image}\" doesn't exist.")
                elif not image.is_file():
                    raise ValueError(f"\"{image}\" isn't a file.")

                return "image", markup.Image(name, image)
        #elif line.startswith("* ") and " " not in line[2:]:
        #    todo: add plugin installation and parsing
        #    return "plugins", line[2:]
        else:
            raise SyntaxError(f"Unknown metadata in line {i + 1}: '{line}'.")

    @classmethod
    def makeId(cls, name: str) -> str:
        return "".join(char for char in name.lower() if char.isalnum() or char.isspace() or char == "-").replace(" ", "-")

class Post(File):
    def __init__(self, name: str, description: str, publishDate: datetime.date, content: markup.Markup, feed: Feed, authors: list[Author | str] | None = None, image: markup.Image | None = None, tags: set[str] | None = None, plugins: set[type[markup.Plugin]] | None = None, customId: str | None = None):
        super().__init__(name, feed, image, customId, plugins)
        self.description = description
        self.date = publishDate
        self.content = content
        if authors is None:
            if feed.defaultAuthors:
                self.authors = feed.defaultAuthors
            else:
                raise ValueError("No authors specified and feed doesn't have any default authors.")
        else:
            self.authors = authors
        self.tags = set() if tags is None else tags
        self.readTime =  math.ceil(" ".join(str(element) for element in self.content.elements).replace("  ", "").count(" ") / 195)

    @classmethod
    def parse(cls, path: Path, feed: Feed) -> Self:
        with path.open(mode="r") as file:
            lines = file.read().splitlines()

        try:
            idx = lines.index("")
        except:
            raise SyntaxError("No metadata found. Make sure to seperate it from the post contents with an empty line!") from None

        args = cls.parseMetadata(lines[:idx], path, feed)
        if not args.get("authors"):
            args["authors"] = feed.defaultAuthors
        args["content"] = markup.Markup.parse("\n".join(lines[idx + 1:]), path, feed, args["plugins"])
        return cls(**args)

    @classmethod
    def parseMetadataLine(cls, i: int, line: str, path: Path, feed: Feed) -> tuple[str, Any]:
        if i == 1:
            return "description", line
        elif line.startswith("#") and " " not in line:
            return "tags", line[1:]
        elif date := re.match(r"^(\d{1,2})/(\d{1,2})/(\d{1,4})$", line):
            return "publishDate", datetime.date(int(date.group(3)), int(date.group(1)), int(date.group(2)))
        elif line.startswith(":"):
            if author := {author.id: author for author in feed.authors}.get(line[1:]):
                return "authors", author
            elif author := {author.name: author for author in feed.authors}.get(line[1:]):
                return "authors", author
            else:
                return "authors", line[1:]
        else:
            return super().parseMetadataLine(i, line, path, feed)

class Author(File):
    def __init__(self, name: str, bio: markup.Text, feed: Feed, image: markup.Image | None = None, groups: set[str] | None = None, plugins: set[type[markup.Plugin]] | None = None, customId: str | None = None):
        super().__init__(name, feed, image, customId, plugins)
        self.bio = bio
        self.groups = set() if groups is None else groups

    @classmethod
    def parse(cls, path: Path, feed: Feed) -> Self:
        with path.open(mode="r") as file:
            lines = file.read().splitlines()

        try:
            idx = lines.index("")
        except:
            raise SyntaxError("No metadata found. Make sure to seperate it from the bio with an empty line!") from None

        args = cls.parseMetadata(lines[:idx], path, feed)
        args["bio"] = markup.Text.parse("\n".join(lines[idx + 1:]), path, feed, {format for plugin in args["plugins"] for format in plugin.formats})
        return cls(**args)

    @classmethod
    def parseMetadataLine(cls, i: int, line: str, path: Path, feed: Feed) -> tuple[str, Any]:
        if line.startswith("#") and " " not in line:
            return "groups", line[1:]
        else:
            return super().parseMetadataLine(i, line, path, feed)

class DummyAuthor:
    def __init__(self, name: str):
        self.name = name

class Feed:
    def __init__(self, name: str, shortDescription: str, longDescription: str, authors: list[Author], posts: list[Post], tags: set[str], groups: set[str], root: Path, siteTheme: type[site.Site] = defaultSite.DefaultSite, defaultAuthors: list[Author] | None = None):
        self.name = name
        self.shortDescription = shortDescription
        self.longDescription = longDescription
        self.defaultAuthors = [] if defaultAuthors is None else defaultAuthors
        self.siteTheme = siteTheme
        self.authors: list[Author] = authors
        self.posts: list[Post] = posts
        self.tags: set[str] = tags
        self.groups: set[str] = groups
        self.root = root

    @classmethod
    def parse(cls, feed: Path) -> Self:
        if feed.is_file():
            feedDir = feed.parent
            feedConfig = feed
        elif feed.is_dir():
            feedFiles = list(feed.glob("*.mgfeed"))
            match len(feedFiles):
                case 0:
                    raise SyntaxError(f"No '.mgfeed' files exist in {feed}.")
                case 1:
                    feedDir = feed
                    feedConfig = feedFiles[0]
                case _:
                    raise SyntaxError(f"More than one '.mgfeed' files exist in {feed}. Specify one.")
        elif not feed.exists():
            raise SyntaxError(f"{feed} doesn't exist.")
        else:
            raise SyntaxError(f"Unknown error while looking for feed file.")

        lines = feedConfig.read_text().splitlines()
        if len(lines) < 3:
            raise SyntaxError("The feed file should contain at least three lines.")

        feed = cls(lines[0], lines[1], lines[2], [], [], set(), set(), feedDir)

        for file in feedDir.rglob("*.mgauthor"):
            if not file.is_file():
                continue

            try:
                author = Author.parse(file, feed)
            except SyntaxError as e:
                e.add_note(f"Encountered error while parsing '{file.relative_to(Path.cwd())}'.")
                raise
            feed.authors.append(author)
            feed.groups |= author.groups

        for line in lines[3:]:
            if line.startswith(":"):
                if author := {author.id: author for author in feed.authors}.get(line[1:]):
                    feed.defaultAuthors.append(author)
                elif author := {author.name: author for author in feed.authors}.get(line[1:]):
                    feed.defaultAuthors.append(author)
                else:
                    feed.defaultAuthors.append("authors")

        for file in feedDir.rglob("*.mgpost"):
            if not file.is_file():
                continue

            try:
                post = Post.parse(file, feed)
            except SyntaxError as e:
                e.add_note(f"Encountered error while parsing '{file.relative_to(Path.cwd())}'.")
                raise
            feed.posts.append(post)
            feed.tags |= post.tags

        return feed