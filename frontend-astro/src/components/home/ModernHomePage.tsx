'use client';

import React, {useCallback, useEffect, useRef, useState} from 'react';
import {AnimatePresence, motion, useInView, useScroll, useTransform} from 'framer-motion';
import {apiClient} from '@/lib/api/base-client';
import {getFullMediaUrl} from '@/lib/utils';
import {useHomeConfig} from '@/hooks/useHomeConfig';
import {
  ArrowRight,
  ArrowUpRight,
  BookOpen,
  Calendar,
  ChevronLeft,
  ChevronRight,
  Clock,
  Eye,
  Flame,
  Hash,
  Heart,
  Sparkles,
  Star,
  TrendingUp,
  Zap,
} from 'lucide-react';

/* ═══════════════════════════════════════
   Types
   ═══════════════════════════════════════ */
interface Article {
  id: number;
  title: string;
  slug: string;
  excerpt?: string;
  summary?: string;
  cover_image?: string;
  created_at?: string;
  views?: number;
  likes?: number;
  tags?: string[];
  category?: string;
  author?: { username?: string; avatar?: string };
}

interface Category {
  id: number;
  name: string;
  slug: string;
  count?: number;
  image?: string;
  description?: string;
}

interface Stats {
  total_articles?: number;
  total_users?: number;
  total_views?: number;
  total_comments?: number;
}

/* ═══════════════════════════════════════
   Animation Variants
   ═══════════════════════════════════════ */
const fadeUp = {
  hidden: {opacity: 0, y: 40},
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.7,
      ease: [0.22, 1, 0.36, 1] as [number, number, number, number] as [number, number, number, number]
    }
  },
};

const fadeIn = {
  hidden: {opacity: 0},
  visible: {opacity: 1, transition: {duration: 0.6}},
};

const staggerContainer = {
  hidden: {},
  visible: {transition: {staggerChildren: 0.1, delayChildren: 0.1}},
};

const scaleIn = {
  hidden: {opacity: 0, scale: 0.9},
  visible: {
    opacity: 1,
    scale: 1,
    transition: {duration: 0.5, ease: [0.22, 1, 0.36, 1] as [number, number, number, number]}
  },
};

const slideFromLeft = {
  hidden: {opacity: 0, x: -60},
  visible: {
    opacity: 1,
    x: 0,
    transition: {duration: 0.8, ease: [0.22, 1, 0.36, 1] as [number, number, number, number]}
  },
};

const slideFromRight = {
  hidden: {opacity: 0, x: 60},
  visible: {
    opacity: 1,
    x: 0,
    transition: {duration: 0.8, ease: [0.22, 1, 0.36, 1] as [number, number, number, number]}
  },
};

/* ═══════════════════════════════════════
   Reusable: Section Wrapper with scroll animation
   ═══════════════════════════════════════ */
const Section: React.FC<{
  children: React.ReactNode;
  className?: string;
  id?: string;
}> = ({children, className = '', id}) => {
  const ref = useRef(null);
  const isInView = useInView(ref, {once: true, margin: '-80px'});
  return (
    <motion.section
      ref={ref}
      id={id}
      initial="hidden"
      animate={isInView ? 'visible' : 'hidden'}
      variants={staggerContainer}
      className={className}
    >
      {children}
    </motion.section>
  );
};

/* ═══════════════════════════════════════
   Reusable: Animated Counter
   ═══════════════════════════════════════ */
