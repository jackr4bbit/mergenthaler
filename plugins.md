# Plugins

---

Plugins are python packages that provide extra [elements](/README.md#markup-syntax) and [formats](/README.md#text) that you can use in your posts and author bios.
If you're interested in making your own, [scroll down](#making-your-own) or use [the template](https://github.com/jackr4bbit/mergenthaler-plugin-template/).

To use plugins:
1. Install the plugin with its instructions
    - The simplest way would be to do `pip install <package-name>`
      > [!Note]
      > The **Python package name** may be different from the **plugin/import name** (Mergenthaler plugins are importable as `mg_NAME`).  
      > See [Python's documentation](https://packaging.python.org/en/latest/discussions/distribution-package-vs-import-package/) for more info.
2. You mark a file as using a plugin by putting `* NAME` in the metadata.
3. You use the elements and/or formats defined by the plugin in your post or author bio with the plugin's syntax.

Syntax in posts/author bios will prioritize plugins added first in your metadata over plugins added at the end.

---
## Making your own
Mergenthaler plugins are Python packages that are importable as `mg_NAME`, where `NAME` is the text users will put in their files.
Mergenthaler plugins `import mergenthaler` and define children classes of `mergenthaler.Element` and `mergenthaler.Format`.

### Elements
- `mergenthaler.Element` children classes must define a string classvar called `match` that is the RegEx to search with.
- They must define a `__str__` method that gets used for previews of Mergenthaler Markup. For things like images, I would recommend making `__str__` always return an empty string.
- They must define an `html` method that gets passed an instance of `mergenthaler.Site` and returns a string of an HTML representation of the element.
- They must define a `parse` classmethod that returns an instance of your element and gets passed
  - the text that matched the RegEx in the string classvar `match`,
  - a `pathlib.Path` instance representing the file that is currently being parsed,
  - a `mergenthaler.Feed` instance, and
  - a list of `Format` children classes that comes from the built-in formats and formats provided by plugins.


```python
from typing import Self

class Element:
    match: str
    
    def __str__(self) -> str: ...

    @classmethod
    def parse(cls, text: str, path: mergenthaler.Path, feed: mergenthaler.Feed, formats: list[type[mergenthaler.Format]] | None = None) -> Self | None: ...

    def html(self, site: mergenthaler.Site) -> str: ...
```

### Formats

There are two (built-in) ways to make Mergenthaler formats: `mergenthaler.Format` and `mergenthaler.SimpleFormat`.

#### `Mergenthaler.Format`
- `mergenthaler.Format` children classes must define a string classvar called `name` that is the name of the format.
- They must define a string classvar called `start` that is the RegEx to search for the start of the formatting with.
- They must define a string classvar called `end` that is the RegEx to search for the end of the formatting with.
- They may define a `__init__` method that gets passed the `mergenthaler.Text` instance the format is applied to and a dictionary containing the values of capture groups in the `start` and `end` RegEx classvars. The default just sets `self.text` and `self.groups` to its args.
- They must define an `html` method that gets passed an instance of `mergenthaler.Site` and returns a string of an HTML representation of the formatted text. It may call `html(self, site, noFormat=True)` on the `mergenthaler.Text` instance that was passed to it's `__init__` to get a string of the HTML of the formatted text inside this formatted text.


```python
class Format:
    name: str
    start: str
    end: str

    def __init__(self, text: mergenthaler.Text, groups: dict[str | int, str]):
        self.text = text
        self.groups = groups

    def html(self, site: mergenthaler.Site) -> str: ...
```

#### `Mergenthaler.SimpleFormat`

`mergenthaler.SimpleFormat` makes it easy to make a format.
- `mergenthaler.SimpleFormat` children classes must define a string classvar called `name` that is the name of the format.
- They must define a string classvar called `start` that is the RegEx to search for the start of the formatting with.
- They must define a string classvar called `end` that is the RegEx to search for the end of the formatting with.
- They must define a string classvar called `htmlStart` that is the HTML tag to put at the beginning of the formatted text.
- They may have a string classvar called `htmlEnd` that is the HTML tag to put at the end of the formatted text. If none is specified, it will be the `htmlStart` classvar with a slash after the first character (so as to close an HTML tag). 


```python
class SimpleFormat:
    name: str
    start: str
    end: str
    htmlStart: str
    htmlEnd: str | None = None
```