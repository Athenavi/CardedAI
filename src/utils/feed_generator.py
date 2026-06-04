"""
RSS/Atom Feed 生成器
支持 RSS 2.0 和 Atom 1.0 格式
"""
from datetime import datetime
from typing import List, Optional
from xml.dom.minidom import parseString
from xml.etree.ElementTree import Element, SubElement, tostring


class FeedItem:
    """Feed 条目"""

    def __init__(
            self,
            title: str,
            link: str,
            description: str,
            pub_date: datetime,
            author: Optional[str] = None,
            categories: Optional[List[str]] = None,
            content: Optional[str] = None,
            image: Optional[str] = None,
    ):
        self.title = title
        self.link = link
        self.description = description
        self.pub_date = pub_date
        self.author = author
        self.categories = categories or []
        self.content = content
        self.image = image


class FeedGenerator:
    """Feed 生成器基类"""

    def __init__(
            self,
            title: str,
            link: str,
            description: str,
            language: str = 'zh-CN',
            feed_url: Optional[str] = None,
            icon_url: Optional[str] = None,
            copyright: Optional[str] = None,
    ):
        self.title = title
        self.link = link
        self.description = description
        self.language = language
        self.feed_url = feed_url
        self.icon_url = icon_url
        self.copyright = copyright
        self.items: List[FeedItem] = []

    def add_item(self, item: FeedItem):
        """添加 Feed 条目"""
        self.items.append(item)

    def generate_rss(self) -> str:
        """生成 RSS 2.0 格式"""
        raise NotImplementedError

    def generate_atom(self) -> str:
        """生成 Atom 1.0 格式"""
        raise NotImplementedError


class RSSFeedGenerator(FeedGenerator):
    """RSS 2.0 生成器"""

    def generate_rss(self) -> str:
        """生成 RSS 2.0 XML"""
        rss = Element('rss', {'version': '2.0'})
        channel = SubElement(rss, 'channel')

        # 频道信息
        SubElement(channel, 'title').text = self.title
        SubElement(channel, 'link').text = self.link
        SubElement(channel, 'description').text = self.description
        SubElement(channel, 'language').text = self.language

        if self.feed_url:
            SubElement(channel, 'atom:link', {
                'href': self.feed_url,
                'rel': 'self',
                'type': 'application/rss+xml'
            })

        if self.icon_url:
            image = SubElement(channel, 'image')
            SubElement(image, 'url').text = self.icon_url
            SubElement(image, 'title').text = self.title
            SubElement(image, 'link').text = self.link

        if self.copyright:
            SubElement(channel, 'copyright').text = self.copyright

        SubElement(channel, 'lastBuildDate').text = self._format_rfc822(datetime.now())
        SubElement(channel, 'generator').text = 'FastBlog RSS Generator'

        # 添加条目
        for item in self.items:
            item_elem = SubElement(channel, 'item')
            SubElement(item_elem, 'title').text = item.title
            SubElement(item_elem, 'link').text = item.link
            SubElement(item_elem, 'description').text = item.description
            SubElement(item_elem, 'pubDate').text = self._format_rfc822(item.pub_date)

            if item.author:
                SubElement(item_elem, 'author').text = item.author

            if item.content:
                SubElement(item_elem, 'content:encoded').text = item.content

            for category in item.categories:
                SubElement(item_elem, 'category').text = category

            if item.image:
                enclosure = SubElement(item_elem, 'enclosure', {
                    'url': item.image,
                    'type': 'image/jpeg',
                })

        return self._pretty_print(tostring(rss, encoding='unicode'))

    def generate_atom(self) -> str:
        """生成 Atom 1.0 XML"""
        feed = Element('feed', {
            'xmlns': 'http://www.w3.org/2005/Atom'
        })

        SubElement(feed, 'title').text = self.title
        SubElement(feed, 'subtitle').text = self.description

        link_self = SubElement(feed, 'link', {
            'href': self.feed_url or self.link,
            'rel': 'self'
        })

        link_alt = SubElement(feed, 'link', {
            'href': self.link,
            'rel': 'alternate'
        })

        SubElement(feed, 'updated').text = self._format_atom(datetime.now())
        SubElement(feed, 'id').text = self.link
        SubElement(feed, 'generator').text = 'FastBlog Atom Generator'

        if self.copyright:
            SubElement(feed, 'rights').text = self.copyright

        # 添加条目
        for item in self.items:
            entry = SubElement(feed, 'entry')
            SubElement(entry, 'title').text = item.title

            SubElement(entry, 'link', {
                'href': item.link,
                'rel': 'alternate'
            })

            SubElement(entry, 'id').text = item.link
            SubElement(entry, 'updated').text = self._format_atom(item.pub_date)
            SubElement(entry, 'published').text = self._format_atom(item.pub_date)

            if item.author:
                author = SubElement(entry, 'author')
                SubElement(author, 'name').text = item.author

            if item.content:
                SubElement(entry, 'content', {
                    'type': 'html'
                }).text = item.content
            else:
                SubElement(entry, 'summary').text = item.description

            for category in item.categories:
                SubElement(entry, 'category', {
                    'term': category
                })

        return self._pretty_print(tostring(feed, encoding='unicode'))

    @staticmethod
    def _format_rfc822(dt: datetime) -> str:
        """格式化 RFC 822 日期"""
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        months = [
            'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
            'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
        ]
        return f"{days[dt.weekday()]}, {dt.day:02d} {months[dt.month - 1]} {dt.year} {dt.hour:02d}:{dt.minute:02d}:{dt.second:02d} +0000"

    @staticmethod
    def _format_atom(dt: datetime) -> str:
        """格式化 Atom 日期"""
        return dt.strftime('%Y-%m-%dT%H:%M:%SZ')

    @staticmethod
    def _pretty_print(xml_str: str) -> str:
        """美化 XML 输出"""
        dom = parseString(xml_str)
        return dom.toprettyxml(indent='  ', encoding=None)
