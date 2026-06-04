"""
FastBlog Python SDK 使用示例
"""

from fastblog_sdk import FastBlogClient


def main():
    # 创建客户端
    client = FastBlogClient("http://localhost:9421/api/v1")

    try:
        # 1. 登录
        print("=== 登录 ===")
        login_result = client.login("admin@example.com", "password")
        print(f"登录成功: {login_result.get('success')}")

        # 2. 获取当前用户信息
        print("\n=== 当前用户 ===")
        user = client.get_current_user()
        if user.get('success'):
            print(f"用户名: {user['data'].get('username')}")
            print(f"邮箱: {user['data'].get('email')}")

        # 3. 获取文章列表
        print("\n=== 文章列表 ===")
        articles = client.get_articles(page=1, per_page=5)
        if articles.get('success'):
            print(f"共 {articles['data']['total']} 篇文章")
            for article in articles['data']['items'][:3]:
                print(f"  - {article['title']}")

        # 4. 获取分类列表
        print("\n=== 分类列表 ===")
        categories = client.get_categories()
        if categories.get('success'):
            print(f"共 {len(categories['data'])} 个分类")
            for cat in categories['data'][:5]:
                print(f"  - {cat['name']}")

        # 5. 获取仪表板统计
        print("\n=== 仪表板统计 ===")
        stats = client.get_dashboard_stats()
        if stats.get('success'):
            data = stats['data']
            print(f"总文章数: {data.get('total_articles', 0)}")
            print(f"总浏览量: {data.get('total_views', 0)}")
            print(f"总用户数: {data.get('total_users', 0)}")

        # 6. SEO 流量数据
        print("\n=== SEO 流量 ===")
        seo_traffic = client.get_seo_traffic(days=30)
        if seo_traffic.get('success'):
            summary = seo_traffic['data']
            print(f"自然搜索访问量: {summary.get('total_organic_views', 0)}")

        # 7. 热门关键词
        print("\n=== 热门关键词 ===")
        keywords = client.get_top_keywords(limit=10, days=30)
        if keywords.get('success'):
            for kw in keywords['data']['keywords'][:5]:
                print(f"  - {kw['keyword']}: {kw['count']} 次")

        # 8. 内容报表
        print("\n=== 内容报表 ===")
        report = client.get_content_report(days=30)
        if report.get('success'):
            print(f"报表标题: {report['data'].get('title')}")

        # 9. 自定义报表
        print("\n=== 自定义报表 ===")
        custom_report = client.get_custom_report(
            metrics=['content', 'users'],
            days=30
        )
        if custom_report.get('success'):
            print(f"包含指标: {list(custom_report['data']['metrics'].keys())}")

        # 10. 登出
        print("\n=== 登出 ===")
        client.logout()
        print("已登出")

    except Exception as e:
        print(f"错误: {e}")
    finally:
        client.close()


if __name__ == "__main__":
    main()
