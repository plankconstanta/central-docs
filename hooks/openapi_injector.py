import os
from mkdocs.structure.nav import Section, Link
from mkdocs.structure.files import File

SPEC_EXTENSIONS = ['openapi.json', 'openapi.yaml', 'openapi.yml', 'swagger.json']

def on_files(files, config):
    """
    ЭТАП 1: Находим спецификации и генерируем markdown-страницы.
    """
    docs_dir = config['docs_dir']
    
    # Определяем базовый префикс для GitHub Pages
    site_url = config.get('site_url', '')
    if site_url and 'github.io' in site_url:
        base_prefix = '/' + site_url.split('github.io/')[-1].strip('/') + '/'
    else:
        base_prefix = '/'

    for folder in os.listdir(docs_dir):
        folder_path = os.path.join(docs_dir, folder)
        
        if os.path.isdir(folder_path) and folder != 'hooks':
            spec_name = None
            for ext in SPEC_EXTENSIONS:
                if os.path.exists(os.path.join(folder_path, ext)):
                    spec_name = ext
                    break
            
            if spec_name:
                # Формируем жесткий абсолютный URL до файла openapi.json от корня сайта
                absolute_spec_url = f"{base_prefix}central-docs/{folder}/{spec_name}"
                absolute_spec_url = '/' + absolute_spec_url.lstrip('/').replace('//', '/')

                api_page_rel_path = f"{folder}/api-docs.md"
                api_page_full_path = os.path.join(docs_dir, api_page_rel_path)
                
                with open(api_page_full_path, "w", encoding="utf-8") as f:
                    f.write(f"# Спецификация API\n\n")
                    f.write(f'<swagger-ui src="{absolute_spec_url}"/>\n')
                
                new_file = File(
                    path=api_page_rel_path,
                    src_dir=docs_dir,
                    dest_dir=config['site_dir'],
                    use_directory_urls=config['use_directory_urls']
                )
                files.append(new_file)
                
    return files


def on_nav(nav, config, files):
    """
    ЭТАП 2: Добавляем ссылки в меню, вычисляя папку проекта по его названию (item.title).
    """
    docs_dir = config['docs_dir']

    site_url = config.get('site_url', '')
    if site_url and 'github.io' in site_url:
        base_prefix = '/' + site_url.split('github.io/')[-1].strip('/') + '/'
    else:
        base_prefix = '/'

    for item in nav.items:
        # Проверяем секции первого уровня (папки проектов)
        if isinstance(item, Section) and item.title != "Главная":
            
            # НОВЫЙ ПОДХОД: Прямо ищем папку в docs/, которая соответствует этой секции.
            # Обычно папка называется так же, как проект (например, "docgen"), 
            # либо мы можем сопоставить её через os.listdir
            project_folder = None
            for folder in os.listdir(docs_dir):
                if os.path.isdir(os.path.join(docs_dir, folder)) and folder != 'hooks':
                    # Сверяем имя папки (приводим к нижнему регистру для надежности)
                    if folder.lower() in item.title.lower() or item.title.lower() in folder.lower():
                        project_folder = folder
                        break
            
            # Если по названию секции папку определить не удалось, используем старый резервный метод по первому файлу
            if not project_folder and item.children:
                first_child = item.children[0]
                if hasattr(first_child, 'url') and '/' in first_child.url:
                    url_parts = [p for p in first_child.url.strip('/').split('/') if p]
                    if "central-docs" in url_parts: url_parts.remove("central-docs")
                    if "api-docs" in url_parts: url_parts.remove("api-docs")
                    if url_parts:
                        project_folder = url_parts[0]

            # Если папка проекта успешно определена, добавляем ссылки
            if project_folder:
                
                # 1. Добавляем ссылку на Swagger UI (если файл api-docs.md был создан)
                api_page_rel_path = f"{project_folder}/api-docs.md"
                if os.path.exists(os.path.join(docs_dir, api_page_rel_path)):
                    url_suffix = "api-docs/" if config['use_directory_urls'] else "api-docs.html"
                    full_api_url = f"{base_prefix}central-docs/{project_folder}/{url_suffix}"
                    full_api_url = '/' + full_api_url.lstrip('/').replace('//', '/')
                    
                    # Проверяем, нет ли уже такой ссылки, чтобы избежать дублирования
                    if not any(hasattr(c, 'title') and "Swagger" in c.title for p in [item.children] for c in p if p):
                        api_link = Link(title="🌐 Интерактивный Swagger API", url=full_api_url)
                        item.children.append(api_link)

                # 2. Добавляем ссылку на isolated_text.txt (если он существует)
                isolated_file_path = os.path.join(docs_dir, project_folder, "isolated_text.txt")
                if os.path.exists(isolated_file_path):
                    full_file_url = f"{base_prefix}central-docs/{project_folder}/isolated_text.txt"
                    full_file_url = '/' + full_file_url.lstrip('/').replace('//', '/')
                    
                    # Проверяем, нет ли уже такой ссылки
                    if not any(hasattr(c, 'title') and "Скачать" in c.title for p in [item.children] for c in p if p):
                        download_link = Link(title="📥 Скачать документацию проекта", url=full_file_url)
                        item.children.append(download_link)
                        
    return nav
