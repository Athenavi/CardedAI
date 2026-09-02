import { useState, useEffect } from 'react';

export function CookieBanner() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const accepted = localStorage.getItem('cookie_consent');
    if (!accepted) {
      const timer = setTimeout(() => setVisible(true), 1000);
      return () => clearTimeout(timer);
    }
  }, []);

  const accept = () => {
    localStorage.setItem('cookie_consent', 'accepted');
    document.cookie = 'cookie_consent=accepted;path=/;max-age=31536000;SameSite=Lax';
    setVisible(false);
  };

  const decline = () => {
    localStorage.setItem('cookie_consent', 'declined');
    document.cookie = 'cookie_consent=declined;path=/;max-age=31536000;SameSite=Lax';
    setVisible(false);
  };

  if (!visible) return null;

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 p-4 bg-background border-t shadow-lg">
      <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
        <p className="text-sm text-muted-foreground">
          我们使用 Cookie 来改善您的体验。继续使用即表示您同意我们的 Cookie 政策。
        </p>
        <div className="flex gap-2">
          <button
            onClick={decline}
            className="px-4 py-2 text-sm rounded-md border hover:bg-accent"
          >
            拒绝
          </button>
          <button
            onClick={accept}
            className="px-4 py-2 text-sm rounded-md bg-primary text-primary-foreground hover:bg-primary/90"
          >
            接受
          </button>
        </div>
      </div>
    </div>
  );
}
