from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
from markdownify import markdownify as md
import csv
import os
import time
import random


# Функция для преобразования HTML в Markdown
def html_to_markdown(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    for img in soup.find_all("img"):
        if "base64" in img["src"]:
            img.decompose()
    for i in range(1, 7):
        for header in soup.find_all(f"h{i}"):
            header.replace_with(f"{'#' * i} {header.get_text()}\n")
    return md(str(soup))


# Функция для создания уникального имени файла
def get_unique_file_path(file_path, random_id):
    base, extension = os.path.splitext(file_path)
    base = base.replace(" ", "_")
    file_path = f"{base}_{random_id}{extension}"
    return file_path

def get_filename_from_path(file_path):
    return os.path.basename(file_path)


# Функция для поиска последнего родителя элемента
def find_parent_title(link):
    try:
        # Найти текущий <li>, являющийся родителем ссылки
        current_li = link.find_element(By.XPATH, "./parent::li[contains(@class, 'menu__list-item')]")
        #print("Current <li> found:", current_li.get_attribute('outerHTML'))

        # Найти родительский <ul> для текущего <li>
        parent_ul = current_li.find_element(By.XPATH, "./parent::ul")
        #print("Parent <ul> found:", parent_ul.get_attribute('outerHTML'))

        # Найти родительский <li> для родительского <ul>
        parent_li = parent_ul.find_element(By.XPATH, "./parent::li[contains(@class, 'menu__list-item')]")
        #print("Parent <li> found:", parent_li.get_attribute('outerHTML'))

        # Найти <div> внутри родительского <li>
        parent_div = parent_li.find_element(By.XPATH, "./div[contains(@class, 'menu__list-item-collapsible')]")
        #print("Parent <div> found:", parent_div.get_attribute('outerHTML'))

        # Найти <a> внутри <div> с классом 'menu__link'
        parent_title_element = parent_div.find_element(By.XPATH, "./a[contains(@class, 'menu__link')]")
        #print("Parent title element <a>: found", parent_title_element.get_attribute('outerHTML'))

        return parent_title_element.text.strip() if parent_title_element else ""
    except NoSuchElementException as e:
        #print("Element not found at some step:", e)
        return ""



# Основная логика скрипта
def main():
    base_url = "https://www.rustore.ru"
    result_folder = "result\\developers"
    if not os.path.exists(result_folder):
        os.makedirs(result_folder)
    csv_file = os.path.join(result_folder, "files.csv")
    csv_data = []
    processed_urls = set()

    driver = webdriver.Chrome()
    try:
        driver.get("https://www.rustore.ru/help/developers/")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "nav[aria-label='Docs sidebar']")))

        while True:
            links = driver.find_elements(By.CSS_SELECTOR, "li.menu__list-item a.menu__link")
            link_processed = False

            for link in links:
                url = link.get_attribute("href")
                title = link.text.strip().replace("/", " ").replace("\\", " ").replace(":", " ").replace("*",
                                                                                                         " ").replace(
                    "?", " ").replace("\"", " ").replace("<", " ").replace(">", " ").replace("|", " ")

                if not title:
                    title = link.get_attribute("innerText").strip().replace("/", " ").replace("\\", " ").replace(":",
                                                                                                                 " ").replace(
                        "*", " ").replace("?", " ").replace("\"", " ").replace("<", " ").replace(">", " ").replace("|",
                                                                                                                   " ")

                if url not in processed_urls:
                    processed_urls.add(url)
                    parent_title = find_parent_title(link)

                    try:
                        driver.execute_script("arguments[0].click();", link)
                        WebDriverWait(driver, 2).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "div.markdown")))
                        article_div = driver.find_element(By.CSS_SELECTOR, "div.markdown")
                        markdown_content = html_to_markdown(article_div.get_attribute("outerHTML"))

                        if not title:  # Проверяем, что название не пустое после повторной попытки
                            print(f"! Неудача. Пустое название | {url}")
                            csv_data.append([title, url, parent_title.replace(" ", "_"), 0, '', ''])
                            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                                writer = csv.writer(f)
                                writer.writerow(
                                    ["Заголовок статьи", "URL", "Заголовок последней зависимости", "isParsed", "ID", "Заголовок файла"])
                                writer.writerows(csv_data)
                            continue

                        md_file_path = os.path.join(result_folder, f"{title}.md")
                        unique_id = random.randint(1000, 9999)
                        md_file_path = get_unique_file_path(md_file_path, unique_id)

                        with open(md_file_path, 'w', encoding='utf-8') as f:
                            f.write(markdown_content)

                        csv_data.append([title, url, parent_title.replace(" ", "_"), 1, unique_id, get_filename_from_path(md_file_path)])
                        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            writer.writerow(["Заголовок статьи", "URL", "Заголовок последней зависимости", "isParsed", "ID", "Заголовок файла"])
                            writer.writerows(csv_data)

                        print(f"+ Успех! '{md_file_path}' | '{url}'")
                    except TimeoutException:
                        print(f"! Неудача. Нет статьи на странице {url}")
                        csv_data.append([title, url, parent_title.replace(" ", "_"), 0, '', ''])
                        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            writer.writerow(["Заголовок статьи", "URL", "Заголовок последней зависимости", "isParsed", "ID", "Заголовок файла"])
                            writer.writerows(csv_data)
                    time.sleep(1)  # Ждем перед переходом к следующей странице

    finally:
        driver.quit()
        print("Скрипт выполнен успешно")


if __name__ == "__main__":
    main()
