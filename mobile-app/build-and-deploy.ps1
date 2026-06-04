# FastBlog Mobile App - 构建和部署脚本
# 修复 styles.xml 问题并构建应用

Write-Host "🔧 FastBlog Mobile App 构建脚本" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# 步骤 1: 构建 Astro 前端
Write-Host "📦 步骤 1: 构建 Astro 前端..." -ForegroundColor Yellow
cd ..\frontend-astro
npm run build

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Astro 构建失败！" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Astro 构建成功" -ForegroundColor Green
Write-Host ""

# 步骤 2: 同步到 Capacitor
Write-Host "🔄 步骤 2: 同步到 Capacitor..." -ForegroundColor Yellow
cd ..\mobile-app
npx cap sync

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Capacitor 同步失败！" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Capacitor 同步成功" -ForegroundColor Green
Write-Host ""

# 步骤 3: 修复 styles.xml
Write-Host "🔧 步骤 3: 修复 styles.xml..." -ForegroundColor Yellow
$stylesXml = @"
<?xml version="1.0" encoding="utf-8"?>
<resources>

    <!-- Base application theme. -->
    <style name="AppTheme" parent="Theme.AppCompat.Light.DarkActionBar">
        <!-- Customize your theme here. -->
        <item name="colorPrimary">@@color/colorPrimary</item>
        <item name="colorPrimaryDark">@@color/colorPrimaryDark</item>
        <item name="colorAccent">@@color/colorAccent</item>
    </style>

    <style name="AppTheme.NoActionBar" parent="Theme.AppCompat.DayNight.NoActionBar">
        <item name="windowActionBar">false</item>
        <item name="windowNoTitle">true</item>
        <item name="android:background">@@null</item>
    </style>

    <style name="AppTheme.NoActionBarLaunch" parent="Theme.SplashScreen">
        <item name="android:background">@@drawable/splash</item>
    </style>
</resources>
"@

$stylesXml | Out-File -FilePath "android\app\src\main\res\values\styles.xml" -Encoding utf8

Write-Host "✅ styles.xml 已修复" -ForegroundColor Green
Write-Host ""

# 步骤 4: 清理并构建 Android
Write-Host "🏗️  步骤 4: 构建 Android 应用..." -ForegroundColor Yellow
cd android
.\gradlew clean
.\gradlew assembleDebug

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Android 构建失败！" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Android 构建成功" -ForegroundColor Green
Write-Host ""

# 步骤 5: 安装到设备
Write-Host "📱 步骤 5: 安装应用到模拟器..." -ForegroundColor Yellow
adb install -r app\build\outputs\apk\debug\app-debug.apk

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 安装失败！" -ForegroundColor Red
    exit 1
}

Write-Host "✅ 安装成功" -ForegroundColor Green
Write-Host ""

# 步骤 6: 启动应用
Write-Host "🚀 步骤 6: 启动应用..." -ForegroundColor Yellow
adb shell am start -n com.fastblog.app/.MainActivity

Write-Host ""
Write-Host "✨ 完成！应用已在模拟器中启动" -ForegroundColor Green
Write-Host ""
Write-Host "提示：" -ForegroundColor Cyan
Write-Host "  • 查看日志: adb logcat | Select-String -Pattern 'capacitor|ERROR'" -ForegroundColor White
Write-Host "  • 重新构建: .\build-and-deploy.ps1" -ForegroundColor White
Write-Host ""
