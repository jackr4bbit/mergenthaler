from colour import Color
from collections.abc import Iterator
from pathlib import Path
from jinja2 import Environment, PackageLoader
from datetime import date
from importlib import resources

from .. import files
from .. import markup


def formatList(items: list[str]):
    items = [str(item) for item in items]

    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"

    return f"{", ".join(items[:-1])}, and {items[-1]}"


class Site:
    name: str = "Default Site"
    colors: dict[str, Color] = {
        "text": Color("#171717"),
        "accent": Color("#2563eb"),
        "muted": Color("#737373"),
        "background": Color("#fafafa"),
        "postImageBackground": Color("#e5e5e5"),
        "green": Color("#10b981"),
        "navy": Color("#1e3a8a"),
        "blue": Color("#3b82f6"),
        "orange": Color("#f97316"),
        "yellow": Color("#d9ab06")
    }
    assetPath: str = "images"

    def __init__(self, feed: files.Feed):
        self.feed = feed
        self.jinjaArgs = {
            "feed": self.feed,
            "now": date.today(),
            "site": self,
            "copyright": f"© {sorted(self.feed.posts, key=lambda post: post.date, reverse=True)[0].date.strftime("%Y")} {formatList([author.name for author in self.feed.defaultAuthors]) if self.feed.defaultAuthors else self.feed.name}"
        }
        self.jinjaEnv = Environment(loader=PackageLoader("mergenthaler", "site"))
        self.notFoundPage = self.jinjaEnv.get_template("404.html").render(**self.jinjaArgs)

    def files(self) -> Iterator[tuple[str, str | Path]]:
        posts = sorted(self.feed.posts, key=lambda post: post.date, reverse=True)

        yield "index.html", self.jinjaEnv.get_template("index.html").render(
            **self.jinjaArgs,
            latestPost=posts[0],
            posts=posts[1:]
        )

        yield "style.css", self.jinjaEnv.get_template("style.css").render(
            **{name: color.hex for name, color in self.colors.items()}
        )

        yield "reveal.js", (resources.files("mergenthaler") / "site" / "reveal.js").read_text()

        yield "posts/index.html", self.jinjaEnv.get_template("posts.html").render(
            **self.jinjaArgs,
            posts=posts
        )

        def saveImage(element: markup.Element | None) -> tuple[str, str | Path] | None:
            if isinstance(element, markup.WebImage):
                return f"{self.__class__.assetPath}/{element.name}", element.url
            elif isinstance(element, markup.Image):
                return f"{self.__class__.assetPath}/{element.name}", element.path

            return None

        for author in self.feed.authors:
            yield f"authors/{author.id}.html", self.jinjaEnv.get_template("author.html").render(
                **self.jinjaArgs,
                author=author,
                posts=[post for post in self.feed.posts if author in post.authors]
            )

            if image := saveImage(author.image):
                yield image

        for post in self.feed.posts:
            yield f"posts/{post.id}.html", self.jinjaEnv.get_template("post.html").render(
                **self.jinjaArgs,
                post=post
            )

            for element in post.content.elements + [post.image]:
                if image := saveImage(element):
                    yield image

        for tag in self.feed.tags:
            yield f"tags/{tag}.html", self.jinjaEnv.get_template("tag.html").render(
                **self.jinjaArgs,
                tag=tag,
                posts=[post for post in posts if tag in post.tags]
            )

        for group in self.feed.groups:
            yield f"groups/{group}.html", self.jinjaEnv.get_template("group.html").render(
                **self.jinjaArgs,
                group=group,
                authors=[author for author in self.feed.authors if group in author.groups]
            )