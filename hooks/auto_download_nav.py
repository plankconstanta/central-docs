from mkdocs.structure.nav import Section, Link

def on_nav(nav, config, files):
    """
    Автоматически находит все корневые разделы (проекты) в меню 
    и добавляет в их конец ссылку на скачивание текста этой секции.
    """
    for item in nav.items:
        # Проверяем, является ли элемент меню разделом (секцией) верхнего уровня
        if isinstance(item, Section) and item.title != "Главная":
            
            # Определяем имя папки на основе первого дочернего элемента
            if item.children:
                first_child = item.children[0]
                # Извлекаем префикс папки проекта (например, "project-alpha")
                if hasattr(first_child, 'url') and '/' in first_child.url:
                    project_folder = first_child.url.split('/')[0]
                    
                    # Генерируем автоматическую ссылку на print_page этого проекта
                    download_url = f"/{project_folder}/print_page/"
                    download_link = Link(
                        title="📥 Скачать текст проекта", 
                        url=download_url
                    )
                    
                    # Добавляем ссылку в конец выпадающего меню этого проекта
                    item.children.append(download_link)
                    
    return nav
