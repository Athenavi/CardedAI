# FastBlog Capacitor 混合应用开发指南

## 📱 什么是 Capacitor？

Capacitor 是一个跨平台原生运行时，可以将你的 **Astro PWA 应用**打包成真正的 iOS、Android、Web 和桌面应用。

**核心优势：**

- ✅ 复用现有 Astro 代码（100% 代码共享）
- ✅ 一键打包到多个平台
- ✅ 访问原生 API（相机、推送、地理位置等）
- ✅ 上架 App Store 和 Google Play
- ✅ 无需学习原生开发

---

## 🚀 快速开始（5分钟上手）

### 前置要求

1. **Node.js 16+** 已安装
2. **npm/yarn** 包管理器
3. **FastBlog Astro 项目** 已完成 PWA 配置

### 步骤 1: 初始化 Capacitor

```bash
# 进入 mobile-app 目录
cd mobile-app

# 初始化 npm 项目
npm init -y

# 安装 Capacitor 核心依赖
npm install @capacitor/core @capacitor/cli

# 初始化 Capacitor 配置
npx cap init FastBlog com.fastblog.app --web-dir=../frontend-astro/dist
```

**参数说明：**

- `FastBlog` - 应用名称
- `com.fastblog.app` - 应用唯一标识（Bundle ID）
- `--web-dir` - Web 资源目录（指向 Astro 构建输出）

### 步骤 2: 添加目标平台

```bash
# 安装 Android 平台支持
npm install @capacitor/android

# 安装 iOS 平台支持（需要 macOS）
npm install @capacitor/ios

# 添加平台
npx cap add android
npx cap add ios
```

### 步骤 3: 构建并同步 Web 资源

```bash
# 返回项目根目录
cd ..

# 构建 Astro 生产版本
cd frontend-astro
npm run build

# 返回 mobile-app 目录
cd ../mobile-app

# 同步 Web 资源到原生项目
npx cap sync
```

### 步骤 4: 运行应用

#### Android

```bash
# 在 Android Studio 中打开
npx cap open android

# 或直接在设备上运行
npx cap run android
```

#### iOS（需要 macOS）

```bash
# 在 Xcode 中打开
npx cap open ios

# 或直接在模拟器上运行
npx cap run ios
```

---

## 📋 完整工作流程

### 日常开发流程

```mermaid
graph LR
    A[修改 Next.js 代码] --> B[npm run build]
    B --> C[npx cap sync]
    C --> D[测试原生应用]
    D --> A
```

### 详细步骤

#### 1. 修改 Web 代码

```bash
# 在 frontend-astro 目录中开发
cd frontend-astro
# 编辑你的 Astro 组件、页面等
```

#### 2. 构建生产版本

```bash
npm run build
```

#### 3. 同步到原生项目

```bash
cd ../mobile-app
npx cap sync
```

**`sync` 命令会：**

- 复制 Web 资源到 `android/app/src/main/assets/public/`
- 复制 Web 资源到 `ios/App/App/public/`
- 更新原生插件配置
- 同步依赖

#### 4. 测试应用

```bash
# Android
npx cap run android

# iOS
npx cap run ios
```

---

## ⚙️ 配置文件详解

### capacitor.config.ts

创建 `mobile-app/capacitor.config.ts`：

```typescript
import {CapacitorConfig} from '@capacitor/cli';

const config: CapacitorConfig = {
    appId: 'com.fastblog.app',
    appName: 'FastBlog',
    webDir: '../frontend-astro/dist',
    server: {
        // 开发时使用本地服务器（热重载）
        // url: 'http://localhost:3000',
        // cleartext: true,

        // 生产时使用本地文件（默认）
        cleartext: false,
    },
    plugins: {
        SplashScreen: {
            launchShowDuration: 2000,
            backgroundColor: '#3b82f6',
            showSpinner: false,
        },
        StatusBar: {
            style: 'light',
            backgroundColor: '#3b82f6',
        },
    },
};

export default config;
```

### package.json

```json
{
  "name": "fastblog-mobile",
  "version": "1.0.0",
  "scripts": {
    "build": "cd ../frontend-astro && npm run build",
    "sync": "cap sync",
    "android": "cap open android",
    "ios": "cap open ios",
    "run:android": "cap run android",
    "run:ios": "cap run ios"
  },
  "dependencies": {
    "@capacitor/android": "^5.0.0",
    "@capacitor/core": "^5.0.0",
    "@capacitor/ios": "^5.0.0"
  },
  "devDependencies": {
    "@capacitor/cli": "^5.0.0"
  }
}
```

---

## 🔌 常用 Capacitor 插件

### 1. 推送通知（Push Notifications）

```bash
npm install @capacitor/push-notifications
```

**使用示例：**

```typescript
import {PushNotifications} from '@capacitor/push-notifications';

// 注册推送
await PushNotifications.requestPermissions();
await PushNotifications.register();

// 监听通知
PushNotifications.addListener('pushNotificationReceived', (notification) => {
    console.log('收到通知:', notification);
});
```

