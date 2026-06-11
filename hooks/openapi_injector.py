import json
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


def generate_asyncapi_markdown(spec_path, output_path):
    """
    Генерация Markdown-документации по AsyncAPI
    для аналитиков и архитекторов.
    """

    with open(spec_path, "r", encoding="utf-8") as f:
        spec = json.load(f)

    channels = spec.get("channels", {})
    messages = spec.get("components", {}).get("messages", {})

    md = []

    title = (
        spec.get("info", {})
        .get("title", "Event Reference")
    )

    description = (
        spec.get("info", {})
        .get("description", "")
    )

    md.append(f"# {title}")
    md.append("")

    if description:
        md.append(description)
        md.append("")

    #
    # Summary
    #

    if channels:

        md.append("## Сводка событий")
        md.append("")

        md.append("| Канал | Направление | Сообщение |")
        md.append("|--------|-------------|------------|")

        for channel_name, channel_data in channels.items():

            direction = None
            message_ref = None

            if "publish" in channel_data:

                direction = "publish"

                message_ref = (
                    channel_data["publish"]
                    .get("message", {})
                    .get("$ref", "")
                )

            elif "subscribe" in channel_data:

                direction = "subscribe"

                message_ref = (
                    channel_data["subscribe"]
                    .get("message", {})
                    .get("$ref", "")
                )

            message_name = (
                message_ref.split("/")[-1]
                if message_ref
                else "-"
            )

            md.append(
                f"| {channel_name} | "
                f"{direction or '-'} | "
                f"{message_name} |"
            )

        md.append("")
        md.append("---")
        md.append("")

    #
    # Details
    #

    for channel_name, channel_data in channels.items():

        direction = None
        message_ref = None

        if "publish" in channel_data:

            direction = "publish"

            message_ref = (
                channel_data["publish"]
                .get("message", {})
                .get("$ref")
            )

        elif "subscribe" in channel_data:

            direction = "subscribe"

            message_ref = (
                channel_data["subscribe"]
                .get("message", {})
                .get("$ref")
            )

        if not message_ref:
            continue

        message_name = message_ref.split("/")[-1]

        message = messages.get(
            message_name,
            {}
        )

        payload = message.get(
            "payload",
            {}
        )

        properties = payload.get(
            "properties",
            {}
        )

        required = set(
            payload.get(
                "required",
                []
            )
        )

        md.append(f"## {channel_name}")
        md.append("")

        md.append(
            f"**Направление:** `{direction}`"
        )
        md.append("")

        md.append(
            f"**Сообщение:** `{message_name}`"
        )
        md.append("")

        md.append("### Поля сообщения")
        md.append("")

        md.append(
            "| Поле | Тип | Обязательное | Описание |"
        )

        md.append(
            "|------|------|--------------|----------|"
        )

        for field_name, field_info in properties.items():

            field_type = field_info.get(
                "type",
                "-"
            )

            description = field_info.get(
                "description",
                ""
            )

            required_flag = (
                "Да"
                if field_name in required
                else "Нет"
            )

            md.append(
                f"| {field_name} | "
                f"{field_type} | "
                f"{required_flag} | "
                f"{description} |"
            )

        md.append("")
        md.append("---")
        md.append("")

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as f:
        f.write("\n".join(md))

    print(
        f"[AsyncAPI] Generated: "
        f"{output_path}"
    )


def on_files(files, config):
    docs_dir = config["docs_dir"]

    for folder in os.listdir(docs_dir):

        folder_path = os.path.join(
            docs_dir,
            folder
        )

        if not os.path.isdir(folder_path):
            continue

        if folder == "hooks":
            continue

        #
        # OpenAPI
        #

        openapi_spec = None

        for ext in OPENAPI_FILES:

            candidate = os.path.join(
                folder_path,
                ext
            )

            if os.path.exists(candidate):

                openapi_spec = ext
                break

        #
        # AsyncAPI
        #

        asyncapi_spec = None

        for ext in ASYNCAPI_FILES:

            candidate = os.path.join(
                folder_path,
                ext
            )

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

            api_html_rel_path = (
                f"{folder}/api.html"
            )

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
        # AsyncAPI -> events.md
        #

        if asyncapi_spec:

            spec_path = os.path.join(
                folder_path,
                asyncapi_spec
            )

            events_rel_path = (
                f"{folder}/events.md"
            )

            events_full_path = os.path.join(
                docs_dir,
                events_rel_path
            )

            generate_asyncapi_markdown(
                spec_path,
                events_full_path
            )

            files.append(
                File(
                    path=events_rel_path,
                    src_dir=docs_dir,
                    dest_dir=config["site_dir"],
                    use_directory_urls=config[
                        "use_directory_urls"
                    ]
                )
            )

    return files


def on_nav(nav, config, files):

    docs_dir = config["docs_dir"]

    site_url = config.get(
        "site_url",
        ""
    )

    if site_url and "github.io" in site_url:

        base_prefix = (
            "/"
            + site_url.split(
                "github.io/"
            )[-1].strip("/")
            + "/"
        )

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
                    url_parts.remove(
                        "central-docs"
                    )

                if url_parts:

                    project_folder = (
                        url_parts[0]
                    )

                    break

        if not project_folder:
            continue

        existing_titles = []

        if item.children:

            for child in item.children:

                if (
                    hasattr(child, "title")
                    and child.title
                ):
                    existing_titles.append(
                        child.title
                    )

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

            if (
                "📘 API Reference"
                not in existing_titles
            ):

                item.children.append(
                    Link(
                        title="📘 API Reference",
                        url=api_url
                    )
                )

        #
        # Event Reference
        #

        events_md_path = os.path.join(
            docs_dir,
            project_folder,
            "events.md"
        )

        if os.path.exists(events_md_path):

            if config.get(
                "use_directory_urls",
                True
            ):

                events_url = (
                    f"{base_prefix}"
                    f"central-docs/"
                    f"{project_folder}/events/"
                )

            else:

                events_url = (
                    f"{base_prefix}"
                    f"central-docs/"
                    f"{project_folder}/events.html"
                )

            events_url = (
                "/"
                + events_url.lstrip("/")
            ).replace("//", "/")

            if (
                "🔄 Event Reference"
                not in existing_titles
            ):

                item.children.append(
                    Link(
                        title="🔄 Event Reference",
                        url=events_url
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

        if os.path.exists(
            isolated_file_path
        ):

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
