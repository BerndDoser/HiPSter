#!/usr/bin/env python3

import os

from jsonargparse import ArgumentParser

from hipster import HTMLGenerator, Task


def main():
    """
    Main function to generate HiPS data.
    """

    parser = ArgumentParser(description="Generate HiPS representation.")

    parser.add_class_arguments(HTMLGenerator, "html")
    parser.add_argument("--tasks", type=list[Task])
    parser.add_argument("--config", action="config", help="Path to the config file.")
    parser.add_argument("--root_path", type=str, default="./HiPSter")
    parser.add_argument("--only_html", action="store_true", help="Only generate HTML.")
    parser.add_argument(
        "--verbose", "-v", default=0, action="count", help="Print level."
    )
    parser.add_argument(
        "--overwrite", action="store_true", help="Overwrite existing files."
    )
    parser.link_arguments("root_path", "html.root_path")
    parser.link_arguments("root_path", "tasks.init_args.root_path")
    parser.link_arguments("title", "tasks.init_args.title")

    cfg = parser.parse_args()
    cfg = parser.instantiate_classes(cfg)

    # Print list of tasks
    if cfg.verbose:
        print("Base URL:", cfg.html.url)
        print("Tasks:")
        for task in cfg.tasks:
            print(f"  - {task.__class__.__name__}")

    os.makedirs(cfg.root_path, exist_ok=cfg.overwrite)

    # Execute tasks
    for task in cfg.tasks:
        task.register(cfg.html)
        if not cfg.only_html:
            task.execute()

    # Generate HTML main page
    cfg.html.generate()


if __name__ == "__main__":
    main()
