import os
from mkdocs.structure.nav import Section, Link
from mkdocs.structure.files import File

# Список поддерживаемых расширений OpenAPI
SPEC_EXTENSIONS = ['openapi.json', 'openapi.yaml', 'openapi.yml', 'swagger.json']

def on_files(files, config):
    """
    ЭТАП 1: Находим спецификации и генерируем markdown-страницы ДО построения навигации.
    """
    docs_dir = config['docs_dir']
    
    # Сканируем папки первого уровня в docs/
    for folder in os.listdir(docs_dir):
        folder_path = os.path.join(docs_dir, folder)
        
        if os.path.isdir(folder_path) and folder != 'hooks':
            spec_name = None
            # Ищем файл спецификации в папке
            for ext in SPEC_EXTENSIONS:
                if os.path.exists(os.path.join(folder_path, ext)):
                    spec_name = ext
                    break
            
            if spec_name:
                spec_relative_path = f"{folder}/{spec_name}"
                api_page_rel_path = f"{folder}/api-docs.md"
                api_page_full_path = os.path.join(docs_dir, api_page_rel_path)
                
                # Создаем markdown-файл для Swagger UI
                with open(api_page_full_path, "w", encoding="utf-8") as f:
                    f.write(f"# Спецификация API\n\n")
                    f.write(f'<swagger-ui src="{spec_relative_path}"/>\n')
                
                # Создаем объект File и добавляем его в системный список MkDocs
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
    ЭТАП 2: Добавляем ссылки в меню для уже созданных страниц и файлов.
    """
    docs_dir = config['docs_dir']

    for item in nav.items:
        # Работаем только с секциями первого уровня (папками проектов)
        if isinstance(item, Section) and item.title != "Главная":
            if item.children:
                first_child = item.children[0]
                
                if hasattr(first_child, 'url') and '/' in first_child.url:
                    project_folder = first_child.url.split('/')[0]
                    
                    # 1. Проверяем, создали ли мы страницу api-docs.md на Этапе 1
                    api_page_rel_path = f"{project_folder}/api-docs.md"
                    if os.path.exists(os.path.join(docs_dir, api_page_rel_path)):
                        
                        # Формируем корректную ссылку в меню
                        url_suffix = "api-docs/" if config['use_directory_urls'] else "api-docs.html"
                        
                        api_link = Link(
                            title="🌐 Интерактивный Swagger API", 
                            url=f"./{url_suffix}"
                        )
                        # Вставляем ссылку Swagger в начало или в конец списка секции
                        item.children.append(api_link)

                    # 2. Логика для isolated_text.txt (остается вашей рабочей)
                    isolated_file_path = os.path.join(docs_dir, project_folder, "isolated_text.txt")
                    if os.path.exists(isolated_file_path):
                        download_link = Link(
                            title="📥 Скачать документацию проекта", 
                            url=f"./isolated_text.txt"
                        )
                        item.children.append(download_link)
                        
    return nav
