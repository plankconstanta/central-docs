import os
from openapi_parser import parse as parse_openapi
from mkdocs.structure.nav import Section, Link
from mkdocs.structure.files import File

SPEC_EXTENSIONS = ['openapi.json', 'openapi.yaml', 'openapi.yml', 'swagger.json']

def render_schema_to_markdown(schema, required_fields=None, depth=0):
    """Рекурсивно превращает JSON-схему (модель данных) в строки Markdown-таблицы."""
    lines = []
    if not schema:
        return lines
        
    indent = "» " * depth
    req_list = required_fields or []

    # Если это объект, парсим его свойства (properties)
    if hasattr(schema, 'properties') and schema.properties:
        for prop_name, prop in schema.properties.items():
            p_type = getattr(prop, 'type', 'object')
            p_desc = getattr(prop, 'description', '') or ''
            p_req = "Да" if prop_name in req_list else "Нет"
            
            # Обработка массивов объектов
            if p_type == 'array' and hasattr(prop, 'items') and prop.items:
                p_type = f"array of {getattr(prop.items, 'type', 'object')}"
            
            lines.append(f"| {indent}`{prop_name}` | {p_type} | {p_req} | {p_desc} |")
            
            # Если свойство само является объектом, уходим вглубь
            if hasattr(prop, 'properties') and prop.properties:
                sub_req = getattr(prop, 'required', [])
                lines.extend(render_schema_to_markdown(prop, sub_req, depth + 1))
            elif p_type.startswith('array of') and hasattr(prop.items, 'properties') and prop.items.properties:
                sub_req = getattr(prop.items, 'required', [])
                lines.extend(render_schema_to_markdown(prop.items, sub_req, depth + 1))
                
    return lines

def openapi_to_markdown(file_path):
    """Парсит OpenAPI файл и генерирует структурированный Markdown текст."""
    try:
        specification = parse_openapi(file_path)
    except Exception as e:
        return f"# Ошибка парсинга API\n\nНе удалось прочитать спецификацию: {str(e)}"

    md = []
    # Заголовок документации берем из OpenAPI
    title = specification.info.title if specification.info else "Спецификация API"
    desc = specification.info.description if specification.info and specification.info.description else ""
    md.append(f"# Спецификация API — {title}\n")
    if desc:
        md.append(f"{desc}\n")

    if not specification.paths:
        md.append("_Методы API не найдены._")
        return "\n".join(md)

    # Обходим все пути и методы
    for path_data in specification.paths:
        path_url = path_data.path
        
        for operation in path_data.operations:
            method = operation.method.value.upper()
            op_summary = operation.summary or ""
            op_desc = operation.description or ""
            
            md.append(f"## {method} `{path_url}`")
            if op_summary:
                md.append(f"**{op_summary}**\n")
            if op_desc:
                md.append(f"{op_desc}\n")

            # 1. ПАРАМЕТРЫ (Query, Path, Headers)
            if operation.parameters:
                md.append("### Параметры запроса\n")
                md.append("| Имя | Расположение | Тип | Обязателен | Описание |")
                md.append("| :--- | :--- | :--- | :--- | :--- |")
                for param in operation.parameters:
                    p_name = param.name
                    p_in = param.location.value if param.location else "query"
                    p_type = getattr(param.schema, 'type', 'string') if param.schema else "string"
                    p_req = "Да" if param.required else "Нет"
                    p_desc = param.description or ""
                    md.append(f"| `{p_name}` | {p_in} | {p_type} | {p_req} | {p_desc} |")
                md.append("")

            # 2. ТЕЛО ЗАПРОСА (Request Body)
            if operation.request_body and operation.request_body.content:
                md.append("### Структура тела запроса (JSON)\n")
                for content in operation.request_body.content:
                    if 'json' in content.media_type and content.schema:
                        md.append("| Поле | Тип | Обязательно | Описание |")
                        md.append("| :--- | :--- | :--- | :--- |")
                        req_fields = getattr(content.schema, 'required', [])
                        rows = render_schema_to_markdown(content.schema, req_fields)
                        md.extend(rows)
                md.append("")

            # 3. ОТВЕТЫ (Responses)
            if operation.responses:
                md.append("### Ответы сервера\n")
                for resp in operation.responses:
                    code = resp.status_code
                    r_desc = resp.description or ""
                    md.append(f"**Код {code}:** {r_desc}\n")
                    
                    if resp.content:
                        for content in resp.content:
                            if 'json' in content.media_type and content.schema:
                                md.append("| Поле | Тип | Обязательно | Описание |")
                                md.append("| :--- | :--- | :--- | :--- |")
                                req_fields = getattr(content.schema, 'required', [])
                                rows = render_schema_to_markdown(content.schema, req_fields)
                                md.extend(rows)
                                md.append("")
            md.append("---")

    return "\n".join(md)

