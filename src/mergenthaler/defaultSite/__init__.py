from packaging.version import Version
from colour import Color
from collections.abc import Iterator
from pathlib import Path
from jinja2 import Template
from datetime import date
from importlib import resources
from ..site import Site
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


class DefaultSite(Site):
    name = "Default Site"
    version = Version("1.0.0")
    colors = {
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

    def __init__(self, feed: files.Feed):
        super().__init__(feed)
        self.jinjaArgs = {
            "feed": self.feed,
            "now": date.today(),
            "site": self,
            "copyright": f"© {sorted(self.feed.posts, key=lambda post: post.date, reverse=True)[0].date.strftime("%Y")} {formatList([author.name for author in self.feed.defaultAuthors]) if self.feed.defaultAuthors else self.feed.name}"
        }
        self.notFoundPage = Template((resources.files("mergenthaler") / "defaultSite" / "404.html").read_text()).render(**self.jinjaArgs)

    def files(self) -> Iterator[tuple[str, str | Path]]:
        theme = resources.files("mergenthaler") / "defaultSite"

        posts = sorted(self.feed.posts, key=lambda post: post.date, reverse=True)

        yield "index.html", Template((theme / "index.html").read_text()).render(
            **self.jinjaArgs,
            latestPost=posts[0],
            posts=posts[1:]
        )

        yield "style.css", Template((theme / "style.css").read_text()).render(
            **{name: color.hex for name, color in self.colors.items()}
        )

        yield "reveal.js", (theme / "reveal.js").read_text()

        yield "posts/index.html", Template((theme / "posts.html").read_text()).render(
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
            yield f"authors/{author.id}.html", Template((theme / "author.html").read_text()).render(
                **self.jinjaArgs,
                author=author,
                posts=[post for post in self.feed.posts if author in post.authors]
            )

            if image := saveImage(author.image):
                yield image

        for post in self.feed.posts:
            yield f"posts/{post.id}.html", Template((theme / "post.html").read_text()).render(
                **self.jinjaArgs,
                post=post
            )

            for element in post.content.elements + [post.image]:
                if image := saveImage(element):
                    yield image

        for tag in self.feed.tags:
            yield f"tags/{tag}.html", Template((theme / "tag.html").read_text()).render(
                **self.jinjaArgs,
                tag=tag,
                posts=[post for post in posts if tag in post.tags]
            )

        for group in self.feed.groups:
            yield f"groups/{group}.html", Template((theme / "group.html").read_text()).render(
                **self.jinjaArgs,
                group=group,
                authors=[author for author in self.feed.authors if group in author.groups]
            )