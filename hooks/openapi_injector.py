import os
from openapi_parser import parse as parse_openapi
from mkdocs.structure.nav import Section, Link
from mkdocs.structure.files import File

SPEC_EXTENSIONS = ['openapi.json', 'openapi.yaml', 'openapi.yml', 'swagger.json']

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
