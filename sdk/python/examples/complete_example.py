"""
FastBlog Python SDK 使用示例 - 同步客户端
展示完整的SDK功能，包括文章CRUD、用户认证、媒体上传等
"""
from fastblog_sdk import FastBlogClient


def main():
    # 创建客户端
    with FastBlogClient("http://localhost:9421/api/v1") as client:

        # ==================== 1. 用户认证 ====================
        print("=" * 60)
        print("🔐 用户认证")
        print("=" * 60)

        # 登录
        print("\n📝 登录...")
        login_result = client.login("admin@example.com", "password")
        if login_result.get('success'):
            print(f"✅ 登录成功")
            token = login_result['data'].get('token')
            print(f"Token: {token[:20]}...")
        else:
            print(f"❌ 登录失败: {login_result.get('error')}")
            return

        # 获取当前用户信息
        print("\n👤 获取用户信息...")
        user_info = client.get_current_user()
        if user_info.get('success'):
            data = user_info['data']
            print(f"用户名: {data.get('username')}")
            print(f"邮箱: {data.get('email')}")
            print(f"角色: {data.get('role', 'user')}")

        # ==================== 2. 文章管理 ====================
        print("\n" + "=" * 60)
        print("📝 文章管理")
        print("=" * 60)

        # 获取文章列表
        print("\n📋 获取文章列表...")
        articles = client.get_articles(page=1, per_page=5)
        if articles.get('success'):
            data = articles['data']
            article_list = data.get('articles', [])
            pagination = data.get('pagination', {})

            print(f"找到 {pagination.get('total', 0)} 篇文章 (第 {pagination.get('current_page', 1)} 页)")
            for i, article in enumerate(article_list, 1):
                print(f"  {i}. {article.get('title')}")
                print(f"     ID: {article.get('id')}, 浏览: {article.get('views', 0)}")

        # 创建新文章
        print("\n✍️  创建新文章...")
        new_article = client.create_article({
            'title': 'Python SDK 测试文章',
            'content': '# Hello World\n\n这是通过 Python SDK 创建的文章。\n\n## 功能特性\n- 支持同步和异步\n- 完整的API覆盖\n- 类型提示',
            'excerpt': '这是一篇测试文章的摘要',
            'status': 0  # 草稿状态
        })

        if new_article.get('success'):
            article_id = new_article['data'].get('id')
            print(f"✅ 文章创建成功，ID: {article_id}")

            # 获取刚创建的文章
            print("\n📖 读取文章...")
            article_detail = client.get_article(article_id)
            if article_detail.get('success'):
                detail = article_detail['data']
                print(f"标题: {detail.get('title')}")
                print(f"状态: {'草稿' if detail.get('status') == 0 else '已发布'}")

            # 更新文章
            print("\n📝 更新文章...")
            update_result = client.update_article(article_id, {
                'title': 'Python SDK 测试文章 (已更新)',
                'status': 1  # 发布
            })
            if update_result.get('success'):
                print("✅ 文章更新并发布成功")

            # 删除文章
            print("\n🗑️  删除文章...")
            delete_result = client.delete_article(article_id)
            if delete_result.get('success'):
                print("✅ 文章删除成功")
        else:
            print(f"❌ 创建文章失败: {new_article.get('error')}")

        # ==================== 3. 分类管理 ====================
        print("\n" + "=" * 60)
        print("📂 分类管理")
        print("=" * 60)

        # 获取分类列表
        print("\n📋 获取分类列表...")
        categories = client.get_categories()
        if categories.get('success'):
            cat_list = categories['data'].get('categories', [])
            print(f"找到 {len(cat_list)} 个分类:")
            for cat in cat_list:
                print(f"  - {cat.get('name')} ({cat.get('slug')})")
                print(f"    文章数: {cat.get('article_count', 0)}")

        # 创建新分类
        print("\n➕ 创建新分类...")
        new_category = client.create_category(
            name="Python开发",
            slug="python-dev",
            description="Python相关的技术文章"
        )
        if new_category.get('success'):
            print(f"✅ 分类创建成功，ID: {new_category['data'].get('id')}")

        # ==================== 4. 媒体管理 ====================
        print("\n" + "=" * 60)
        print("📷 媒体管理")
        print("=" * 60)

        # 上传媒体文件
        print("\n⬆️  上传媒体文件...")
        try:
            upload_result = client.upload_media("test_image.jpg")
            if upload_result.get('success'):
                media_data = upload_result['data']
                print(f"✅ 媒体上传成功")
                print(f"  ID: {media_data.get('id')}")
                print(f"  文件名: {media_data.get('filename')}")
                print(f"  URL: {media_data.get('url')}")
                print(f"  大小: {media_data.get('size', 0) / 1024:.2f} KB")
        except FileNotFoundError:
            print("⚠️  测试文件不存在，跳过上传测试")
            print("   提示: 创建一个 test_image.jpg 文件来测试上传功能")
        except Exception as e:
            print(f"❌ 上传失败: {e}")

        # ==================== 5. 仪表板统计 ====================
        print("\n" + "=" * 60)
        print("📊 仪表板统计")
        print("=" * 60)

        stats = client.get_dashboard_stats()
        if stats.get('success'):
            data = stats['data']
            print(f"\n📈 统计数据:")
            print(f"  总文章数: {data.get('total_articles', 0)}")
            print(f"  已发布: {data.get('published_articles', 0)}")
            print(f"  草稿: {data.get('draft_articles', 0)}")
            print(f"  总用户数: {data.get('total_users', 0)}")
            print(f"  总浏览量: {data.get('total_views', 0)}")
            print(f"  总点赞数: {data.get('total_likes', 0)}")
            print(f"  总评论数: {data.get('total_comments', 0)}")

            # 显示热门文章
            popular = data.get('popular_articles', [])
            if popular:
                print(f"\n🔥 热门文章:")
                for i, article in enumerate(popular[:3], 1):
                    print(f"  {i}. {article.get('title')} ({article.get('views', 0)} 浏览)")

        # ==================== 6. SEO追踪 ====================
        print("\n" + "=" * 60)
        print("📈 SEO 追踪")
        print("=" * 60)

        # 获取SEO流量数据
        print("\n🚦 获取SEO流量数据...")
        seo_traffic = client.get_seo_traffic(days=7)
        if seo_traffic.get('success'):
            print("✅ SEO流量数据获取成功")
            traffic_data = seo_traffic['data']
            print(f"  搜索流量: {traffic_data.get('search_traffic', 0)}")
            print(f"  独立访客: {traffic_data.get('unique_visitors', 0)}")

        # 获取热门关键词
        print("\n🔑 获取热门关键词...")
        keywords = client.get_top_keywords(limit=10, days=7)
        if keywords.get('success'):
            keyword_list = keywords['data'].get('keywords', [])
            print(f"找到 {len(keyword_list)} 个关键词:")
            for kw in keyword_list[:5]:
                print(f"  - {kw.get('keyword')}: {kw.get('views', 0)} 次浏览")

        # ==================== 7. 报表 ====================
        print("\n" + "=" * 60)
        print("📋 报表")
        print("=" * 60)

        # 获取内容报表
        print("\n📊 获取内容报表...")
        content_report = client.get_content_report(days=30)
        if content_report.get('success'):
            print("✅ 内容报表获取成功")
            report_data = content_report['data']
            print(f"  报表周期: {report_data.get('period', '30天')}")
            print(f"  新增文章: {report_data.get('new_articles', 0)}")

        # 获取自定义报表
        print("\n📈 获取自定义报表...")
        custom_report = client.get_custom_report(
            metrics=['views', 'likes', 'comments'],
            days=30
        )
        if custom_report.get('success'):
            print("✅ 自定义报表获取成功")

        # ==================== 8. 登出 ====================
        print("\n" + "=" * 60)
        print("🚪 登出")
        print("=" * 60)

        logout_result = client.logout()
        if logout_result.get('success'):
            print("✅ 已登出")

        print("\n" + "=" * 60)
        print("✨ 所有示例执行完成!")
        print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback

        traceback.print_exc()
