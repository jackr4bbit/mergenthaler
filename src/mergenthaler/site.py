from packaging.version import Version
from colour import Color
from collections.abc import Iterator
from pathlib import Path
from . import files


class Site:
    name: str
    version: Version
    colors: dict[str, Color] = {
        "white": Color("#FFFFFF"),
        "black": Color("#000000"),
        "red": Color("#FF0000"),
        "green": Color("#008000"),
        "lime": Color("#00FF00"),
        "blue": Color("#0000FF"),
        "yellow": Color("#FFFF00"),
        "cyan": Color("#00FFFF"),
        "magenta": Color("#FF00FF"),
        "gray": Color("#808080"),
        "silver": Color("#C0C0C0"),
        "maroon": Color("#800000"),
        "olive": Color("#808000"),
        "teal": Color("#008080"),
        "navy": Color("#000080"),
        "purple": Color("#800080")
    }
    assetPath: str = "images"

    def __init__(self, feed: files.Feed) -> None:
        self.feed = feed
        self.notFoundPage = "404: Page not found."

    def files(self) -> Iterator[tuple[str, str | Path]]:
        for author in self.feed.authors:
            yield f"authors/{author.id}.html", author.bio.html(self)

        for post in self.feed.posts:
            yield f"posts/{post.id}.html", post.content.html(self)
            if isinstance(post.image, str):
                yield f"{self.__class__.assetPath}/posts/{post.id}{post.image.split("/")[-1].split(".")[1:]}", post.image
            elif isinstance(post.image, Path):
                yield f"{self.__class__.assetPath}/posts/{post.id}{"".join(post.image.suffixes)}", post.image

        for tag in self.feed.tags:
            yield f"tags/{tag}.html", tag

        for group in self.feed.groups:
            yield f"groups/{group}.html", group
