
# Mergenthaler
## A blogging platform with its own markup language.

---


## Installation

```bash
pip install mergenthaler
```


## Features

| Feature                                                                                                                   | Status |
|---------------------------------------------------------------------------------------------------------------------------|:------:|
| [Feed files parsing](#feed)                                                                                               |   ✅   |
| [Author files parsing](#author)                                                                                           |   ✅   |
| [Post files parsing](#post)                                                                                               |   ✅   |
|                                                                                                                           |        |
| [Elements: Images (both local and external), Links, Lists, Code blocks, Block quotes, and formatted text](#markup-syntax) |   ✅   |
| [Text formats: Header, Italic, Underline, Bold, and Strikethrough](#text)                                                 |   ✅   |
|                                                                                                                           |        |
| [Static site generator](#build)                                                                                           |   ✅   |
| [Server (automatically updates for new/edited posts/authors)](#serve)                                                     |   ✅   |
| [Syntax checker](#test)                                                                                                   |   ✅   |
|                                                                                                                           |        |
| Custom site themes                                                                                                        |   🛠️   |
| Plugins                                                                                                                   |   🛠️   |
|                                                                                                                           |        |
| RSS                                                                                                                       |   ⏳   |
| Markdown to Mergenthaler Markup                                                                                           |   ⏳   |


## Usage

### Markup Syntax

#### Images
```mgmarkup
[#Alt text#][/relative/to/feed/root.png]
[#Alt text#][relative/to/this/post.png]
[#Alt text#][https://picsum.photos/200/300]
```

#### Links
```mgmarkup
[Link][https://example.com/]
```

#### Lists
```mgmarkup
- item /*one*/
- item /*two*/
```
Each item can use [text formatting](#text).

#### Code blocks
```mgmarkup
:::
Line one
Line two
:::
```

#### Block quotes
```mgmarkup
> Line 1
> Line 2
```

#### Text
Formats:
- `[*Header*]`
- `/*Italic*/`
- `__Underlined__`
- `<*Bold*>`
- `--Strikethrough--`

### Files

#### Feed
```mgfeed
Feed name
Feed tagline/short description
Feed description
:Default author name or author-id
:Default author name or author-id
```

#### Author

```mgauthor
Author name
(custom-id)
[/image.png]
#group
#group

Bio/description using Mergenthaler Markup.
```
A custom id is optional. If none is specified, the id will be the alphanumeric and hyphen characters in the author's name with spaces replaced with hyphens.  
An image is optional and can be external, relative to the post, or relative to the feed (see [the section on Markup images](#images)).   
Groups are optional.
All lines can be in any order except for the name.
Mergenthaler Markup text formats (e.g. bold) may be used in the bio, but elements (images, links, lists, code blocks, block quotes, or images) may not.

#### Post

```mgpost
Post title
Subtitle/description
(custom-id)
[/image.png]
:Author name or author-id
:Author name or author-id
:Author name or author-id
DD/MM/YYYY
#tag
#tag

Content using Mergenthaler Markup.
```
A custom id is optional. If none is specified, the id will be the alphanumeric and hyphen characters in the post's name with spaces replaced with hyphens.  
An image is optional and can be external, relative to the post, or relative to the feed (see [the section on Markup images](#images)).  
Authors are optional (if none are specified, it will use the default authors defined in the feed file) and can be the authors id or the author's name (which will throw an error if there are multiple authors with the same name). If an author's file isn't found, it will have their name on the post but they won't have a page of their own.  
Tags are optional.
All lines can be in any order except for the title and description.

### CLI

#### Build
`mg build`
Builds a static site from a Mergenthaler feed.  
`mg build -l LOCATION`  
`mg build --location LOCATION`  
Path to the feed file or directory containing it to build from (default current working dir).
`mg build -o OUTPUT`  
`mg build --output OUTPUT`  
Path to the output directory (default subdir "output" of current working dir).  
`mg build --nodelete`  
If present, Mergenthaler won't delete all existing files in the output directory.


#### Serve
`mg serve`  
Serves a Mergenthaler feed that updates when you update the files  
`mg serve -l LOCATION`  
`mg serve --location LOCATION`  
Path to the feed file or directory containing it to serve from (default current working dir).  
`mg serve -p PORT`  
`mg serve --port PORT`  
Port to listen on (default 8080).  
`mg serve --host HOST`  
The IP address to bind the server to (default 0.0.0.0).

#### Test
`mg test`.  
Tests a Mergenthaler feed's syntax.  
`mg test -l LOCATION`  
`mg test --location LOCATION`  
Path to the feed file or directory containing it to test (default current working dir).