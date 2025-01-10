import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def crawl_website(base_url, allowed_domains, output_dir="minecraft_knowledge/original_src"):
    """
    주어진 웹사이트와 하위 페이지들을 크롤링하여 HTML 파일로 저장합니다.
    base_url의 이름을 기반으로 output_dir에 하위 폴더를 생성합니다.
    allowed_domains에 지정된 도메인만 크롤링합니다.

    Args:
        base_url: 크롤링할 웹사이트의 기본 URL
        allowed_domains: 크롤링이 허용된 도메인 리스트 (예: ["minecraft.fandom.com/wiki"])
        output_dir: HTML 파일들을 저장할 상위 디렉토리 (기본값: minecraft_knowledge/original_src)
    """

    site_name = get_site_name(base_url)
    site_output_dir = os.path.join(output_dir, site_name)

    if not os.path.exists(site_output_dir):
        os.makedirs(site_output_dir)

    visited_urls = set()
    urls_to_visit = [base_url]

    while urls_to_visit:
        url = urls_to_visit.pop()
        if url in visited_urls:
            continue

        try:
            response = requests.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")
            page_name = get_page_name(url)
            save_path = os.path.join(site_output_dir, f"{page_name}.html")

            with open(save_path, "w", encoding="utf-8") as f:
                f.write(str(soup))

            print(f"Saved: {url} to {save_path}")
            visited_urls.add(url)

            # 하위 페이지 링크 추출 (도메인 제한 적용)
            for link in soup.find_all("a", href=True):
                absolute_url = urljoin(url, link["href"])
                if is_allowed_url(absolute_url, allowed_domains) and absolute_url not in visited_urls:
                    urls_to_visit.append(absolute_url)

        except requests.exceptions.RequestException as e:
            print(f"Error crawling {url}: {e}")

def is_allowed_url(url, allowed_domains):
    """
    주어진 URL이 허용된 도메인에 속하는지 확인합니다.

    Args:
        url: 확인할 URL
        allowed_domains: 허용된 도메인 리스트

    Returns:
        True if the URL is allowed, False otherwise
    """


    if allowed_domains in url:
        return True
    return False
    

def get_site_name(url):
    """
    URL에서 사이트 이름을 추출합니다. (디렉토리 이름으로 사용 가능하도록 변환)

    Args:
        url: 사이트 URL

    Returns:
        사이트 이름 (디렉토리 이름으로 사용 가능하도록 변환)
    """
    parsed_url = urlparse(url)
    netloc = parsed_url.netloc
    site_name = netloc.replace("www.", "")
    site_name = site_name.replace(".", "_")

    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in invalid_chars:
        site_name = site_name.replace(char, "_")

    return site_name

def get_page_name(url):
    """
    URL에서 페이지 이름을 추출합니다. (Windows 파일 이름 제한 대응)

    Args:
        url: 페이지 URL

    Returns:
        페이지 이름 (파일 이름으로 사용 가능하도록 변환)
    """
    parsed_url = urlparse(url)
    path = parsed_url.path
    if path.endswith("/"):
        path = path[:-1]
    page_name = path.replace("/", "_").strip()

    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in invalid_chars:
        page_name = page_name.replace(char, "_")

    if not page_name:
        page_name = "index"
    return page_name

if __name__ == "__main__":
    base_url = "https://minecraft.fandom.com/wiki/Minecraft_Wiki"
    allowed_domains = "https://minecraft.fandom.com/wiki"
    crawl_website(base_url, allowed_domains)