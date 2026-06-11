import os
from mkdocs.structure.nav import Section, Link
from mkdocs.structure.files import File

SPEC_EXTENSIONS = ['openapi.json', 'openapi.yaml', 'openapi.yml', 'swagger.json']

def on_files(files, config):
    """
    ЭТАП 1: Находим спецификации и генерируем markdown-страницы.
    """
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
                spec_relative_path = f"{folder}/{spec_name}"
                api_page_rel_path = f"{folder}/api-docs.md"
                api_page_full_path = os.path.join(docs_dir, api_page_rel_path)
                
                with open(api_page_full_path, "w", encoding="utf-8") as f:
                    f.write(f"# Спецификация API\n\n")
                    f.write(f'<swagger-ui src="{spec_relative_path}"/>\n')
                
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
    ЭТАП 2: Добавляем ссылки в меню, вычисляя правильную папку проекта.
    """
    docs_dir = config['docs_dir']

    site_url = config.get('site_url', '')
    if site_url and 'github.io' in site_url:
        base_prefix = '/' + site_url.split('github.io/')[-1].strip('/') + '/'
    else:
        base_prefix = '/'

    for item in nav.items:
        if isinstance(item, Section) and item.title != "Главная":
            if item.children:
                first_child = item.children[0]
                
                if hasattr(first_child, 'url') and '/' in first_child.url:
                    url_parts = [p for p in first_child.url.strip('/').split('/') if p]
                    
                    # Если в пути есть central-docs, убираем его, чтобы найти чистую папку проекта
                    if "central-docs" in url_parts:
                        url_parts.remove("central-docs")
                        
                    if not url_parts:
                        continue
                        
                    project_folder = url_parts[0] # Теперь здесь точно "docgen"
                    
                    # 1. Ссылка на Swagger UI
                    api_page_rel_path = f"{project_folder}/api-docs.md"
                    if os.path.exists(os.path.join(docs_dir, api_page_rel_path)):
                        url_suffix = "api-docs/" if config['use_directory_urls'] else "api-docs.html"
                        full_api_url = f"{base_prefix}central-docs/{project_folder}/{url_suffix}"
                        full_api_url = '/' + full_api_url.lstrip('/').replace('//', '/')
                        
                        api_link = Link(title="🌐 Интерактивный Swagger API", url=full_api_url)
                        item.children.append(api_link)

                    # 2. Ссылка на isolated_text.txt
                    isolated_file_path = os.path.join(docs_dir, project_folder, "isolated_text.txt")
                    if os.path.exists(isolated_file_path):
                        full_file_url = f"{base_prefix}central-docs/{project_folder}/isolated_text.txt"
                        full_file_url = '/' + full_file_url.lstrip('/').replace('//', '/')
                        
                        download_link = Link(title="📥 Скачать документацию проекта", url=full_file_url)
                        item.children.append(download_link)
                        
    return nav
