"""
FastBlog Python SDK 使用示例 - 异步客户端
"""
import asyncio
from fastblog_sdk import AsyncFastBlogClient


async def main():
    # 创建异步客户端
    async with AsyncFastBlogClient("http://localhost:9421/api/v1") as client:

        # 1. 用户登录
        print("🔐 登录...")
        login_result = await client.login("admin@example.com", "password")
        print(f"✅ 登录成功: {login_result.get('message')}")

        # 2. 获取当前用户信息
        print("\n👤 获取用户信息...")
        user_info = await client.get_current_user()
        if user_info.get('success'):
            print(f"用户名: {user_info['data'].get('username')}")
            print(f"邮箱: {user_info['data'].get('email')}")

        # 3. 获取文章列表
        print("\n📝 获取文章列表...")
        articles = await client.get_articles(page=1, per_page=5)
        if articles.get('success'):
            data = articles['data']
            article_list = data.get('articles', [])
            print(f"找到 {len(article_list)} 篇文章:")
            for i, article in enumerate(article_list, 1):
                print(f"  {i}. {article.get('title')}")

        # 4. 创建新文章
        print("\n✍️  创建新文章...")
        new_article = await client.create_article({
            'title': '测试文章 - Python SDK',
            'content': '# Hello World\n\n这是通过 Python SDK 创建的文章。',
            'status': 0  # 草稿状态
        })
        if new_article.get('success'):
            article_id = new_article['data'].get('id')
            print(f"✅ 文章创建成功，ID: {article_id}")

            # 5. 更新文章
            print("\n📝 更新文章...")
            update_result = await client.update_article(article_id, {
                'title': '测试文章 - Python SDK (已更新)',
                'excerpt': '这是一篇测试文章的摘要'
            })
            if update_result.get('success'):
                print("✅ 文章更新成功")

        # 6. 获取分类列表
        print("\n📂 获取分类列表...")
        categories = await client.get_categories()
        if categories.get('success'):
            cat_list = categories['data'].get('categories', [])
            print(f"找到 {len(cat_list)} 个分类:")
            for cat in cat_list:
                print(f"  - {cat.get('name')}")

        # 7. 上传媒体文件
        print("\n📷 上传媒体文件...")
        try:
            upload_result = await client.upload_media("test_image.jpg")
            if upload_result.get('success'):
                media_id = upload_result['data'].get('id')
                print(f"✅ 媒体上传成功，ID: {media_id}")
        except FileNotFoundError:
            print("⚠️  测试文件不存在，跳过上传测试")
        except Exception as e:
            print(f"❌ 上传失败: {e}")

        # 8. 获取仪表板统计
        print("\n📊 获取仪表板统计...")
        stats = await client.get_dashboard_stats()
        if stats.get('success'):
            data = stats['data']
            print(f"总文章数: {data.get('total_articles', 0)}")
            print(f"总浏览量: {data.get('total_views', 0)}")
            print(f"总点赞数: {data.get('total_likes', 0)}")

        # 9. 获取SEO流量数据
        print("\n📈 获取SEO流量数据...")
        seo_data = await client.get_seo_traffic(days=7)
        if seo_data.get('success'):
            print("✅ SEO数据获取成功")

        # 10. 获取热门关键词
        print("\n🔑 获取热门关键词...")
        keywords = await client.get_top_keywords(limit=10, days=7)
        if keywords.get('success'):
            keyword_list = keywords['data'].get('keywords', [])
            print(f"找到 {len(keyword_list)} 个关键词:")
            for kw in keyword_list[:5]:
                print(f"  - {kw.get('keyword')}: {kw.get('views')} 次浏览")

        # 11. 获取内容报表
        print("\n📋 获取内容报表...")
        report = await client.get_content_report(days=30)
        if report.get('success'):
            print("✅ 报表获取成功")

        # 12. 登出
        print("\n🚪 登出...")
        await client.logout()
        print("✅ 已登出")


if __name__ == "__main__":
    # 运行异步主函数
    asyncio.run(main())
