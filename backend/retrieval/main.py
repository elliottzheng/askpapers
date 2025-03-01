import os
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse
from retrieval.cool_paper import search_papers_by_keyword
import json
from werkzeug.utils import secure_filename
import logging
import tqdm


def setup_logging():
    """配置日志格式和级别"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger(__name__)


# 在文件开头添加
logger = setup_logging()


def is_valid_github_url(url):
    """验证是否为有效的 GitHub URL"""
    try:
        parsed = urlparse(url)
        return (
            parsed.netloc == "github.com"
            and len(parsed.path.strip("/").split("/")) >= 2
        )
    except:
        return False


def normalize_github_repo_url(repo_url):
    """标准化 GitHub 仓库 URL"""
    try:
        if not is_valid_github_url(repo_url):
            return None
        # 使用更严格的正则表达式匹配
        match = re.match(r"https://github\.com/([^/]+)/([^/]+)(?:/.*)?", repo_url)
        if match:
            return f"{match.group(1)}/{match.group(2)}"
        return None
    except Exception as e:
        logger.error(f"Error processing URL {repo_url}: {str(e)}")
        return None


def get_paper_title_from_arxiv(paper_url):
    response = requests.get(paper_url)
    if response.status_code == 200:
        html = response.text
        title = BeautifulSoup(html, "html.parser").find("meta", property="og:title")[
            "content"
        ]
        return title
    else:
        logger.error(f"Error: Received status code {response.status_code}")
        return None


def get_arxiv_url_from_readme(readme_url):
    """从 README.md 获取 ArXiv 论文链接"""
    try:
        md_content = requests.get(readme_url, timeout=10).text
        paper_urls = re.findall(r"https://arxiv.org/(?:abs|pdf)/\d+\.\d+", md_content)
        return paper_urls if paper_urls else None
    except Exception as e:
        logger.error(f"Error fetching README from {readme_url}: {str(e)}")
        return None


def get_arxiv_url_from_github(github_repo):
    """从 GitHub 仓库获取 ArXiv 论文链接"""
    if not github_repo:
        return None
    for branch in ["main", "master"]:  # 尝试两个主要分支
        github_readme_url = f"https://raw.githubusercontent.com/{github_repo}/refs/heads/{branch}/README.md"
        paper_urls = get_arxiv_url_from_readme(github_readme_url)
        if paper_urls:
            return paper_urls
    return None


class Paper:
    def __init__(
        self,
        title=None,
        arxiv_url=None,
        github_repo=None,
        pdf_url=None,
        entry_name=None,
    ):
        self.title = title
        self.arxiv_url = arxiv_url
        self.github_repo = github_repo
        self.pdf_url = pdf_url
        self.entry_name = entry_name

    def __repr__(self):
        return self.__str__()


def github_repos_to_arxiv(github_repos):
    # 处理并清理 GitHub 仓库 URL
    normalized_repos = []
    for repo_url in github_repos:
        normalized = normalize_github_repo_url(repo_url)
        if normalized:
            normalized_repos.append(normalized)

    # 去重处理
    github_repos = list(set(normalized_repos))
    logger.info(github_repos)
    arxiv_urls = []
    titles = []
    for repo_url in github_repos:
        paper_urls = get_arxiv_url_from_github(repo_url)
        if paper_urls is None:
            logger.info(f"No ArXiv paper found in {repo_url}")
            repo_name = repo_url.split("/")[-1]
            titles.append(repo_name)
        else:
            logger.info(f"Found ArXiv paper in {repo_url}: {paper_urls[0]}")
            arxiv_urls.append(paper_urls[0])
    return arxiv_urls, titles


def titles_to_arxiv(titles):
    arxiv_urls = []
    for title in titles:
        results = search_papers_by_keyword(title)
        if results:
            arxiv_url = results[0].arxiv_link
            if arxiv_url is None:
                logger.info(f"Failed to find ArXiv URL for {title}")
            else:
                print(f"Found ArXiv URL for {title}: {arxiv_url}")
                arxiv_urls.append(arxiv_url)
        else:
            logger.info(f"Failed to find ArXiv URL for {title}")
    return arxiv_urls


def get_short_filename(title):
    safe_name = secure_filename(title)
    if len(safe_name) > 50:
        safe_name = safe_name[:50]
    return safe_name

def download_pdf(pdf_url, pdf_path):
    response = requests.get(pdf_url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    block_size = 1024  # 1 Kibibyte
    
    # Initialize buffer to store the entire content
    pdf_content = bytearray()
    
    # Download with progress bar
    if total_size > 0:
        progress_bar = tqdm.tqdm(total=total_size, unit='iB', unit_scale=True)
        for data in response.iter_content(block_size):
            progress_bar.update(len(data))
            pdf_content.extend(data)
        progress_bar.close()
    else:
        pdf_content = response.content
    
    # Write the complete content to file after downloading
    with open(pdf_path, "wb") as f:
        f.write(pdf_content)

def dump_paper(paper, out_folder):
    os.makedirs(out_folder, exist_ok=True)
    file_name = paper.entry_name
    json_path = os.path.join(out_folder, f"info.json")
    if os.path.exists(json_path):
        logger.info(f"Skipping existing file: {json_path}")
        return False
    pdf_path = os.path.join(out_folder, f"{file_name}.pdf")
    pdf_response = requests.get(paper.pdf_url)
    if pdf_response.status_code != 200:
        logger.error(f"Failed to download PDF: {paper.pdf_url}")
        return False
    # Download PDF with progress bar
    print(f"Downloading PDF: {paper.pdf_url}")
    download_pdf(paper.pdf_url, pdf_path)
    

    with open(json_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(paper.__dict__, ensure_ascii=False, indent=4))
    return True


def dump_papers(papers, out_folder):
    os.makedirs(out_folder, exist_ok=True)
    dumped_papers = []
    for paper in papers:
        paper_entry_name = get_short_filename(paper.title)
        print(f"Dumping paper: {paper_entry_name}")
        paper.entry_name = paper_entry_name
        paper_out_folder = os.path.join(out_folder, paper_entry_name)
        success = dump_paper(paper, paper_out_folder)
        if success:
            dumped_papers.append(paper)
    return dumped_papers


def import_papers(paper_descs, paper_db_dir):
    paper_db_dir = os.path.abspath(paper_db_dir)
    github_repos = []
    arxiv_urls = []
    titles = []
    paper_names = []
    pdf_urls = []

    for paper_desc in paper_descs:
        if "github.com" in paper_desc:
            github_repos.append(paper_desc)
        elif "arxiv.org" in paper_desc:
            arxiv_urls.append(paper_desc)
        elif paper_desc.endswith(".pdf"):
            pdf_urls.append(paper_desc)
        else:
            paper_names.append(paper_desc)

    logger.info("Input Summary:")
    logger.info(f"Found {len(github_repos)} GitHub repos")
    logger.info(f"Found {len(arxiv_urls)} ArXiv URLs")
    logger.info(f"Found {len(pdf_urls)} PDF URLs")
    logger.info(f"Found {len(paper_names)} paper names")

    arxiv_urls2, titles2 = github_repos_to_arxiv(github_repos)
    arxiv_urls.extend(arxiv_urls2)
    titles.extend(titles2)

    arxiv_urls3 = titles_to_arxiv(titles + paper_names)
    arxiv_urls.extend(arxiv_urls3)
    papers = []
    for arxiv_url in arxiv_urls:
        if "/abs/" in arxiv_url:
            arxiv_pdf_url = arxiv_url.replace("/abs/", "/pdf/")
        elif "/pdf/" in arxiv_url:
            arxiv_pdf_url = arxiv_url
            arxiv_url = arxiv_url.replace("/pdf/", "/abs/")
        else:
            logger.info(f"Invalid ArXiv URL: {arxiv_url}")
            continue
        paper = Paper(
            title=get_paper_title_from_arxiv(arxiv_url),
            arxiv_url=arxiv_url,
            github_repo=None,
            pdf_url=arxiv_pdf_url,
        )
        papers.append(paper)
    assert len(pdf_urls) == 0, "PDF URLs not supported yet"

    # 去重
    papers = list(
        {paper.arxiv_url: paper for paper in papers if paper.title is not None}.values()
    )

    logger.info(f"Number of unique papers to dump: {len(papers)}")

    dumped_papers = dump_papers(papers, paper_db_dir)
    logger.info("=== Processing Complete ===")

    return [paper.__dict__ for paper in dumped_papers]


def load_paper_descs(in_file):
    paper_descs = open(in_file, "r", encoding="utf-8").read().split("\n")
    # filter # comments
    paper_descs = [x for x in paper_descs if not x.startswith("#")]
    return paper_descs


if __name__ == "__main__":
    logger.info("=== Starting Paper Processing ===")
    in_file = "../data/papers.txt"
    paper_descs = load_paper_descs(in_file)
    paper_db_dir = "../data/download_papers2"
    import_papers(paper_descs, paper_db_dir)
