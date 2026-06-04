/**
 * 移动端手势组件 - React 岛屿
 */

'use client';

import {useEffect, useRef} from 'react';

const MobileGestures = () => {
    const touchStartX = useRef(0);
    const touchStartY = useRef(0);

    useEffect(() => {
        const handleTouchStart = (e: TouchEvent) => {
            touchStartX.current = e.touches[0].clientX;
            touchStartY.current = e.touches[0].clientY;
        };

        const handleTouchEnd = (e: TouchEvent) => {
            const deltaX = e.changedTouches[0].clientX - touchStartX.current;
            const deltaY = e.changedTouches[0].clientY - touchStartY.current;
            const absDeltaX = Math.abs(deltaX);
            const absDeltaY = Math.abs(deltaY);

            // 右滑返回（在屏幕左边缘）
            if (deltaX > 80 && absDeltaX > absDeltaY && touchStartX.current < 50) {
                window.history.back();
            }
        };

        window.addEventListener('touchstart', handleTouchStart);
        window.addEventListener('touchend', handleTouchEnd);

        return () => {
            window.removeEventListener('touchstart', handleTouchStart);
            window.removeEventListener('touchend', handleTouchEnd);
        };
    }, []);

    return null;
};

export default MobileGestures;
