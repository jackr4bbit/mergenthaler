# Sites

---

Site themes can make the generated/served site look more personalized.
If you're interested in making your own, [scroll down](#making-your-own) or use [the template](https://github.com/jackr4bbit/mergenthaler-site-template/).

To use a custom site theme:
1. Install the site theme with its instructions
    - The simplest way would be to do `pip install <package-name>`
      > [!Note]
      > The **Python package name** may be different from the **theme/import name** (Mergenthaler sites are importable as `mg_NAME_site`).  
      > See [Python's documentation](https://packaging.python.org/en/latest/discussions/distribution-package-vs-import-package/) for more info.
2. You use the site theme by putting `* NAME` in your `.mgfeed` file.


---
## Making your own
Mergenthaler sites are Python packages that are importable as `mg_NAME_site`, where `NAME` is the text users will put in their `.mgfeed` file.
Mergenthaler site `import mergenthaler` and define a children class of `mergenthaler.Site`.

- `mergenthaler.Site` children classes must define a string classvar called `name` that is the name of the site.
- They must define a dictionary classvar called `colors` with keys being strings of color names and values being `Colour.color` instances. You can do `colors = mergenthaler.Site.colors | {...}` to just replace some colors.
- They must define a string classvar called `assetPath` that is the directory/path (without leading or trailing slashes) of where images are hosted, used primarily by image elements.
- They must define a `files` method that returns an iterator of tuples with
  - a string of what path (from the server root) a file should go at,
    > [!Note]
    > It shouldn't begin with a slash. It may end with a slash, but it is recommended not to.
  - and either
    - a string of what should go there,
    - a string of a url that should be downloaded with HTTPS GET, or
    - a `pathlib.Path` instance of a file to copy there.


```python
from colour import Color
from collections.abc import Iterator
from pathlib import Path
from jinja2 import Environment, PackageLoader

class Site:
    name: str = "Default Site"
    colors: dict[str, Color] = {
        #...
    }
    assetPath: str = "images"

    def __init__(self, feed: mergenthaler.Feed): ...

    def files(self) -> Iterator[tuple[str, str | Path]]: ...
```