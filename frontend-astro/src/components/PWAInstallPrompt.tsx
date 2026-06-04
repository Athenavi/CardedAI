/**
 * PWA 安装提示 - React 岛屿
 */

'use client';

import {useEffect, useState} from 'react';
import {X} from 'lucide-react';

const PWAInstallPrompt = () => {
    const [showPrompt, setShowPrompt] = useState(false);
    const [deferredPrompt, setDeferredPrompt] = useState<any>(null);

    useEffect(() => {
        const handler = (e: Event) => {
            e.preventDefault();
            setDeferredPrompt(e);
            setShowPrompt(true);
        };

        window.addEventListener('beforeinstallprompt', handler);

        // 检查是否已安装
        if (window.matchMedia('(display-mode: standalone)').matches) {
            setShowPrompt(false);
        }

        return () => window.removeEventListener('beforeinstallprompt', handler);
    }, []);

    const handleInstall = async () => {
        if (!deferredPrompt) return;
        deferredPrompt.prompt();
        const {outcome} = await deferredPrompt.userChoice;
        if (outcome === 'accepted') {
            setShowPrompt(false);
        }
        setDeferredPrompt(null);
    };

    if (!showPrompt) return null;

    return (
        <div className="fixed bottom-20 md:bottom-4 left-4 right-4 md:left-auto md:right-4 md:w-80 z-50 p-4 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
            <div className="flex items-start justify-between">
                <div>
                    <h3 className="font-semibold text-gray-900 dark:text-white">安装 FastBlog</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">添加到主屏幕，获得更好的体验</p>
                </div>
                <button onClick={() => setShowPrompt(false)} className="p-1 text-gray-400 hover:text-gray-600">
                    <X className="w-4 h-4" />
                </button>
            </div>
            <button onClick={handleInstall}
                className="mt-3 w-full py-2 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium">
                安装
            </button>
        </div>
    );
};

export default PWAInstallPrompt;
