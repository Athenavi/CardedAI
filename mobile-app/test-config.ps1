# FastBlog Mobile App 测试脚本
# 用于验证 Astro 前端构建和 Capacitor 配置

Write-Host "🧪 FastBlog Mobile App 配置测试" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# 检查 Astro 项目是否存在
if (-not (Test-Path "..\frontend-astro")) {
    Write-Host "❌ 错误: frontend-astro 目录不存在" -ForegroundColor Red
    exit 1
}

Write-Host "✅ frontend-astro 目录存在" -ForegroundColor Green

# 检查 Astro 项目是否已构建
if (-not (Test-Path "..\frontend-astro\dist")) {
    Write-Host "⚠️  警告: frontend-astro/dist 目录不存在，需要先构建" -ForegroundColor Yellow
    Write-Host "   运行: cd ..\frontend-astro; npm run build" -ForegroundColor Yellow
} else {
    Write-Host "✅ frontend-astro/dist 目录存在" -ForegroundColor Green
    
    # 检查 dist 目录是否有内容
    $distFiles = Get-ChildItem "..\frontend-astro\dist" -Recurse -File
    if ($distFiles.Count -eq 0) {
        Write-Host "⚠️  警告: dist 目录为空，需要重新构建" -ForegroundColor Yellow
    } else {
        Write-Host "✅ dist 目录包含 $($distFiles.Count) 个文件" -ForegroundColor Green
    }
}

Write-Host ""

# 检查 capacitor.config.json
if (-not (Test-Path "capacitor.config.json")) {
    Write-Host "❌ 错误: capacitor.config.json 不存在" -ForegroundColor Red
    exit 1
}

Write-Host "✅ capacitor.config.json 存在" -ForegroundColor Green

# 读取并验证配置
$configContent = Get-Content "capacitor.config.json" -Raw
if ($configContent -match '"webDir":\s*"../frontend-astro/dist"') {
    Write-Host "✅ webDir 配置正确: ../frontend-astro/dist" -ForegroundColor Green
} else {
    Write-Host "❌ 错误: webDir 配置不正确" -ForegroundColor Red
    Write-Host "   当前配置:" -ForegroundColor Yellow
    $configContent | Select-String "webDir"
    exit 1
}

Write-Host ""

# 检查 package.json
if (-not (Test-Path "package.json")) {
    Write-Host "❌ 错误: package.json 不存在" -ForegroundColor Red
    exit 1
}

Write-Host "✅ package.json 存在" -ForegroundColor Green

$packageContent = Get-Content "package.json" -Raw
if ($packageContent -match '"build:web":\s*"cd ../frontend-astro && npm run build"') {
    Write-Host "✅ build:web 脚本配置正确" -ForegroundColor Green
} else {
    Write-Host "❌ 错误: build:web 脚本配置不正确" -ForegroundColor Red
    Write-Host "   当前配置:" -ForegroundColor Yellow
    $packageContent | Select-String "build:web"
    exit 1
}

Write-Host ""
Write-Host "✨ 所有配置检查通过！" -ForegroundColor Green
Write-Host ""
Write-Host "接下来你可以：" -ForegroundColor Cyan
Write-Host "  1. 构建 Astro 前端: cd ..\frontend-astro; npm run build" -ForegroundColor White
Write-Host "  2. 同步到 Capacitor: npx cap sync" -ForegroundColor White
Write-Host "  3. 打开 Android Studio: npx cap open android" -ForegroundColor White
Write-Host ""
