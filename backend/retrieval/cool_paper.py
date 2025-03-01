from urllib.parse import urlencode
import requests
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class Author:
    name: str


@dataclass
class Paper:
    id: str
    title: str
    updated: datetime
    authors: List[Author]
    link: str
    summary: str
    arxiv_link: Optional[str]


def construct_url(keyword: str) -> str:
    query = urlencode({"query": keyword})
    return f"https://papers.cool/arxiv/search/feed?{query}"


def parse_feed(xml_content: str) -> List[Paper]:
    # 解析XML内容
    root = ET.fromstring(xml_content)

    # 定义Atom命名空间
    ns = {"atom": "http://www.w3.org/2005/Atom"}

    papers = []
    for entry in root.findall("atom:entry", ns):
        # 提取论文信息
        link = entry.find("atom:link", ns).get("href")
        if "arxiv" in link:
            arxiv_id = link.split("/")[-1]
            arxiv_link = f"https://arxiv.org/abs/{arxiv_id}"
        else:
            arxiv_link = None
        paper = Paper(
            id=entry.find("atom:id", ns).text,
            title=entry.find("atom:title", ns).text,
            updated=datetime.fromisoformat(
                entry.find("atom:updated", ns).text.replace("Z", "+00:00")
            ),
            authors=[
                Author(author.find("atom:name", ns).text)
                for author in entry.findall("atom:author", ns)
            ],
            link=link,
            arxiv_link=arxiv_link,
            summary=entry.find("atom:summary", ns).text,
        )
        papers.append(paper)

    return papers


def search_papers_by_keyword(keyword: str) -> List[Paper]:
    """搜索论文并返回解析后的结果"""
    url = construct_url(keyword)
    response = requests.get(url)
    if response.status_code == 200:
        papers = parse_feed(response.text)
        return papers
    else:
        raise Exception(f"搜索失败: {response.status_code}")


if __name__ == "__main__":
    # 搜索示例
    papers = search_papers_by_keyword(
        "HALLO2: LONG-DURATION AND HIGH-RESOLUTION AUDIO-DRIVEN PORTRAIT IMAGE ANIMATION"
    )
    for paper in papers[:1]:
        print(f"\nTitle: {paper.title}")
        print(f"Authors: {', '.join(a.name for a in paper.authors)}")
        print(f"Updated: {paper.updated}")
        print(f"Link: {paper.link}")
        print(f"Summary: {paper.summary[:200]}...")
