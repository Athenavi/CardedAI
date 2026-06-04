# FastBlog Capacitor 初始化脚本
# 用于快速设置 Capacitor 混合应用

Write-Host "🚀 FastBlog Capacitor 初始化" -ForegroundColor Cyan
Write-Host "=============================" -ForegroundColor Cyan
Write-Host ""

# 检查是否在正确的目录
if (-not (Test-Path "capacitor.config.json")) {
    Write-Host "❌ 错误: 请在 mobile-app 目录中运行此脚本" -ForegroundColor Red
    exit 1
}

Write-Host "📦 步骤 1: 安装依赖..." -ForegroundColor Yellow
npm install

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 依赖安装失败！" -ForegroundColor Red
    exit 1
}

Write-Host "✅ 依赖安装成功" -ForegroundColor Green
Write-Host ""

Write-Host "🔨 步骤 2: 构建 Astro Web 应用..." -ForegroundColor Yellow
cd ..\frontend-astro
npm run build

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Web 构建失败！" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Web 构建成功" -ForegroundColor Green
Write-Host ""

Write-Host "📱 步骤 3: 同步到 Capacitor..." -ForegroundColor Yellow
cd ..\mobile-app
npx cap sync

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 同步失败！" -ForegroundColor Red
    exit 1
}

Write-Host "✅ 同步成功" -ForegroundColor Green
Write-Host ""

Write-Host "✨ 初始化完成！" -ForegroundColor Green
Write-Host ""
Write-Host "接下来你可以：" -ForegroundColor Cyan
Write-Host "  • 运行 'npx cap open android' 在 Android Studio 中打开" -ForegroundColor White
Write-Host "  • 运行 'npx cap open ios' 在 Xcode 中打开（需要 macOS）" -ForegroundColor White
Write-Host "  • 运行 'npx cap run android' 直接在设备上运行" -ForegroundColor White
Write-Host ""
Write-Host "详细文档请查看: CAPACITOR_GUIDE.md" -ForegroundColor Yellow
Write-Host ""
