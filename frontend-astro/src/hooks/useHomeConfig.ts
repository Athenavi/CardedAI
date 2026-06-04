import {useEffect, useState} from 'react';
import {apiClient} from '@/lib/api/base-client';

export interface HomeConfig {
  hero?: {
    title?: string;
    subtitle?: string;
    backgroundImage?: string;
    ctaText?: string;
    ctaLink?: string;
    ctaTarget?: string;
  };
  sections?: {
    featuredTitle?: string;
    mainTitle?: string;
    categoriesTitle?: string;
  };
  newsletter?: {
    title?: string;
    subtitle?: string;
    buttonText?: string;
  };
  messages?: {
    noSummary?: string;
  };
}

const DEFAULT_CONFIG: Required<{
  hero: NonNullable<HomeConfig['hero']>;
  sections: NonNullable<HomeConfig['sections']>;
  newsletter: NonNullable<HomeConfig['newsletter']>;
  messages: NonNullable<HomeConfig['messages']>;
}> = {
  hero: {
    title: '用文字连接每一个想法',
    subtitle: 'FastBlog 是一个现代化的内容创作平台，为创作者提供极致的写作体验，让灵感自由流动。',
    backgroundImage: '',
    ctaText: '开始阅读',
    ctaLink: '/articles',
    ctaTarget: '_self',
  },
  sections: {
    featuredTitle: '精选推荐',
    mainTitle: '最新发布',
    categoriesTitle: '探索分类',
  },
  newsletter: {
    title: '准备好开始创作了吗？',
    subtitle: '加入 FastBlog，与数千名创作者一起分享你的知识和想法。',
    buttonText: '免费注册',
  },
  messages: {
    noSummary: '...',
  },
};

export function useHomeConfig() {
  const [config, setConfig] = useState<HomeConfig>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const res = await apiClient.get('/home/config');
        if (res.success && res.data) {
          setConfig(res.data);
        }
      } catch {
        // 使用默认配置
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const hero = {...DEFAULT_CONFIG.hero, ...config.hero};
  const sections = {...DEFAULT_CONFIG.sections, ...config.sections};
  const newsletter = {...DEFAULT_CONFIG.newsletter, ...config.newsletter};
  const messages = {...DEFAULT_CONFIG.messages, ...config.messages};

  return {hero, sections, newsletter, messages, loading, raw: config};
}
