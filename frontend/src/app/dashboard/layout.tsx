'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';
import { useAuthStore } from '@/store/store';
import { useQuizStore } from '@/store/store';
import { analyticsAPI, StoredQuiz } from '@/lib/api';
import toast from 'react-hot-toast';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, isLoggedIn, hasHydrated, logout } = useAuthStore();
  const { setQuiz } = useQuizStore();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [recentQuizzes, setRecentQuizzes] = useState<StoredQuiz[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!hasHydrated) {
      return;
    }

    if (!isLoggedIn || !user) {
      router.push('/');
      return;
    }

    const loadRecentQuizzes = async () => {
      try {
        const response = await analyticsAPI.getRecentQuizzes(user);
        setRecentQuizzes(response.quizzes || []);
      } catch (error) {
        console.error('Failed to load recent quizzes');
      } finally {
        setLoading(false);
      }
    };

    loadRecentQuizzes();
  }, [hasHydrated, isLoggedIn, user, router]);

  const handleLogout = () => {
    logout();
    router.push('/');
    toast.success('Logged out successfully');
  };

  const formatDate = (timestamp: string) => {
    return new Date(timestamp).toLocaleDateString();
  };

  if (!hasHydrated) {
    return <div className="p-4 text-sm text-zinc-500">Loading...</div>;
  }

  if (!isLoggedIn) {
    return <div>Redirecting...</div>;
  }

  const displayUser = user || 'User';

  const SidebarIcon = ({ children }: { children: React.ReactNode }) => (
    <span className="w-4 h-4 inline-flex items-center justify-center text-zinc-500">{children}</span>
  );

  return (
    <div className="min-h-screen bg-white flex">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/30 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div
        className={`fixed inset-y-0 left-0 z-50 w-64 bg-zinc-50/80 border-r border-zinc-200/80 transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:sticky lg:top-0 lg:h-screen lg:self-start ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between px-3 py-3 border-b border-zinc-200/70">
            <h2 className="text-lg font-semibold tracking-tight text-zinc-900">SmartQuiz</h2>
            <button
              onClick={() => setSidebarOpen(false)}
              className="lg:hidden px-2 py-1 text-xs border border-zinc-200 rounded-lg text-zinc-700"
            >
              Close
            </button>
          </div>

          {/* Top Actions */}
          <div className="px-2.5 py-2.5 space-y-1.5 border-b border-zinc-200/70">
            <Link
              href="/dashboard/quiz-custom"
              className="interactive-soft flex items-center gap-2 w-full px-2.5 py-2 text-[13px] rounded-lg border border-zinc-200 text-zinc-800 hover:bg-white"
              onClick={() => setSidebarOpen(false)}
            >
              <SidebarIcon>
                <svg viewBox="0 0 24 24" className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                  <path d="M12 5v14M5 12h14" />
                </svg>
              </SidebarIcon>
              New Quiz
            </Link>
            <Link
              href="/dashboard/history"
              className="interactive-soft flex items-center gap-2 w-full px-2.5 py-2 text-[13px] rounded-lg text-zinc-700 hover:bg-white"
              onClick={() => setSidebarOpen(false)}
            >
              <SidebarIcon>
                <svg viewBox="0 0 24 24" className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                  <circle cx="11" cy="11" r="7" />
                  <path d="M20 20l-3.5-3.5" />
                </svg>
              </SidebarIcon>
              Search History
            </Link>
          </div>

          {/* Navigation */}
          <nav className="px-2.5 py-2.5 space-y-0.5 border-b border-zinc-200/70">
            <Link
              href="/dashboard"
              className={`interactive-soft flex items-center gap-2 px-2.5 py-1.5 text-[13px] rounded-lg ${
                pathname === '/dashboard'
                  ? 'bg-zinc-900 text-white'
                  : 'text-zinc-700 hover:bg-white'
              }`}
              onClick={() => setSidebarOpen(false)}
            >
              <SidebarIcon>
                <svg viewBox="0 0 24 24" className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                  <path d="M3 11l9-7 9 7" />
                  <path d="M5 10v10h14V10" />
                </svg>
              </SidebarIcon>
              Dashboard
            </Link>

            <Link
              href="/dashboard/quiz-adaptive"
              className={`interactive-soft flex items-center gap-2 px-2.5 py-1.5 text-[13px] rounded-lg ${
                pathname === '/dashboard/quiz-adaptive'
                  ? 'bg-zinc-900 text-white'
                  : 'text-zinc-700 hover:bg-white'
              }`}
              onClick={() => setSidebarOpen(false)}
            >
              <SidebarIcon>
                <svg viewBox="0 0 24 24" className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                  <path d="M4 19h16" />
                  <path d="M7 15l3-4 3 2 4-6" />
                </svg>
              </SidebarIcon>
              Adaptive Quiz
            </Link>

            <Link
              href="/dashboard/quiz-custom"
              className={`interactive-soft flex items-center gap-2 px-2.5 py-1.5 text-[13px] rounded-lg ${
                pathname === '/dashboard/quiz-custom'
                  ? 'bg-zinc-900 text-white'
                  : 'text-zinc-700 hover:bg-white'
              }`}
              onClick={() => setSidebarOpen(false)}
            >
              <SidebarIcon>
                <svg viewBox="0 0 24 24" className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                  <rect x="4" y="4" width="16" height="16" rx="2" />
                  <path d="M8 9h8M8 13h8M8 17h5" />
                </svg>
              </SidebarIcon>
              Custom Quiz
            </Link>

            <Link
              href="/dashboard/settings"
              className={`interactive-soft flex items-center gap-2 px-2.5 py-1.5 text-[13px] rounded-lg ${
                pathname === '/dashboard/settings'
                  ? 'bg-zinc-900 text-white'
                  : 'text-zinc-700 hover:bg-white'
              }`}
              onClick={() => setSidebarOpen(false)}
            >
              <SidebarIcon>
                <svg viewBox="0 0 24 24" className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                  <circle cx="12" cy="12" r="3" />
                  <path d="M19.4 15a1 1 0 0 0 .2 1.1l.1.1a1 1 0 0 1 0 1.4l-1 1a1 1 0 0 1-1.4 0l-.1-.1a1 1 0 0 0-1.1-.2 1 1 0 0 0-.6.9V20a1 1 0 0 1-1 1h-1.4a1 1 0 0 1-1-1v-.2a1 1 0 0 0-.6-.9 1 1 0 0 0-1.1.2l-.1.1a1 1 0 0 1-1.4 0l-1-1a1 1 0 0 1 0-1.4l.1-.1a1 1 0 0 0 .2-1.1 1 1 0 0 0-.9-.6H4a1 1 0 0 1-1-1v-1.4a1 1 0 0 1 1-1h.2a1 1 0 0 0 .9-.6 1 1 0 0 0-.2-1.1l-.1-.1a1 1 0 0 1 0-1.4l1-1a1 1 0 0 1 1.4 0l.1.1a1 1 0 0 0 1.1.2 1 1 0 0 0 .6-.9V4a1 1 0 0 1 1-1h1.4a1 1 0 0 1 1 1v.2a1 1 0 0 0 .6.9 1 1 0 0 0 1.1-.2l.1-.1a1 1 0 0 1 1.4 0l1 1a1 1 0 0 1 0 1.4l-.1.1a1 1 0 0 0-.2 1.1 1 1 0 0 0 .9.6h.2a1 1 0 0 1 1 1v1.4a1 1 0 0 1-1 1h-.2a1 1 0 0 0-.9.6Z" />
                </svg>
              </SidebarIcon>
              Settings
            </Link>

            <Link
              href="/dashboard/history"
              className={`interactive-soft flex items-center gap-2 px-2.5 py-1.5 text-[13px] rounded-lg ${
                pathname === '/dashboard/history'
                  ? 'bg-zinc-900 text-white'
                  : 'text-zinc-700 hover:bg-white'
              }`}
              onClick={() => setSidebarOpen(false)}
            >
              <SidebarIcon>
                <svg viewBox="0 0 24 24" className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                  <path d="M12 8v5l3 2" />
                  <circle cx="12" cy="12" r="8" />
                </svg>
              </SidebarIcon>
              Quiz History
            </Link>
          </nav>

          {/* Recent Quizzes */}
          <div className="px-2.5 py-2.5 flex-1 min-h-0 overflow-hidden">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-[10px] font-semibold text-zinc-500 uppercase tracking-[0.08em]">
                Recent Quizzes
              </h3>
              <Link
                href="/dashboard/history"
                className="interactive-soft inline-flex items-center gap-1 text-[10px] font-medium text-zinc-600 hover:text-zinc-900 rounded-md px-1.5 py-0.5"
                onClick={() => setSidebarOpen(false)}
              >
                <svg viewBox="0 0 24 24" className="w-3 h-3" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                  <path d="M20 20l-3.5-3.5" />
                  <circle cx="11" cy="11" r="7" />
                </svg>
                Manage
              </Link>
            </div>
            <div className="space-y-0.5 h-full overflow-y-auto pr-0.5">
              {loading ? (
                <p className="text-xs text-zinc-500 px-2 py-1">Loading...</p>
              ) : recentQuizzes.length > 0 ? (
                recentQuizzes.slice(0, 10).map((quiz, idx) => (
                  <button
                    key={idx}
                    className="interactive-soft w-full text-left px-2 py-1.5 rounded-lg hover:bg-white border border-transparent hover:border-zinc-200/70"
                    onClick={() => {
                      if (quiz.id) {
                        setSidebarOpen(false);
                        router.push(`/dashboard/history/${quiz.id}`);
                        return;
                      }

                      if (!quiz.mcqs || quiz.mcqs.length === 0) {
                        toast.error('Questions for this quiz are not available.');
                        return;
                      }
                      setQuiz(quiz.mcqs, quiz.topic, quiz.difficulty, quiz.id);
                      setSidebarOpen(false);
                      router.push('/dashboard/quiz');
                      toast.success('Loaded previous quiz.');
                    }}
                  >
                    <div className="flex justify-between items-start gap-2">
                      <div className="flex-1">
                        <p className="text-[13px] font-medium text-zinc-900 truncate leading-5">
                          {quiz.topic}
                        </p>
                        <p className="text-[11px] text-zinc-500 leading-4">
                          {quiz.difficulty} • {formatDate(quiz.timestamp)}
                        </p>
                      </div>
                      <div className="text-right text-[12px] font-semibold text-zinc-900 leading-5">
                        <p>
                          {typeof quiz.score === 'number' ? `${quiz.score}/${quiz.num_questions}` : '-'}
                        </p>
                      </div>
                    </div>
                  </button>
                ))
              ) : (
                <p className="text-xs text-zinc-500 px-2 py-1">
                  No quizzes yet. Take your first quiz!
                </p>
              )}
            </div>
          </div>

          {/* User Info & Logout */}
          <div className="px-2.5 py-2.5 border-t border-zinc-200/70 bg-zinc-50/95">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="w-7 h-7 bg-zinc-900 rounded-full flex items-center justify-center text-white text-xs font-semibold">
                  {displayUser.charAt(0).toUpperCase()}
                </div>
                <span className="ml-2.5 text-[13px] font-medium text-zinc-900 truncate max-w-[120px]">{displayUser}</span>
              </div>
              <button
                onClick={handleLogout}
                className="interactive-soft inline-flex items-center gap-1.5 px-2.5 py-1 text-[11px] border border-zinc-200 rounded-lg text-zinc-700 hover:bg-white"
                title="Logout"
              >
                <svg viewBox="0 0 24 24" className="w-3 h-3" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                  <path d="M10 17l-5-5 5-5" />
                  <path d="M5 12h10" />
                  <path d="M15 5h4v14h-4" />
                </svg>
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Mobile header */}
        <div className="lg:hidden bg-white border-b border-zinc-200/70 px-3 py-2.5 flex items-center justify-between">
          <button
            onClick={() => setSidebarOpen(true)}
            className="interactive-soft px-2 py-1 text-xs border border-zinc-200 rounded-lg text-zinc-700"
          >
            Menu
          </button>
          <h1 className="text-base font-semibold text-zinc-900">SmartQuiz</h1>
          <div className="w-12"></div>
        </div>

        {/* Page Content */}
        <main className="flex-1 p-5 lg:p-6">
          <div className="max-w-7xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
