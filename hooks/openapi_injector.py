import os
from mkdocs.structure.nav import Section, Link
from mkdocs.structure.files import File

def on_nav(nav, config, files):
    """
    Автоматически добавляет ссылку на интерактивный Swagger и на скачивание
    монолитного файла для каждого проекта первого уровня.
    """
    docs_dir = config['docs_dir']

    for item in nav.items:
        # Проверяем, что это секция (папка) и не главная страница
        if isinstance(item, Section) and item.title != "Главная":
            if item.children:
                first_child = item.children[0] # Исправлено: берем первый элемент списка детей
                
                # Извлекаем имя папки проекта из URL его первого документа
                if hasattr(first_child, 'url') and '/' in first_child.url:
                    project_folder = first_child.url.split('/')[0] # Исправлено: берем именно строку (имя папки)
                    
                    # ----------------------------------------------------
                    # ЧАСТЬ 1: Поиск OpenAPI/Swagger спецификации
                    # ----------------------------------------------------
                    # Добавлен openapi.json в список проверяемых файлов
                    spec_name = None
                    for ext in ['openapi.json', 'openapi.yaml', 'openapi.yml', 'swagger.json']:
                        if os.path.exists(os.path.join(docs_dir, project_folder, ext)):
                            spec_name = ext
                            break

                    if spec_name:
                        spec_relative_path = f"{project_folder}/{spec_name}"
                        api_page_rel_path = f"{project_folder}/api-docs.md"
                        api_page_full_path = os.path.join(docs_dir, api_page_rel_path)

                        # Создаем физический markdown-файл для Swagger-плагина
                        with open(api_page_full_path, "w", encoding="utf-8") as f:
                            f.write(f"# Спецификация API — {item.title}\n\n")
                            f.write(f'<swagger-ui src="{spec_relative_path}"/>\n')

                        # Регистрируем новый md-файл в жизненном цикле MkDocs
                        new_file = File(
                            path=api_page_rel_path,
                            src_dir=docs_dir,
                            dest_dir=config['site_dir'],
                            use_directory_urls=config['use_directory_urls']
                        )
                        files.append(new_file)

                        # Нам нужна относительная ссылка внутри папки проекта, 
                        # чтобы избежать проблем с базовым URL репозитория на GitHub Pages
                        api_link = Link(
                            title="🌐 Интерактивный Swagger API", 
                            url=f"./api-docs/" if config['use_directory_urls'] else f"./api-docs.html"
                        )
                        item.children.append(api_link)

                    # ----------------------------------------------------
                    # ЧАСТЬ 2: Ваша логика для isolated_text.txt
                    # ----------------------------------------------------
                    isolated_file_path = os.path.join(docs_dir, project_folder, "isolated_text.txt")
                    if os.path.exists(isolated_file_path):
                        # Ссылка на скачивание файла относительно папки проекта
                        download_link = Link(
                            title="📥 Скачать документацию проекта", 
                            url=f"./isolated_text.txt"
                        )
                        item.children.append(download_link)
                        
    return nav
