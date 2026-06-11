import os
import subprocess

from mkdocs.structure.nav import Section, Link
from mkdocs.structure.files import File

OPENAPI_FILES = [
    "openapi.json",
    "openapi.yaml",
    "openapi.yml",
    "swagger.json"
]

ASYNCAPI_FILES = [
    "asyncapi.json",
    "asyncapi.yaml",
    "asyncapi.yml"
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


def generate_asyncapi_html(spec_name, output_path):
    """
    Генерация standalone AsyncAPI HTML через Web Component.
    Работает на GitHub Pages без дополнительных сборщиков.
    """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">

    <title>AsyncAPI Reference</title>

    <script src="https://unpkg.com/@asyncapi/web-component@latest/lib/asyncapi-web-component.js"></script>

    <style>
        html,
        body {{
            margin: 0;
            padding: 0;
            height: 100%;
            width: 100%;
        }}

        asyncapi-component {{
            height: 100vh;
            width: 100%;
        }}
    </style>
</head>

<body>

<asyncapi-component
    schema-url="{spec_name}">
</asyncapi-component>

</body>
</html>
"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[AsyncAPI] Generated: {output_path}")

def on_files(files, config):
    docs_dir = config["docs_dir"]

    for folder in os.listdir(docs_dir):

        folder_path = os.path.join(docs_dir, folder)

        if not os.path.isdir(folder_path):
            continue

        if folder == "hooks":
            continue

        openapi_spec = None

        for ext in OPENAPI_FILES:

            candidate = os.path.join(folder_path, ext)

            if os.path.exists(candidate):
                openapi_spec = ext
                break

        asyncapi_spec = None

        for ext in ASYNCAPI_FILES:

            candidate = os.path.join(folder_path, ext)

            if os.path.exists(candidate):
                asyncapi_spec = ext
                break

        if not openapi_spec and not asyncapi_spec:
            continue

        #
        # OpenAPI -> api.html
        #

        if openapi_spec:

            spec_path = os.path.join(
                folder_path,
                openapi_spec
            )

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

        #
        # AsyncAPI -> asyncapi.html
        #

        if asyncapi_spec:

            asyncapi_rel_path = (
                f"{folder}/asyncapi.html"
            )

            asyncapi_full_path = os.path.join(
                docs_dir,
                asyncapi_rel_path
            )

            generate_asyncapi_html(
                asyncapi_spec,
                asyncapi_full_path
            )

            files.append(
                File(
                    path=asyncapi_rel_path,
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

        #
        # API Reference
        #

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

        #
        # AsyncAPI Reference
        #

        asyncapi_html_path = os.path.join(
            docs_dir,
            project_folder,
            "asyncapi.html"
        )

        if os.path.exists(asyncapi_html_path):

            async_url = (
                f"{base_prefix}"
                f"central-docs/"
                f"{project_folder}/asyncapi.html"
            )

            async_url = (
                "/"
                + async_url.lstrip("/")
            ).replace("//", "/")

            if (
                "🔄 AsyncAPI Reference"
                not in existing_titles
            ):

                item.children.append(
                    Link(
                        title="🔄 AsyncAPI Reference",
                        url=async_url
                    )
                )

        #
        # Download link
        #

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