### 2. 相机（Camera）

```bash
npm install @capacitor/camera
```

**使用示例：**

```typescript
import {Camera, CameraResultType} from '@capacitor/camera';

const image = await Camera.getPhoto({
    quality: 90,
    allowEditing: false,
    resultType: CameraResultType.Uri,
});

console.log('图片路径:', image.webPath);
```

### 3. 文件系统（Filesystem）

```bash
npm install @capacitor/filesystem
```

**使用示例：**

```typescript
import {Filesystem, Directory} from '@capacitor/filesystem';

// 写入文件
await Filesystem.writeFile({
    path: 'article.txt',
    data: '文章内容',
    directory: Directory.Documents,
});
```

### 4. 地理位置（Geolocation）

```bash
npm install @capacitor/geolocation
```

**使用示例：**

```typescript
import {Geolocation} from '@capacitor/geolocation';

const coordinates = await Geolocation.getCurrentPosition();
console.log('纬度:', coordinates.coords.latitude);
console.log('经度:', coordinates.coords.longitude);
```

### 5. 分享（Share）

```bash
npm install @capacitor/share
```

**使用示例：**

```typescript
import {Share} from '@capacitor/share';

await Share.share({
    title: 'FastBlog 文章',
    text: '查看这篇精彩的文章',
    url: 'https://fastblog.com/article/123',
});
```

### 更多插件

