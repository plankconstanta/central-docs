from mkdocs.structure.nav import Section, Link
import os

def on_nav(nav, config, files):
    """
    Проверяет папки проектов первого уровня. Если внутри сгенерирован isolated_text.txt,
    автоматически добавляет прямую ссылку на его скачивание в меню проекта.
    """
    for item in nav.items:
        if isinstance(item, Section) and item.title != "Главная":
            if item.children:
                first_child = item.children[0]
                if hasattr(first_child, 'url') and '/' in first_child.url:
                    # Получаем имя папки проекта (например, "project-alpha")
                    project_folder = first_child.url.split('/')[0]

                    # Формируем прямую ссылку на скачивание файла
                    file_url = f"/{project_folder}/isolated_text.txt"

                    download_link = Link(
                        title="📥 Скачать документацию проекта", 
                        url=file_url
                    )
                    item.children.append(download_link)
    return nav