const AnimatedNumber: React.FC<{ value: number; suffix?: string }> = ({value, suffix = ''}) => {
  const [display, setDisplay] = useState(0);
  const ref = useRef<HTMLSpanElement>(null);
  const isInView = useInView(ref, {once: true});

  useEffect(() => {
    if (!isInView || value === 0) return;
    const duration = 1800;
    const startTime = Date.now();
    const tick = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(Math.floor(eased * value));
      if (progress < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }, [isInView, value]);

  return <span ref={ref}>{display.toLocaleString()}{suffix}</span>;
};

/* ═══════════════════════════════════════
   Reusable: Horizontal Scroll Container
   ═══════════════════════════════════════ */
const HorizontalScroll: React.FC<{
  children: React.ReactNode;
  className?: string;
}> = ({children, className = ''}) => {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(true);

  const checkScroll = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    setCanScrollLeft(el.scrollLeft > 10);
    setCanScrollRight(el.scrollLeft < el.scrollWidth - el.clientWidth - 10);
  }, []);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    el.addEventListener('scroll', checkScroll, {passive: true});
    checkScroll();
    return () => el.removeEventListener('scroll', checkScroll);
  }, [checkScroll]);

  const scroll = (direction: 'left' | 'right') => {
    const el = scrollRef.current;
    if (!el) return;
    const amount = el.clientWidth * 0.75;
    el.scrollBy({left: direction === 'left' ? -amount : amount, behavior: 'smooth'});
  };

  return (
    <div className="relative group/scroll">
      {canScrollLeft && (
        <button
          onClick={() => scroll('left')}
          className="absolute left-0 top-1/2 -translate-y-1/2 z-20 w-12 h-12 flex items-center justify-center
            bg-white/90 dark:bg-gray-900/90 backdrop-blur-sm rounded-full shadow-xl border border-gray-200/50 dark:border-gray-700/50
            opacity-0 group-hover/scroll:opacity-100 transition-all duration-300 hover:scale-110 -translate-x-2"
          aria-label="向左滚动"
        >
          <ChevronLeft className="w-5 h-5 text-gray-700 dark:text-gray-300"/>
        </button>
      )}
      {canScrollRight && (
        <button
          onClick={() => scroll('right')}
          className="absolute right-0 top-1/2 -translate-y-1/2 z-20 w-12 h-12 flex items-center justify-center
            bg-white/90 dark:bg-gray-900/90 backdrop-blur-sm rounded-full shadow-xl border border-gray-200/50 dark:border-gray-700/50
            opacity-0 group-hover/scroll:opacity-100 transition-all duration-300 hover:scale-110 translate-x-2"
          aria-label="向右滚动"
        >
          <ChevronRight className="w-5 h-5 text-gray-700 dark:text-gray-300"/>
        </button>
      )}
      <div
        ref={scrollRef}
        className={`flex gap-6 overflow-x-auto scroll-smooth snap-x snap-mandatory pb-4
          scrollbar-hide [${className}]`}
        style={{scrollbarWidth: 'none', msOverflowStyle: 'none'}}
      >
        {children}
      </div>
    </div>
  );
};

/* ═══════════════════════════════════════
   Loading Skeleton
   ═══════════════════════════════════════ */