def on_files(files, config):
    """ЭТАП 1: Находим спецификации и генерируем текстовые страницы."""
    docs_dir = config['docs_dir']
    
    for folder in os.listdir(docs_dir):
        folder_path = os.path.join(docs_dir, folder)
        
        if os.path.isdir(folder_path) and folder != 'hooks':
            spec_name = None
            for ext in SPEC_EXTENSIONS:
                if os.path.exists(os.path.join(folder_path, ext)):
                    spec_name = ext
                    break
            
            if spec_name:
                spec_full_path = os.path.join(folder_path, spec_name)
                api_page_rel_path = f"{folder}/api-docs.md"
                api_page_full_path = os.path.join(docs_dir, api_page_rel_path)
                
                # ГЕНЕРИРУЕМ ЧИСТЫЙ MARKDOWN С ТАБЛИЦАМИ
                markdown_content = openapi_to_markdown(spec_full_path)
                with open(api_page_full_path, "w", encoding="utf-8") as f:
                    f.write(markdown_content)
                
                new_file = File(
                    path=api_page_rel_path,
                    src_dir=docs_dir,
                    dest_dir=config['site_dir'],
                    use_directory_urls=config['use_directory_urls']
                )
                files.append(new_file)
                
    return files

def on_nav(nav, config, files):
    """ЭТАП 2: Добавляем ссылки в меню."""
    docs_dir = config['docs_dir']

    site_url = config.get('site_url', '')
    if site_url and 'github.io' in site_url:
        base_prefix = '/' + site_url.split('github.io/')[-1].strip('/') + '/'
    else:
        base_prefix = '/'

    for item in nav.items:
        if isinstance(item, Section) and item.title != "Главная":
            project_folder = None
            
            if item.children:
                for child in item.children:
                    if hasattr(child, 'url') and child.url:
                        url_parts = [p for p in child.url.strip('/').split('/') if p]
                        if "central-docs" in url_parts: url_parts.remove("central-docs")
                        if "api-docs" in url_parts: url_parts.remove("api-docs")
                        if url_parts:
                            project_folder = url_parts
                            break

            if project_folder and isinstance(project_folder, str):
                existing_titles = []
                if item.children:
                    for child in item.children:
                        if hasattr(child, 'title') and child.title is not None:
                            existing_titles.append(child.title)

                # 1. Текстовая страница API
                api_page_rel_path = f"{project_folder}/api-docs.md"
                if os.path.exists(os.path.join(docs_dir, api_page_rel_path)):
                    url_suffix = "api-docs/" if config['use_directory_urls'] else "api-docs.html"
                    full_api_url = f"{base_prefix}central-docs/{project_folder}/{url_suffix}"
                    full_api_url = '/' + full_api_url.lstrip('/').replace('//', '/')
                    
                    if "📋 Спецификация API (Таблицы)" not in existing_titles:
                        # Переименовали пункт меню, чтобы аналитикам было понятнее
                        api_link = Link(title="📋 Спецификация API (Таблицы)", url=full_api_url)
                        item.children.append(api_link)

                # 2. Ссылка на isolated_text.txt
                isolated_file_path = os.path.join(docs_dir, project_folder, "isolated_text.txt")
                if os.path.exists(isolated_file_path):
                    full_file_url = f"{base_prefix}central-docs/{project_folder}/isolated_text.txt"
                    full_file_url = '/' + full_file_url.lstrip('/').replace('//', '/')
                    
                    if "📥 Скачать документацию проекта" not in existing_titles:
                        download_link = Link(title="📥 Скачать документацию проекта", url=full_file_url)
                        item.children.append(download_link)
                        
    return nav
