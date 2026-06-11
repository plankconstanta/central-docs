import os
import subprocess

from mkdocs.structure.nav import Section, Link
from mkdocs.structure.files import File

SPEC_EXTENSIONS = [
    "openapi.json",
    "openapi.yaml",
    "openapi.yml",
    "swagger.json"
]


def generate_redoc_html(spec_path, output_path):
    """
    Генерация статической HTML-документации через ReDocly.
    """

    theme_path = os.path.join(
        os.path.dirname(__file__),
        "redoc-theme.json"
    )

    try:
        subprocess.run(
            [
                "redocly",
                "build-docs",
                spec_path,
                "--theme.openapi.theme=" + theme_path,
                "-o",
                output_path
            ],
            check=True
        )

        print(f"[ReDoc] Generated: {output_path}")

    except subprocess.CalledProcessError as e:
        print(f"[ReDoc] Failed for {spec_path}: {e}")


def on_files(files, config):
    docs_dir = config["docs_dir"]

    for folder in os.listdir(docs_dir):

        folder_path = os.path.join(docs_dir, folder)

        if not os.path.isdir(folder_path):
            continue

        if folder == "hooks":
            continue

        spec_name = None

        for ext in SPEC_EXTENSIONS:

            candidate = os.path.join(folder_path, ext)

            if os.path.exists(candidate):
                spec_name = ext
                break

        if not spec_name:
            continue

        spec_path = os.path.join(folder_path, spec_name)

        api_html_rel_path = f"{folder}/api.html"
        api_html_full_path = os.path.join(
            docs_dir,
            api_html_rel_path
        )

        generate_redoc_html(
            spec_path,
            api_html_full_path
        )

        files.append(
            File(
                path=api_html_rel_path,
                src_dir=docs_dir,
                dest_dir=config["site_dir"],
                use_directory_urls=False
            )
        )

    return files


def on_nav(nav, config, files):

    docs_dir = config["docs_dir"]

    site_url = config.get("site_url", "")

    if site_url and "github.io" in site_url:
        base_prefix = "/" + site_url.split(
            "github.io/"
        )[-1].strip("/") + "/"
    else:
        base_prefix = "/"

    for item in nav.items:

        if not isinstance(item, Section):
            continue

        if item.title == "Главная":
            continue

        project_folder = None

        if item.children:

            for child in item.children:

                if not hasattr(child, "url"):
                    continue

                if not child.url:
                    continue

                url_parts = [
                    p
                    for p in child.url.strip("/").split("/")
                    if p
                ]

                if "central-docs" in url_parts:
                    url_parts.remove("central-docs")

                if url_parts:
                    project_folder = url_parts[0]
                    break

        if not project_folder:
            continue

        existing_titles = []

        if item.children:

            for child in item.children:

                if hasattr(child, "title") and child.title:
                    existing_titles.append(child.title)

        api_html_path = os.path.join(
            docs_dir,
            project_folder,
            "api.html"
        )

        if os.path.exists(api_html_path):

            api_url = (
                f"{base_prefix}"
                f"central-docs/"
                f"{project_folder}/api.html"
            )

            api_url = (
                "/"
                + api_url.lstrip("/")
            ).replace("//", "/")

            if "📘 API Reference" not in existing_titles:

                item.children.append(
                    Link(
                        title="📘 API Reference",
                        url=api_url
                    )
                )

        isolated_file_path = os.path.join(
            docs_dir,
            project_folder,
            "isolated_text.txt"
        )

        if os.path.exists(isolated_file_path):

            file_url = (
                f"{base_prefix}"
                f"central-docs/"
                f"{project_folder}/isolated_text.txt"
            )

            file_url = (
                "/"
                + file_url.lstrip("/")
            ).replace("//", "/")

            if (
                "📥 Скачать документацию проекта"
                not in existing_titles
            ):
                item.children.append(
                    Link(
                        title="📥 Скачать документацию проекта",
                        url=file_url
                    )
                )

    return nav