const LoadingScreen = () => (
  <div className="min-h-screen bg-white dark:bg-gray-950">
    {/* Hero skeleton */}
    <div className="relative h-[85vh] min-h-[600px] bg-gray-100 dark:bg-gray-900 animate-pulse">
      <div className="absolute inset-0 flex items-center">
        <div className="max-w-7xl mx-auto px-6 w-full">
          <div className="max-w-2xl space-y-6">
            <div className="h-4 w-32 bg-gray-200 dark:bg-gray-800 rounded-full"/>
            <div className="h-16 w-96 bg-gray-200 dark:bg-gray-800 rounded-xl"/>
            <div className="h-6 w-80 bg-gray-200 dark:bg-gray-800 rounded-lg"/>
            <div className="flex gap-4 mt-8">
              <div className="h-14 w-40 bg-gray-200 dark:bg-gray-800 rounded-xl"/>
              <div className="h-14 w-36 bg-gray-200 dark:bg-gray-800 rounded-xl"/>
            </div>
          </div>
        </div>
      </div>
    </div>
    {/* Content skeletons */}
    <div className="max-w-7xl mx-auto px-6 py-20 space-y-16">
      {[1, 2].map(section => (
        <div key={section}>
          <div className="h-8 w-48 bg-gray-100 dark:bg-gray-900 rounded-lg mb-8"/>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map(i => (
              <div key={i} className="rounded-2xl overflow-hidden border border-gray-100 dark:border-gray-800">
                <div className="aspect-[16/10] bg-gray-100 dark:bg-gray-900"/>
                <div className="p-5 space-y-3">
                  <div className="h-4 w-16 bg-gray-100 dark:bg-gray-900 rounded"/>
                  <div className="h-6 bg-gray-100 dark:bg-gray-900 rounded"/>
                  <div className="h-4 w-3/4 bg-gray-100 dark:bg-gray-900 rounded"/>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  </div>
);

/* ═══════════════════════════════════════
   Main Component
   ═══════════════════════════════════════ */
const isVideoMedia = (url: string) => /\.(mp4|webm|ogg|mov|avi|mkv)(\?|$)/i.test(url);

export default function ModernHomePage() {
  const [featured, setFeatured] = useState<Article[]>([]);
  const [recent, setRecent] = useState<Article[]>([]);
  const [popular, setPopular] = useState<Article[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [stats, setStats] = useState<Stats>({});
  const [loading, setLoading] = useState(true);
  const [activeHeroSlide, setActiveHeroSlide] = useState(0);

  const {hero, sections, newsletter, messages, loading: configLoading} = useHomeConfig();

  const heroRef = useRef<HTMLDivElement>(null);
  const {scrollYProgress} = useScroll({
    target: heroRef,
    offset: ['start start', 'end start'],
  });
  const heroParallaxY = useTransform(scrollYProgress, [0, 1], [0, 150]);
  const heroOpacity = useTransform(scrollYProgress, [0, 0.8], [1, 0]);

  useEffect(() => {
    (async () => {
      try {
        const [featRes, recentRes, popRes, catRes, statRes] = await Promise.all([
          apiClient.get('/home/featured'),
          apiClient.get('/home/recent'),
          apiClient.get('/home/popular'),
          apiClient.get('/home/categories'),
          apiClient.get('/home/stats'),
        ]);
        if (featRes.success) setFeatured(Array.isArray(featRes.data) ? featRes.data : featRes.data?.articles || []);
        if (recentRes.success) setRecent(Array.isArray(recentRes.data) ? recentRes.data.slice(0, 12) : recentRes.data?.articles?.slice(0, 12) || []);
        if (popRes.success) setPopular(Array.isArray(popRes.data) ? popRes.data.slice(0, 8) : popRes.data?.articles?.slice(0, 8) || []);
        if (catRes.success) setCategories(Array.isArray(catRes.data) ? catRes.data : catRes.data?.categories || []);
        if (statRes.success) setStats(statRes.data || {});
      } catch {
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  // Auto-rotate hero featured slides
  useEffect(() => {
    if (featured.length <= 1) return;
    const timer = setInterval(() => {
      setActiveHeroSlide(prev => (prev + 1) % Math.min(featured.length, 5));
    }, 6000);
    return () => clearInterval(timer);
  }, [featured.length]);

  if (loading || configLoading) return <LoadingScreen/>;

  const heroFeatured = featured.slice(0, 5);
  const heroArticle = heroFeatured[activeHeroSlide];

  const categoryGradients = [
    'from-blue-600 via-blue-500 to-cyan-400',
    'from-purple-600 via-purple-500 to-pink-400',
    'from-emerald-600 via-emerald-500 to-teal-400',
    'from-orange-600 via-orange-500 to-amber-400',
    'from-indigo-600 via-indigo-500 to-blue-400',
    'from-rose-600 via-rose-500 to-pink-400',
  ];

  const categoryIcons = [Sparkles, Star, Flame, Zap, BookOpen, Hash];

  return (
    <div className="bg-white dark:bg-gray-950 overflow-hidden">

      {/* ═══════════════════════════════════════════
          HERO: Cinematic Full-Screen Section
          ═══════════════════════════════════════════ */}
      <section ref={heroRef} className="relative h-[90vh] min-h-[650px] max-h-[1000px] overflow-hidden">
        {/* Background with parallax */}
        <motion.div
          style={{y: heroParallaxY}}
          className="absolute inset-0 -top-[10%] -bottom-[10%]"
        >
          {(() => {
            const bgUrl = heroArticle?.cover_image || hero.backgroundImage || '';
            const fullBgUrl = bgUrl ? getFullMediaUrl(bgUrl) : '';
            if (fullBgUrl && isVideoMedia(bgUrl)) {
              return (
                <video
                  src={fullBgUrl}
                  className="w-full h-full object-cover"
                  autoPlay
                  loop
                  muted
                  playsInline
                />
              );
            }
            if (fullBgUrl) {
              return (
                <img
                  src={fullBgUrl}
                  alt=""
                  className="w-full h-full object-cover"
                />
              );
            }
            return <div className="w-full h-full bg-gradient-to-br from-gray-900 via-blue-950 to-gray-900"/>;
          })()}
        </motion.div>

        {/* Gradient overlays */}
        <div className="absolute inset-0 bg-gradient-to-r from-black/80 via-black/50 to-transparent"/>
        <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-black/30"/>
        <div
          className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-white dark:from-gray-950 to-transparent"/>

        {/* Animated background particles */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          {[...Array(20)].map((_, i) => (
            <motion.div
              key={i}
              className="absolute w-1 h-1 bg-white/20 rounded-full"
              initial={{
                x: Math.random() * (typeof window !== 'undefined' ? window.innerWidth : 1200),
                y: Math.random() * (typeof window !== 'undefined' ? window.innerHeight : 800),
              }}
              animate={{
                y: [null, Math.random() * -200 - 100],
                opacity: [0, 0.6, 0],
              }}
              transition={{
                duration: Math.random() * 8 + 6,
                repeat: Infinity,
                delay: Math.random() * 5,
                ease: 'linear',
              }}
            />
          ))}
        </div>

        {/* Hero Content */}
        <motion.div
          style={{opacity: heroOpacity}}
          className="relative h-full flex items-center"
        >
          <div className="max-w-7xl mx-auto px-6 sm:px-8 w-full">
            <div className="max-w-2xl">
              {/* Badge */}
              <motion.div
                initial={{opacity: 0, y: 20}}
                animate={{opacity: 1, y: 0}}
                transition={{duration: 0.6, delay: 0.2}}
              >
                <span className="inline-flex items-center gap-2 px-4 py-2 bg-white/10 backdrop-blur-md
                  rounded-full text-sm font-medium text-white/90 border border-white/20 mb-8">
                  <Sparkles className="w-4 h-4 text-amber-400"/>
                  {heroArticle?.category || '精选内容'}
                </span>
              </motion.div>

              {/* Title */}
              <AnimatePresence mode="wait">
                <motion.h1
                  key={activeHeroSlide}
                  initial={{opacity: 0, y: 30}}
                  animate={{opacity: 1, y: 0}}
                  exit={{opacity: 0, y: -20}}
                  transition={{duration: 0.7, ease: [0.22, 1, 0.36, 1] as [number, number, number, number]}}
                  className="text-4xl sm:text-5xl lg:text-6xl xl:text-7xl font-black text-white
                    tracking-tight leading-[1.05] mb-6"
                >
                  {heroArticle?.title || hero.title}
                </motion.h1>
              </AnimatePresence>

              {/* Subtitle */}
              <AnimatePresence mode="wait">
                <motion.p
                  key={`sub-${activeHeroSlide}`}
                  initial={{opacity: 0, y: 20}}
                  animate={{opacity: 1, y: 0}}
                  exit={{opacity: 0, y: -10}}
                  transition={{duration: 0.6, delay: 0.1}}
                  className="text-base sm:text-lg lg:text-xl text-white/70 mb-10 leading-relaxed max-w-xl"
                >
                  {heroArticle?.excerpt || heroArticle?.summary || hero.subtitle}
                </motion.p>
              </AnimatePresence>

              {/* CTAs */}
              <motion.div
                initial={{opacity: 0, y: 20}}
                animate={{opacity: 1, y: 0}}
                transition={{duration: 0.6, delay: 0.4}}
                className="flex flex-wrap gap-4"
              >
                <a
                  href={heroArticle ? `/view?slug=${heroArticle.slug}` : hero.ctaLink}
                  target={hero.ctaTarget as React.HTMLAttributeAnchorTarget}
                  className="group inline-flex items-center gap-3 px-8 py-4 bg-white text-gray-900
                    font-bold rounded-xl hover:bg-gray-100 transition-all duration-300
                    shadow-2xl shadow-black/20 hover:shadow-white/20 hover:-translate-y-0.5"
                >
                  {hero.ctaText}
                  <ArrowRight className="w-5 h-5 transition-transform group-hover:translate-x-1"/>
                </a>
                <a
                  href="/articles"
                  className="inline-flex items-center gap-3 px-8 py-4 bg-white/10 backdrop-blur-sm text-white
                    font-medium rounded-xl border border-white/20 hover:bg-white/20 transition-all duration-300
                    hover:-translate-y-0.5"
                >
                  浏览全部
                  <ArrowUpRight className="w-5 h-5"/>
                </a>
              </motion.div>

              {/* Hero Slide Indicators */}
              {heroFeatured.length > 1 && (
                <motion.div
                  initial={{opacity: 0}}
                  animate={{opacity: 1}}
                  transition={{delay: 0.8}}
                  className="flex items-center gap-2 mt-12"
                >
                  {heroFeatured.map((_, i) => (
                    <button
                      key={i}
                      onClick={() => setActiveHeroSlide(i)}
                      className={`h-1 rounded-full transition-all duration-500 ${
                        i === activeHeroSlide
                          ? 'w-10 bg-white'
                          : 'w-3 bg-white/30 hover:bg-white/50'
                      }`}
                      aria-label={`幻灯片 ${i + 1}`}
                    />
                  ))}
                  <span className="text-white/40 text-sm ml-3 font-mono">
                    {String(activeHeroSlide + 1).padStart(2, '0')} / {String(heroFeatured.length).padStart(2, '0')}
                  </span>
                </motion.div>
              )}
            </div>
          </div>
        </motion.div>
      </section>

      {/* ═══════════════════════════════════════════
          FEATURED: Hero Card + Side List
          ═══════════════════════════════════════════ */}
      {featured.length > 0 && (
        <Section className="max-w-7xl mx-auto px-6 sm:px-8 py-20 sm:py-28">
          <motion.div variants={fadeUp} className="flex items-end justify-between mb-12">
            <div>
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-1 bg-gradient-to-r from-blue-600 to-cyan-500 rounded-full"/>
                <span className="text-sm font-semibold text-blue-600 dark:text-blue-400 uppercase tracking-widest">
                  Featured
                </span>
              </div>
              <h2 className="text-3xl sm:text-4xl font-black text-gray-900 dark:text-white tracking-tight">
                {sections.featuredTitle}
              </h2>
            </div>
            <a
              href="/articles"
              className="hidden sm:flex items-center gap-2 text-sm font-semibold text-gray-500 hover:text-blue-600
                dark:text-gray-400 dark:hover:text-blue-400 transition-colors group"
            >
              查看全部
              <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1"/>
            </a>
          </motion.div>

          <div className="grid lg:grid-cols-12 gap-6">
            {/* Main Featured */}
            <motion.div variants={fadeUp} className="lg:col-span-7">
              <a
                href={`/view?slug=${featured[0].slug}`}
                className="group block relative aspect-[16/10] rounded-2xl overflow-hidden bg-gray-100 dark:bg-gray-900"
              >
                {featured[0].cover_image ? (
                  <img
                    src={getFullMediaUrl(featured[0].cover_image)}
                    alt={featured[0].title}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
                    loading="eager"
                  />
                ) : (
                  <div
                    className="w-full h-full flex items-center justify-center bg-gradient-to-br from-blue-50 to-purple-50 dark:from-blue-950/50 dark:to-purple-950/50">
                    <BookOpen className="w-20 h-20 text-gray-200 dark:text-gray-800"/>
                  </div>
                )}
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent"/>
                <div className="absolute bottom-0 left-0 right-0 p-6 sm:p-8">
                  {featured[0].tags?.[0] && (
                    <span
                      className="inline-flex items-center gap-1.5 px-3 py-1 bg-blue-600 text-white text-xs font-semibold rounded-full mb-4">
                      <Hash className="w-3 h-3"/>
                      {featured[0].tags[0]}
                    </span>
                  )}
                  <h3
                    className="text-2xl sm:text-3xl font-bold text-white mb-3 leading-tight line-clamp-2 group-hover:text-blue-200 transition-colors">
                    {featured[0].title}
                  </h3>
                  <p className="text-white/70 text-sm line-clamp-2 max-w-lg mb-4">
                    {featured[0].excerpt || featured[0].summary || messages.noSummary}
                  </p>
                  <div className="flex items-center gap-4 text-xs text-white/50">
                    {featured[0].created_at && (
                      <span className="flex items-center gap-1.5">
                        <Calendar className="w-3.5 h-3.5"/>
                        {new Date(featured[0].created_at).toLocaleDateString('zh-CN')}
                      </span>
                    )}
                    <span className="flex items-center gap-1.5">
                      <Eye className="w-3.5 h-3.5"/>
                      {featured[0].views || 0}
                    </span>
                    <span className="flex items-center gap-1.5">
                      <Heart className="w-3.5 h-3.5"/>
                      {featured[0].likes || 0}
                    </span>
                  </div>
                </div>
              </a>
            </motion.div>

            {/* Side Featured List */}
            <div className="lg:col-span-5 flex flex-col gap-4">
              {featured.slice(1, 4).map((article, i) => (
                <motion.a
                  key={article.id}
                  variants={fadeUp}
                  href={`/view?slug=${article.slug}`}
                  className="group flex gap-4 p-3 rounded-xl border border-gray-100 dark:border-gray-800
                    hover:border-blue-200 dark:hover:border-blue-800 bg-white dark:bg-gray-900/50
                    hover:shadow-lg hover:shadow-blue-500/5 transition-all duration-300"
                >
                  <div className="flex-shrink-0 w-28 h-20 rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-800">
                    {article.cover_image ? (
                      <img
                        src={getFullMediaUrl(article.cover_image)}
                        alt={article.title}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                        loading="lazy"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <BookOpen className="w-6 h-6 text-gray-300 dark:text-gray-700"/>
                      </div>
                    )}
                  </div>
                  <div className="flex-1 min-w-0 flex flex-col justify-center">
                    <h4 className="font-semibold text-gray-900 dark:text-white text-sm line-clamp-2
                      group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors leading-snug">
                      {article.title}
                    </h4>
                    <div className="flex items-center gap-3 mt-2 text-xs text-gray-400">
                      <span className="flex items-center gap-1">
                        <Eye className="w-3 h-3"/>{article.views || 0}
                      </span>
                      <span className="flex items-center gap-1">
                        <Heart className="w-3 h-3"/>{article.likes || 0}
                      </span>
                    </div>
                  </div>
                </motion.a>
              ))}
            </div>
          </div>
        </Section>
      )}


      {/* ═══════════════════════════════════════════
          CATEGORIES: Immersive Cards with Horizontal Scroll
          ═══════════════════════════════════════════ */}
      {categories.length > 0 && (
        <Section
          id="categories"
          className="py-20 sm:py-28 bg-gray-50 dark:bg-gray-900/50 border-y border-gray-100 dark:border-gray-900"
        >
          <div className="max-w-7xl mx-auto px-6 sm:px-8">
            <motion.div variants={fadeUp} className="flex items-end justify-between mb-12">
              <div>
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-1 bg-gradient-to-r from-purple-600 to-pink-500 rounded-full"/>
                  <span
                    className="text-sm font-semibold text-purple-600 dark:text-purple-400 uppercase tracking-widest">
                    Explore
                  </span>
                </div>
                <h2 className="text-3xl sm:text-4xl font-black text-gray-900 dark:text-white tracking-tight">
                  {sections.categoriesTitle}
                </h2>
                <p className="text-gray-500 dark:text-gray-400 mt-2">按主题浏览感兴趣的内容</p>
              </div>
              <a
                href="/categories"
                className="hidden sm:flex items-center gap-2 text-sm font-semibold text-gray-500 hover:text-purple-600
                  dark:text-gray-400 dark:hover:text-purple-400 transition-colors group"
              >
                查看全部
                <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1"/>
              </a>
            </motion.div>

            <HorizontalScroll>
              {categories.map((cat, i) => {
                const Icon = categoryIcons[i % categoryIcons.length];
                return (
                  <motion.a
                    key={cat.id}
                    variants={scaleIn}
                    href={`/category?slug=${cat.slug}`}
                    className="group flex-shrink-0 w-[260px] snap-start"
                  >
                    <div className="relative h-52 rounded-2xl overflow-hidden border border-gray-100 dark:border-gray-800
                      bg-white dark:bg-gray-900 hover:border-gray-200 dark:hover:border-gray-700
                      hover:shadow-2xl hover:shadow-black/10 dark:hover:shadow-black/40 transition-all duration-500
                      hover:-translate-y-2"
                    >
                      {/* Gradient background */}
                      <div
                        className={`absolute inset-0 bg-gradient-to-br ${categoryGradients[i % categoryGradients.length]} opacity-10
                        group-hover:opacity-20 transition-opacity duration-500`}/>

                      {/* Content */}
                      <div className="relative h-full flex flex-col items-center justify-center p-6 text-center">
                        <div
                          className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${categoryGradients[i % categoryGradients.length]}
                          flex items-center justify-center mb-4 shadow-lg group-hover:scale-110
                          group-hover:rotate-3 transition-all duration-500`}>
                          <Icon className="w-7 h-7 text-white"/>
                        </div>
                        <h3 className="font-bold text-gray-900 dark:text-white text-base mb-1.5">
                          {cat.name}
                        </h3>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {cat.count || 0} 篇文章
                        </p>
                        <div className="absolute bottom-4 right-4 w-8 h-8 rounded-full bg-gray-100 dark:bg-gray-800
                          flex items-center justify-center opacity-0 group-hover:opacity-100
                          translate-y-2 group-hover:translate-y-0 transition-all duration-300">
                          <ArrowUpRight className="w-4 h-4 text-gray-500 dark:text-gray-400"/>
                        </div>
                      </div>
                    </div>
                  </motion.a>
                );
              })}
            </HorizontalScroll>
          </div>
        </Section>
      )}


      {/* ═══════════════════════════════════════════
          RECENT ARTICLES: Magazine Grid
          ═══════════════════════════════════════════ */}
      {recent.length > 0 && (
        <Section className="max-w-7xl mx-auto px-6 sm:px-8 py-20 sm:py-28">
          <motion.div variants={fadeUp} className="flex items-end justify-between mb-12">
            <div>
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-1 bg-gradient-to-r from-emerald-600 to-teal-500 rounded-full"/>
                <span
                  className="text-sm font-semibold text-emerald-600 dark:text-emerald-400 uppercase tracking-widest">
                  Latest
                </span>
              </div>
              <h2 className="text-3xl sm:text-4xl font-black text-gray-900 dark:text-white tracking-tight">
                {sections.mainTitle}
              </h2>
            </div>
            <a
              href="/articles"
              className="hidden sm:flex items-center gap-2 text-sm font-semibold text-gray-500 hover:text-emerald-600
                dark:text-gray-400 dark:hover:text-emerald-400 transition-colors group"
            >
              查看全部
              <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1"/>
            </a>
          </motion.div>

          {/* Responsive Grid: Featured first, then grid */}
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {recent.map((article, i) => (
              <motion.a
                key={article.id}
                variants={fadeUp}
                href={`/view?slug=${article.slug}`}
                className="group flex flex-col bg-white dark:bg-gray-900 rounded-2xl border border-gray-100
                  dark:border-gray-800 overflow-hidden hover:border-gray-200 dark:hover:border-gray-700
                  hover:shadow-xl hover:shadow-black/5 dark:hover:shadow-black/30 transition-all duration-500
                  hover:-translate-y-1"
              >
                {/* Cover */}
                <div className="relative aspect-[16/10] bg-gray-50 dark:bg-gray-800 overflow-hidden">
                  {article.cover_image ? (
                    <img
                      src={getFullMediaUrl(article.cover_image)}
                      alt={article.title}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
                      loading="lazy"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <BookOpen className="w-10 h-10 text-gray-200 dark:text-gray-700"/>
                    </div>
                  )}
                  {/* Category badge */}
                  {article.category && (
                    <div className="absolute top-3 left-3">
                      <span className="px-2.5 py-1 bg-white/90 dark:bg-gray-900/90 backdrop-blur-sm
                        text-gray-700 dark:text-gray-300 text-[11px] font-medium rounded-lg
                        border border-gray-200/50 dark:border-gray-700/50">
                        {article.category}
                      </span>
                    </div>
                  )}
                </div>

                {/* Content */}
                <div className="flex-1 p-5 flex flex-col">
                  <div className="flex items-center gap-2 text-xs text-gray-400 mb-3">
                    {article.tags?.[0] && (
                      <span className="text-blue-600 dark:text-blue-400 font-medium flex items-center gap-0.5">
                        <Hash className="w-3 h-3"/>{article.tags[0]}
                      </span>
                    )}
                    {article.tags?.[0] && <span>·</span>}
                    {article.created_at && (
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3"/>
                        {new Date(article.created_at).toLocaleDateString('zh-CN')}
                      </span>
                    )}
                  </div>
                  <h3 className="font-bold text-gray-900 dark:text-white text-sm line-clamp-2
                    group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors leading-relaxed mb-3">
                    {article.title}
                  </h3>
                  <p className="text-xs text-gray-500 dark:text-gray-400 line-clamp-2 leading-relaxed mb-4 flex-1">
                    {article.excerpt || article.summary || ''}
                  </p>
                  <div
                    className="flex items-center justify-between text-xs text-gray-400 pt-3 border-t border-gray-50 dark:border-gray-800/50">
                    <div className="flex items-center gap-3">
                      <span className="flex items-center gap-1"><Eye className="w-3 h-3"/>{article.views || 0}</span>
                      <span className="flex items-center gap-1"><Heart className="w-3 h-3"/>{article.likes || 0}</span>
                    </div>
                    {article.author && (
                      <div className="flex items-center gap-1.5">
                        {article.author.avatar ? (
                          <img src={article.author.avatar} alt="" className="w-5 h-5 rounded-full"/>
                        ) : (
                          <div className="w-5 h-5 rounded-full bg-gradient-to-br from-blue-400 to-purple-400"/>
                        )}
                        <span className="font-medium text-gray-500 dark:text-gray-400">{article.author.username}</span>
                      </div>
                    )}
                  </div>
                </div>
              </motion.a>
            ))}
          </div>
        </Section>
      )}


      {/* ═══════════════════════════════════════════
          POPULAR / TRENDING: Rank List Style
          ═══════════════════════════════════════════ */}
      {popular.length > 0 && (
        <Section
          id="trending"
          className="py-20 sm:py-28 bg-gray-50 dark:bg-gray-900/50 border-y border-gray-100 dark:border-gray-900"
        >
          <div className="max-w-7xl mx-auto px-6 sm:px-8">
            <motion.div variants={fadeUp} className="flex items-end justify-between mb-12">
              <div>
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-1 bg-gradient-to-r from-orange-500 to-red-500 rounded-full"/>
                  <span
                    className="text-sm font-semibold text-orange-600 dark:text-orange-400 uppercase tracking-widest">
                    Trending
                  </span>
                </div>
                <h2
                  className="text-3xl sm:text-4xl font-black text-gray-900 dark:text-white tracking-tight flex items-center gap-3">
                  <Flame className="w-8 h-8 text-orange-500"/>
                  热门趋势
                </h2>
                <p className="text-gray-500 dark:text-gray-400 mt-2">最受欢迎的内容</p>
              </div>
            </motion.div>

            <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
              {popular.map((article, i) => (
                <motion.a
                  key={article.id}
                  variants={fadeUp}
                  href={`/view?slug=${article.slug}`}
                  className="group relative flex flex-col bg-white dark:bg-gray-900 rounded-2xl border border-gray-100
                    dark:border-gray-800 overflow-hidden hover:border-gray-200 dark:hover:border-gray-700
                    hover:shadow-xl hover:shadow-black/5 dark:hover:shadow-black/30 transition-all duration-500
                    hover:-translate-y-1"
                >
                  {/* Rank badge */}
                  <div className="absolute top-3 left-3 z-10">
                    <span className={`inline-flex items-center justify-center w-8 h-8 rounded-lg text-sm font-black ${
                      i === 0 ? 'bg-amber-500 text-white shadow-lg shadow-amber-500/30' :
                        i === 1 ? 'bg-gray-400 text-white' :
                          i === 2 ? 'bg-orange-600 text-white' :
                            'bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400'
                    }`}>
                      {i + 1}
                    </span>
                  </div>

                  {/* Cover */}
                  <div className="relative aspect-[16/10] bg-gray-50 dark:bg-gray-800 overflow-hidden">
                    {article.cover_image ? (
                      <img
                        src={getFullMediaUrl(article.cover_image)}
                        alt={article.title}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
                        loading="lazy"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <TrendingUp className="w-10 h-10 text-gray-200 dark:text-gray-700"/>
                      </div>
                    )}
                  </div>

                  {/* Content */}
                  <div className="p-4 flex-1">
                    <h3 className="font-bold text-gray-900 dark:text-white text-sm line-clamp-2
                      group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors leading-relaxed mb-3">
                      {article.title}
                    </h3>
                    <div className="flex items-center gap-3 text-xs text-gray-400">
                      <span className="flex items-center gap-1">
                        <Eye className="w-3 h-3"/>{article.views || 0}
                      </span>
                      <span className="flex items-center gap-1">
                        <Heart className="w-3 h-3"/>{article.likes || 0}
                      </span>
                    </div>
                  </div>
                </motion.a>
              ))}
            </div>
          </div>
        </Section>
      )}


      {/* ═══════════════════════════════════════════
          CTA: Newsletter / Registration
          ═══════════════════════════════════════════ */}
      <Section className="max-w-7xl mx-auto px-6 sm:px-8 py-20 sm:py-28">
        <motion.div
          variants={scaleIn}
          className="relative rounded-3xl overflow-hidden"
        >
          {/* Background */}
          <div className="absolute inset-0 bg-gradient-to-br from-blue-600 via-purple-600 to-blue-800"/>
          <div className="absolute inset-0 opacity-30"
               style={{
                 backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.08'%3E%3Ccircle cx='30' cy='30' r='2'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
               }}
          />
          {/* Gradient blur orbs */}
          <div className="absolute -top-24 -left-24 w-64 h-64 bg-blue-400/30 rounded-full blur-3xl"/>
          <div className="absolute -bottom-24 -right-24 w-64 h-64 bg-purple-400/30 rounded-full blur-3xl"/>

          <div className="relative z-10 p-8 sm:p-12 lg:p-16 text-center">
            <motion.div variants={fadeUp}>
              <span className="inline-flex items-center gap-2 px-4 py-2 bg-white/10 backdrop-blur-sm
                rounded-full text-sm font-medium text-white/90 border border-white/20 mb-6">
                <Sparkles className="w-4 h-4 text-amber-300"/>
                加入我们
              </span>
            </motion.div>
            <motion.h2
              variants={fadeUp}
              className="text-3xl sm:text-4xl lg:text-5xl font-black text-white mb-5 leading-tight"
            >
              {newsletter.title}
            </motion.h2>
            <motion.p
              variants={fadeUp}
              className="text-blue-100/80 text-lg mb-10 max-w-xl mx-auto leading-relaxed"
            >
              {newsletter.subtitle}
            </motion.p>
            <motion.div variants={fadeUp} className="flex flex-wrap items-center justify-center gap-4">
              <a
                href="/register"
                className="group inline-flex items-center gap-3 px-8 py-4 bg-white text-blue-700
                  font-bold rounded-xl hover:bg-gray-50 transition-all duration-300 shadow-xl
                  shadow-black/10 hover:shadow-white/20 hover:-translate-y-0.5"
              >
                {newsletter.buttonText || '免费注册'}
                <ArrowRight className="w-5 h-5 transition-transform group-hover:translate-x-1"/>
              </a>
              <a
                href="/about"
                className="inline-flex items-center gap-3 px-8 py-4 bg-white/10 backdrop-blur-sm
                  text-white font-medium rounded-xl border border-white/20 hover:bg-white/20
                  transition-all duration-300 hover:-translate-y-0.5"
              >
                了解更多
              </a>
            </motion.div>
          </div>
        </motion.div>
      </Section>


      {/* ═══════════════════════════════════════════
          FOOTER SPACER
          ═══════════════════════════════════════════ */}
      <div className="h-8"/>
    </div>
  );
}
