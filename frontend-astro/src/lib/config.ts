// 运行时配置加载器
// 优先从运行时配置文件加载，如果没有则使用默认配置

let runtimeApiConfig: { API_BASE_URL: string; API_PREFIX: string } | null = null;

// 异步加载运行时配置
export const loadRuntimeConfig = async (): Promise<{ API_BASE_URL: string; API_PREFIX: string }> => {
    if (runtimeApiConfig) {
        return runtimeApiConfig;
    }

    try {
        // 在浏览器环境中尝试加载运行时配置
        if (typeof window !== 'undefined') {
            // 优先尝试 JSON 格式的配置文件
            const configJsonUrl = `${window.location.origin}/config.json`;
            const jsonResponse = await fetch(configJsonUrl);
            if (jsonResponse.ok) {
                const configData = await jsonResponse.json();
                runtimeApiConfig = {
                    API_BASE_URL: configData.API_BASE_URL || configData.api_base_url || '',
                    API_PREFIX: configData.API_PREFIX || configData.api_prefix || '/api/v2'
                };
                console.log('✅ 已加载运行时 API 配置 (JSON):', runtimeApiConfig.API_BASE_URL);
                return runtimeApiConfig;
            }

            // 回退：使用 new Function 加载 JS 格式的配置（比 eval 更安全）
            const configUrl = `${window.location.origin}/config.js`;
            const response = await fetch(configUrl);
            if (response.ok) {
                const configText = await response.text();
                // 使用 new Function 代替 eval，限制作用域
                const configFn = new Function(`${configText}; return typeof runtimeConfig !== 'undefined' ? runtimeConfig : null;`);
                const configModule = configFn();
                if (configModule) {
                    runtimeApiConfig = {
                        API_BASE_URL: configModule.API_BASE_URL,
                        API_PREFIX: configModule.API_PREFIX || '/api/v2'
                    };
                    console.log('✅ 已加载运行时 API 配置 (JS):', runtimeApiConfig.API_BASE_URL);
                    return runtimeApiConfig;
                }
            }
        }
    } catch (error) {
        console.warn('⚠️ 未找到运行时配置，使用默认配置');
    }

    // 默认配置（构建时配置）
    runtimeApiConfig = {
        API_BASE_URL: '',
        API_PREFIX: '/api/v2'
    };

    return runtimeApiConfig;
};

// 同步获取配置（如果已加载）
export const getConfig = (): { API_BASE_URL: string; API_PREFIX: string } => {
    const config = runtimeApiConfig || {
        API_BASE_URL: '',
        API_PREFIX: '/api/v2'
    };
    return config;
};
