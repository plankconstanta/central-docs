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
                first_child = item.children[0]
                
                # Извлекаем имя папки проекта из URL его первого документа
                if hasattr(first_child, 'url') and '/' in first_child.url:
                    project_folder = first_child.url.split('/')[0]
                    
                    # ----------------------------------------------------
                    # ЧАСТЬ 1: Поиск OpenAPI/Swagger спецификации
                    # ----------------------------------------------------
                    # Проверяем возможные расширения спецификации в папке проекта
                    spec_name = None
                    for ext in ['openapi.yaml', 'openapi.yml', 'openapi.json']:
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

                        # Вычисляем правильный URL в зависимости от настроек MkDocs
                        page_url = new_file.url if config['use_directory_urls'] else f"{project_folder}/api-docs.html"
                        
                        # Добавляем интерактивную страницу API в меню
                        api_link = Link(
                            title="🌐 Интерактивный Swagger API",
                            url=f"/{config['site_name'].lower().replace(' ', '-')}/{page_url}" if config.get('site_url') else f"/{page_url}"
                        )
                        # Если сайт деплоится на GitHub Pages без кастомного домена, 
                        # базовый путь может содержать имя репозитория. Для универсальности:
                        api_link = Link(title="🌐 Интерактивный Swagger API", url=f"./{page_url.split('/')[-1]}")
                        item.children.append(api_link)

                    # ----------------------------------------------------
                    # ЧАСТЬ 2: Ваша логика для isolated_text.txt
                    # ----------------------------------------------------
                    isolated_file_path = os.path.join(docs_dir, project_folder, "isolated_text.txt")
                    if os.path.exists(isolated_file_path):
                        # Ссылка на скачивание файла относительно корня сайта
                        file_url = f"{project_folder}/isolated_text.txt"
                        
                        download_link = Link(
                            title="📥 Скачать документацию проекта", 
                            url=file_url
                        )
                        item.children.append(download_link)
                        
    return nav
