

from fastapi.responses import HTMLResponse

from src.unified_logger import default_logger as logger


def error(status_code, message):
    if status_code == 404:
        simple_error_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>页面未找到 - {status_code}</title>
                <meta charset="utf-8">
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        text-align: center;
                        padding: 50px;
                        background-color: #f5f5f5;
                    }}
                    .error-container {{
                        max-width: 600px;
                        margin: 0 auto;
                        background: white;
                        padding: 40px;
                        border-radius: 10px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    }}
                    h1 {{
                        color: #e74c3c;
                        font-size: 72px;
                        margin: 0;
                        line-height: 1;
                    }}
                    h2 {{
                        color: #2c3e50;
                        font-size: 24px;
                        margin-top: 10px;
                    }}
                    p {{
                        font-size: 18px;
                        color: #666;
                        margin: 20px 0;
                    }}
                    a {{
                        color: #3498db;
                        text-decoration: none;
                        font-weight: bold;
                        font-size: 16px;
                    }}
                    a:hover {{
                        text-decoration: underline;
                    }}
                    .home-link {{
                        display: inline-block;
                        margin-top: 20px;
                        padding: 10px 20px;
                        background-color: #3498db;
                        color: white;
                        border-radius: 5px;
                        text-decoration: none;
                    }}
                    .home-link:hover {{
                        background-color: #2980b9;
                        text-decoration: none;
                    }}
                </style>
            </head>
            <body>
                <div class="error-container">
                    <h1>404</h1>
                    <h2>页面未找到</h2>
                    <p>{message}</p>
                    <a href="/" class="home-link">返回首页</a>
                </div>
            </body>
            </html>
            """
    else:
        simple_error_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>错误 - {status_code}</title>
                <meta charset="utf-8">
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        text-align: center;
                        padding: 50px;
                        background-color: #f5f5f5;
                    }}
                    .error-container {{
                        max-width: 600px;
                        margin: 0 auto;
                        background: white;
                        padding: 40px;
                        border-radius: 10px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    }}
                    h1 {{
                        color: #e74c3c;
                        font-size: 72px;
                        margin: 0;
                        line-height: 1;
                    }}
                    h2 {{
                        color: #2c3e50;
                        font-size: 24px;
                        margin-top: 10px;
                    }}
                    p {{
                        font-size: 18px;
                        color: #666;
                        margin: 20px 0;
                    }}
                    a {{
                        color: #3498db;
                        text-decoration: none;
                        font-weight: bold;
                        font-size: 16px;
                    }}
                    a:hover {{
                        text-decoration: underline;
                    }}
                    .home-link {{
                        display: inline-block;
                        margin-top: 20px;
                        padding: 10px 20px;
                        background-color: #3498db;
                        color: white;
                        border-radius: 5px;
                        text-decoration: none;
                    }}
                    .home-link:hover {{
                        background-color: #2980b9;
                        text-decoration: none;
                    }}
                </style>
            </head>
            <body>
                <div class="error-container">
                    <h1>{status_code}</h1>
                    <h2>发生错误</h2>
                    <p>{message}</p>
                    <a href="/" class="home-link">返回首页</a>
                </div>
            </body>
            </html>
            """

    return HTMLResponse(content=simple_error_html, status_code=status_code)
