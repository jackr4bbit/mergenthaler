from pathlib import Path
import shutil
import argparse
from flask import Flask, send_file
from waitress import serve
import requests

from .files import Feed
from .utils import validUrl

def main():
    parser = argparse.ArgumentParser(description="The Mergenthaler validator, builder, and server.")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available subcommands")

    testCommand = subparsers.add_parser("test", help="Tests a Mergenthaler feed's syntax.")
    testCommand.add_argument("-l", "--location", type=str, help="Path to the feed file or directory containing it to test (default current working dir).")

    buildCommand = subparsers.add_parser("build", help="Builds a static site from a Mergenthaler feed.")
    buildCommand.add_argument("-l", "--location", type=str, help="Path to the feed file or directory containing it to build from (default current working dir).")
    buildCommand.add_argument("-o", "--output", type=str, help="Path to the output directory default subdir \"output\" of current working dir).")
    buildCommand.add_argument("--nodelete", action="store_true", help="Don't delete all existing files in the output directory.")

    serveCommand = subparsers.add_parser("serve", help="Serves a Mergenthaler feed that updates when you update the files.")
    serveCommand.add_argument("-l", "--location", type=str, help="Path to the feed file or directory containing it to serve from (default current working dir).")
    serveCommand.add_argument("-p", "--port", type=int, help="Port to listen on (default 8080).", default=8080)
    serveCommand.add_argument("--host", type=str, help="The IP address to bind the server to (default 0.0.0.0).", default="0.0.0.0")

    args = parser.parse_args()

    if args.location:
        inputPath = Path(args.location)
    else:
        inputPath = Path.cwd()

    feed = Feed.parse(inputPath)

    match args.command:
        case "build":
            if args.output:
                outputPath = Path(args.output)
            else:
                outputPath = Path.cwd() / "output"

            if not args.nodelete and outputPath.exists():
                for item in outputPath.iterdir():
                    if item.is_file() or item.is_symlink():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)

            for path, contents in feed.siteTheme(feed).files():
                path = outputPath / path
                path.parent.mkdir(parents=True, exist_ok=True)
                if isinstance(contents, Path):
                    contents.copy(path, preserve_metadata=True)
                elif isinstance(contents, str):
                    if validUrl(contents):
                        with path.open(mode="wb") as file:
                            file.write(requests.get(contents).content)
                    else:
                        with path.open(mode="w") as f:
                            f.write(contents)

        case "serve":
            app = Flask(__name__)

            @app.route("/", defaults={"subpath": ""}, methods=["GET"])
            @app.route("/<path:subpath>", methods=["GET"])
            def route(subpath: str):
                def getFile(path: str) -> str | Path | None:
                    return next((file[1] for file in site.files() if file[0] == path), None)

                if subpath.endswith("/"):
                    subpath = subpath[:-1]

                feed = Feed.parse(inputPath)
                site = feed.siteTheme(feed)

                if subpath == "":
                    file = getFile("index.html")
                else:
                    file = getFile(subpath)
                    for suffix in [".html", "/index.html"]:
                        if file is not None:
                            break
                        file = getFile(subpath+suffix)

                if file is None:
                    return site.notFoundPage, 404
                elif isinstance(file, Path):
                    return send_file(file), 200, ({"Content-Type": "text/css"} if file.suffix == ".css" else None)
                else:
                    if validUrl(file):
                        response = requests.get(file)
                        return response.content, 200, {"Content-Type": response.headers.get("Content-Type")}
                    else:
                        return file, 200, ({"Content-Type": "text/css"} if subpath.endswith(".css") else None)

            print(f"Starting server at {args.host}:{args.port}!")
            serve(app, host=args.host, port=args.port)

        case "test":
            print("Successful!")

if __name__ == "__main__":
    main()