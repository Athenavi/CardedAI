"""
XML 站点地图生成器
支持标准 Sitemap 协议、多语言 hreflang 标签和多种站点地图类型
"""
from datetime import datetime
from typing import List, Optional, Dict
from xml.dom.minidom import parseString
from xml.etree.ElementTree import Element, SubElement, tostring


class SitemapUrl:
    """站点地图 URL 条目"""

    def __init__(
            self,
            loc: str,
            lastmod: Optional[datetime] = None,
            changefreq: str = 'weekly',
            priority: float = 0.5,
            alternate_links: Optional[List[Dict[str, str]]] = None,
            images: Optional[List[Dict[str, str]]] = None,
            videos: Optional[List[Dict[str, str]]] = None,
    ):
        self.loc = loc
        self.lastmod = lastmod
        self.changefreq = changefreq
        self.priority = priority
        self.alternate_links = alternate_links or []
        self.images = images or []
        self.videos = videos or []


class SitemapGenerator:
    """XML 站点地图生成器"""

    def __init__(self):
        self.urls: List[SitemapUrl] = []

    def add_url(self, url: SitemapUrl):
        """添加 URL 条目"""
        self.urls.append(url)

    def generate_xml(self) -> str:
        """生成 XML 站点地图"""
        # 检查是否有图片或视频，如果有则添加相应的命名空间
        has_images = any(url.images for url in self.urls)
        has_videos = any(url.videos for url in self.urls)

        namespaces = {
            'xmlns': 'http://www.sitemaps.org/schemas/sitemap/0.9',
            'xmlns:xhtml': 'http://www.w3.org/1999/xhtml'  # 添加 xhtml 命名空间以支持 hreflang
        }
        if has_images:
            namespaces['xmlns:image'] = 'http://www.google.com/schemas/sitemap-image/1.1'
        if has_videos:
            namespaces['xmlns:video'] = 'http://www.google.com/schemas/sitemap-video/1.1'

        urlset = Element('urlset', namespaces)

        for url in self.urls:
            url_elem = SubElement(urlset, 'url')
            SubElement(url_elem, 'loc').text = url.loc

            if url.lastmod:
                SubElement(url_elem, 'lastmod').text = url.lastmod.strftime('%Y-%m-%dT%H:%M:%S+00:00')

            if url.changefreq:
                SubElement(url_elem, 'changefreq').text = url.changefreq

            if url.priority is not None:
                SubElement(url_elem, 'priority').text = f"{url.priority:.1f}"

            # 添加多语言 hreflang 链接
            if url.alternate_links:
                for alt in url.alternate_links:
                    link_elem = SubElement(url_elem, '{http://www.w3.org/1999/xhtml}link')
                    link_elem.set('rel', 'alternate')
                    link_elem.set('hreflang', alt['hreflang'])
                    link_elem.set('href', alt['href'])

            # 添加图片信息
            if url.images:
                for img in url.images:
                    image_elem = SubElement(url_elem, '{http://www.google.com/schemas/sitemap-image/1.1}image')
                    SubElement(image_elem, '{http://www.google.com/schemas/sitemap-image/1.1}loc').text = img.get('loc',
                                                                                                                  '')
                    if img.get('title'):
                        SubElement(image_elem, '{http://www.google.com/schemas/sitemap-image/1.1}title').text = img[
                            'title']
                    if img.get('caption'):
                        SubElement(image_elem, '{http://www.google.com/schemas/sitemap-image/1.1}caption').text = img[
                            'caption']
                    if img.get('geo_location'):
                        SubElement(image_elem, '{http://www.google.com/schemas/sitemap-image/1.1}geo_location').text = \
                            img['geo_location']
                    if img.get('license'):
                        SubElement(image_elem, '{http://www.google.com/schemas/sitemap-image/1.1}license').text = img[
                            'license']

            # 添加视频信息
            if url.videos:
                for video in url.videos:
                    video_elem = SubElement(url_elem, '{http://www.google.com/schemas/sitemap-video/1.1}video')
                    SubElement(video_elem,
                               '{http://www.google.com/schemas/sitemap-video/1.1}thumbnail_loc').text = video.get(
                        'thumbnail_loc', '')
                    SubElement(video_elem, '{http://www.google.com/schemas/sitemap-video/1.1}title').text = video.get(
                        'title', '')
                    SubElement(video_elem,
                               '{http://www.google.com/schemas/sitemap-video/1.1}description').text = video.get(
                        'description', '')
                    if video.get('content_loc'):
                        SubElement(video_elem, '{http://www.google.com/schemas/sitemap-video/1.1}content_loc').text = \
                            video['content_loc']
                    if video.get('player_loc'):
                        player_elem = SubElement(video_elem,
                                                 '{http://www.google.com/schemas/sitemap-video/1.1}player_loc')
                        player_elem.text = video['player_loc']
                        if video.get('allow_embed'):
                            player_elem.set('allow_embed', '1' if video['allow_embed'] else '0')
                    if video.get('duration'):
                        SubElement(video_elem, '{http://www.google.com/schemas/sitemap-video/1.1}duration').text = str(
                            video['duration'])
                    if video.get('expiration_date'):
                        SubElement(video_elem,
                                   '{http://www.google.com/schemas/sitemap-video/1.1}expiration_date').text = video[
                            'expiration_date']
                    if video.get('rating'):
                        SubElement(video_elem, '{http://www.google.com/schemas/sitemap-video/1.1}rating').text = str(
                            video['rating'])
                    if video.get('view_count'):
                        SubElement(video_elem,
                                   '{http://www.google.com/schemas/sitemap-video/1.1}view_count').text = str(
                            video['view_count'])
                    if video.get('publication_date'):
                        SubElement(video_elem,
                                   '{http://www.google.com/schemas/sitemap-video/1.1}publication_date').text = video[
                            'publication_date']
                    if video.get('tags'):
                        for tag in video['tags']:
                            SubElement(video_elem, '{http://www.google.com/schemas/sitemap-video/1.1}tag').text = tag
                    if video.get('category'):
                        SubElement(video_elem, '{http://www.google.com/schemas/sitemap-video/1.1}category').text = \
                            video['category']
                    if video.get('family_friendly'):
                        SubElement(video_elem,
                                   '{http://www.google.com/schemas/sitemap-video/1.1}family_friendly').text = 'yes' if \
                            video['family_friendly'] else 'no'

        return self._pretty_print(tostring(urlset, encoding='unicode'))

    @staticmethod
    def _pretty_print(xml_str: str) -> str:
        """美化 XML 输出"""
        dom = parseString(xml_str)
        return dom.toprettyxml(indent='  ', encoding=None)


class SitemapIndex:
    """站点地图索引（用于多个站点地图文件）"""

    def __init__(self):
        self.sitemaps: List[dict] = []

    def add_sitemap(self, loc: str, lastmod: Optional[datetime] = None):
        """添加站点地图引用"""
        self.sitemaps.append({
            'loc': loc,
            'lastmod': lastmod,
        })

    def generate_xml(self) -> str:
        """生成站点地图索引 XML"""
        sitemapindex = Element('sitemapindex', {
            'xmlns': 'http://www.sitemaps.org/schemas/sitemap/0.9'
        })

        for sm in self.sitemaps:
            sitemap_elem = SubElement(sitemapindex, 'sitemap')
            SubElement(sitemap_elem, 'loc').text = sm['loc']

            if sm['lastmod']:
                SubElement(sitemap_elem, 'lastmod').text = sm['lastmod'].strftime('%Y-%m-%dT%H:%M:%S+00:00')

        return self._pretty_print(tostring(sitemapindex, encoding='unicode'))

    @staticmethod
    def _pretty_print(xml_str: str) -> str:
        """美化 XML 输出"""
        dom = parseString(xml_str)
        return dom.toprettyxml(indent='  ', encoding=None)
