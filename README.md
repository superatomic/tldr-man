<div>
    <h1 align="center">tldr-man-client</h1>
    <h5 align="center">A tldr-pages client that works just like <code>man</code></h5>
</div>

`tldr-man-client` is a command-line client for [tldr-pages][tldr-pages],
a collection of community-maintained help pages for command-line tools.
It differs from other clients because it displays its pages as `man` pages.

This client is also able to integrate with the `man` command to fall back to displaying a tldr-page for a command when
no manpage exists.

Features:
- Fully abides by the [tldr-pages client specification][client-spec].
- Supports all page languages, not just English pages.
- Displays tldr-pages in the same style as manpages.
- Integrates with `man` to provide a fallback for missing manpages.
- Supports rendering markdown formatted tldr-pages with `--render`.
- Local cache abides by the [XDG base directory specification][xdg].
- And much more!


## Installation

### With Homebrew

Install `tldr-man-client` with [Homebrew](https://brew.sh):

```shell
brew install superatomic/tap/tldr-man
```

### With Pip

Install `tldr-man-client` with pip (version 3.10+):

```shell
pip install tldr-man
```

`tldr-man-client` additionally depends on [`pandoc`](https://pandoc.org/installing.html) being installed.

After installation, you can view a tldr-page with the `tldr` command.


## Usage

**Display a tldr-page for a command:**

```shell
tldr <COMMAND>
```

**Update the local page cache:**

```shell
tldr --update
```

**Render a page locally:**

```shell
tldr --render path/to/page.md
```

**Print tldr manpage paths as a colon-separated list (see the [Manpage Integration](#manpage-integration) section):**

```shell
tldr --manpath
```

**Display usage information:**

```shell
tldr --help
```


### Setting languages

[As specified by the tldr-pages client specification][client-spec-language],
tldr-pages from other languages can be displayed by this client
(falling back to English if the page doesn't exist for that language).

To do so, set any of the environment variables `$LANG`, `$LANGUAGE`, or `$TLDR_LANGUAGE` to the two-letter language code
for your language (e.g. `export LANGUAGE=es`),
or set the `--language` option when running `tldr` (e.g. `tldr <COMMAND> --language es`).


### Setting platforms

By default, tldr-pages will be displayed based on your current platform.
To directly specify what platform's page to use, use the `--platform` flag.

For example, to display the macOS version of the `top` command's tldr-page, run `tldr top --platform macos`.
This is the default behavior on macOS,
but `--platform macos` is required to show the macOS version of this page on other platforms.


## Manpage Integration

The command `man` can be set up to fall back to displaying tldr-pages if no manpages are found.

To do so,
add the provided line to your shell's startup script (e.g. `~/.bash_profile`, `~/.zshenv`, `~/.config/fish/config.fish`)
to add this behavior to `man`:

### Bash and Zsh

```shell
export MANPATH="$MANPATH:$(tldr --manpath)"
```

### Fish

```shell
set -gxa MANPATH (tldr --manpath)
```

[tldr-pages]: https://github.com/tldr-pages/tldr
[client-spec]: https://github.com/tldr-pages/tldr/blob/main/CLIENT-SPECIFICATION.md
[client-spec-language]: https://github.com/tldr-pages/tldr/blob/main/CLIENT-SPECIFICATION.md#language
[xdg]: https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html