访问 [Capacitor 插件市场](https://capacitorjs.com/docs/plugins) 查看所有可用插件。

---

## 🎨 优化原生体验

### 1. 启动画面（Splash Screen）

在 `capacitor.config.ts` 中配置：

```typescript
plugins: {
    SplashScreen: {
        launchShowDuration: 3000,
            backgroundColor
    :
        '#3b82f6',
            showSpinner
    :
        true,
            spinnerColor
    :
        '#ffffff',
            splashFullScreen
    :
        true,
            splashImmersive
    :
        true,
    }
,
}
```

### 2. 状态栏（Status Bar）

```typescript
import {StatusBar, Style} from '@capacitor/status-bar';

// 设置浅色状态栏
await StatusBar.setStyle({style: Style.Light});

// 设置背景色
await StatusBar.setBackgroundColor({color: '#3b82f6'});
```

### 3. 安全区域（Safe Area）

在 CSS 中添加：

```css
body {
    padding-top: env(safe-area-inset-top);
    padding-bottom: env(safe-area-inset-bottom);
    padding-left: env(safe-area-inset-left);
    padding-right: env(safe-area-inset-right);
}
```

---

## 📦 打包和发布

### Android 打包

#### 1. 生成签名密钥

```bash
keytool -genkey -v -keystore fastblog-release-key.jks -keyalg RSA -keysize 2048 -validity 10000 -alias fastblog
```

#### 2. 配置签名

在 `android/app/build.gradle` 中添加：

```gradle
android {
    signingConfigs {
        release {
            storeFile file('../fastblog-release-key.jks')
            storePassword 'your-password'
            keyAlias 'fastblog'
            keyPassword 'your-password'
        }
    }
    
    buildTypes {
        release {
            signingConfig signingConfigs.release
            minifyEnabled true
            proguardFiles getDefaultProguardFile('proguard-android.txt'), 'proguard-rules.pro'
        }
    }
}
```

#### 3. 构建 APK/AAB

```bash
# 在 Android Studio 中
# Build → Generate Signed Bundle / APK

# 或使用命令行
cd android
./gradlew bundleRelease  # 生成 AAB（推荐用于 Google Play）
./gradlew assembleRelease  # 生成 APK
```

输出位置：

- AAB: `android/app/build/outputs/bundle/release/app-release.aab`
- APK: `android/app/build/outputs/apk/release/app-release.apk`

### iOS 打包

#### 1. 在 Xcode 中配置

1. 打开 `ios/App/App.xcworkspace`
2. 选择项目 → Signing & Capabilities
3. 设置 Team 和 Bundle Identifier
4. 配置证书和描述文件

#### 2. 归档应用

1. Product → Archive
2. 等待归档完成
3. Distribute App → App Store Connect

#### 3. 上传到 App Store

使用 Xcode 或 Transporter 应用上传 IPA 文件。

---

## 🔧 调试技巧

### 1. Android 调试

```bash
# Chrome DevTools
chrome://inspect/#devices

# Logcat 日志
adb logcat | grep -i "capacitor\|console"
```

### 2. iOS 调试

```bash
# Safari Web Inspector
# Safari → 开发 → 你的设备 → FastBlog
```

### 3. 远程调试

在应用中启用调试模式：

```typescript
import {Capacitor} from '@capacitor/core';

if (Capacitor.isNativePlatform()) {
    console.log('运行在原生平台');
} else {
    console.log('运行在 Web 环境');
}
```

---

## 🐛 常见问题

### Q1: 如何区分 Web 和原生环境？

```typescript
import {Capacitor} from '@capacitor/core';

if (Capacitor.isNativePlatform()) {
    // 原生平台代码
    console.log('Running on native platform');
} else {
    // Web 平台代码
    console.log('Running on web');
}
```

### Q2: 如何处理平台特定代码？

```typescript
import {Platform} from '@capacitor/device';

const platform = await Platform.getInfo();

if (platform.platform === 'ios') {
    // iOS 特定逻辑
} else if (platform.platform === 'android') {
    // Android 特定逻辑
} else {
    // Web 逻辑
}
```

### Q3: 如何实现热重载？

**开发时使用本地服务器：**

```typescript
// capacitor.config.ts
server: {
    url: 'http://localhost:3000',
        cleartext
:
    true,
}
```

然后运行：

```bash
# Terminal 1: 启动 Astro 开发服务器
cd frontend-astro
npm run dev

# Terminal 2: 运行原生应用
cd mobile-app
npx cap run android
```

### Q4: 如何处理 CORS 问题？

在开发模式下，Capacitor 会自动处理 CORS。生产模式下使用本地文件，不存在 CORS 问题。

### Q5: 如何更新应用？

1. 修改 Astro 代码
2. `npm run build`
3. `npx cap sync`
4. 重新打包并发布到应用商店

**注意：** 纯 Web 内容更新可以通过服务器即时生效，但原生功能更新需要重新提交审核。

---

## 📊 性能优化

### 1. 减少初始加载时间

```typescript
// 预加载关键资源
const preloadResources = async () => {
    const resources = [
        '/api/v1/articles?limit=5',
        '/api/v1/categories',
    ];

    await Promise.all(
        resources.map(url => fetch(url))
    );
};
```

### 2. 懒加载非关键功能

```typescript
// 动态导入重型组件
const HeavyComponent = dynamic(() => import('@/components/HeavyComponent'), {
    loading: () => <p>Loading...</p>,
});
```

### 3. 优化图片

```typescript
// 使用 Capacitor Camera 拍摄的图片
import {Camera} from '@capacitor/camera';

const photo = await Camera.getPhoto({
    quality: 70, // 降低质量
    width: 800,  // 限制尺寸
});
```

---

## 🔒 安全最佳实践

### 1. 不要硬编码敏感信息

```typescript
// ❌ 错误做法
const API_KEY = 'sk-1234567890';

// ✅ 正确做法
const API_KEY = process.env.NEXT_PUBLIC_API_KEY;
```

### 2. 使用 HTTPS

确保所有 API 请求使用 HTTPS：

```typescript
const API_BASE_URL = 'https://api.fastblog.com';
```

### 3. 验证用户输入

```typescript
// 始终验证来自原生 API 的数据
const validatePhoto = (photo: Photo) => {
    if (!photo.webPath || !photo.format) {
        throw new Error('Invalid photo');
    }
};
```

---

## 📚 进阶主题

### 自定义原生插件

如果需要访问特殊原生功能，可以创建自定义插件：

```bash
npx @capacitor/plugin-generator create-plugin
```

### CI/CD 自动化

使用 GitHub Actions 自动构建：

```yaml
name: Build Mobile App
on: [ push ]
jobs:
  build-android:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v2
      - run: npm ci
      - run: npm run build
      - run: npx cap sync
      - run: cd android && ./gradlew assembleRelease
```

### 深度链接（Deep Linking）

配置应用可以从 URL 打开：

```typescript
// capacitor.config.ts
plugins: {
    App: {
        appUrlOpen: {
            androidScheme: 'https',
                iosScheme
        :
            'https',
        }
    ,
    }
,
}
```

---

## 🎯 总结

### Capacitor vs React Native

| 特性       | Capacitor | React Native |
|----------|-----------|--------------|
| **学习曲线** | 低（Web 技术） | 高（需学新框架）     |
| **代码复用** | 100%      | 80-90%       |
| **性能**   | 良好        | 优秀           |
| **原生体验** | 好         | 完美           |
| **开发速度** | 快         | 中等           |
| **维护成本** | 低         | 高            |

### 何时使用 Capacitor？

✅ **推荐使用：**

- 已有成熟的 Web/PWA 应用
- 需要快速上架应用商店
- 团队熟悉 Web 技术
- 应用以内容展示为主

❌ **不推荐：**

- 需要极致性能（如游戏）
- 重度依赖复杂原生交互
- 需要完全自定义的 UI

---

## 🔗 相关资源

- [Capacitor 官方文档](https://capacitorjs.com/docs)
- [Capacitor 插件市场](https://capacitorjs.com/docs/plugins)
- [Android 开发者文档](https://developer.android.com/docs)
- [iOS 开发者文档](https://developer.apple.com/documentation)
- [FastBlog PWA 迁移报告](../PWA_MIGRATION_COMPLETE.md)

---

**FastBlog + Capacitor** = 一套代码，多端运行 🚀

*最后更新：2026-05-15*
