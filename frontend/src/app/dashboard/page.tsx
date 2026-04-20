'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import toast from 'react-hot-toast';
import { useAuthStore } from '@/store/store';
import { analyticsAPI } from '@/lib/api';

export default function DashboardPage() {
  const router = useRouter();
  const { user, isLoggedIn } = useAuthStore();
  const [analytics, setAnalytics] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isLoggedIn || !user) {
      router.push('/');
      return;
    }

    // Load analytics once auth state is ready.
    const loadAnalytics = async () => {
      try {
        const response = await analyticsAPI.getAnalytics(user);
        setAnalytics(response.analytics);
      } catch (error: any) {
        toast.error('Failed to load analytics');
      } finally {
        setLoading(false);
      }
    };

    loadAnalytics();
  }, [isLoggedIn, user, router]);

  // Keep route transitions centralized for quick-action cards.
  const handleNavigation = (page: string) => {
    router.push(`/dashboard/${page}`);
  };

  if (!isLoggedIn || !user) {
    return <div>Loading...</div>;
  }

  if (loading) {
    return <div className="text-sm text-zinc-500">Loading dashboard...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Welcome Header */}
      <div>
        <h1 className="text-2xl md:text-3xl font-semibold tracking-tight text-zinc-900 mb-1.5">Welcome back, {user}</h1>
        <p className="text-sm text-zinc-600">
          Generate adaptive and custom quizzes from one clean workspace.
        </p>
      </div>

      {/* Analytics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div className="border border-zinc-200/70 rounded-xl p-4">
          <h3 className="text-zinc-600 text-sm font-medium">Total Quizzes</h3>
          <p className="text-3xl font-semibold text-zinc-900 mt-1.5">
            {analytics?.total_quizzes || 0}
          </p>
        </div>

        <div className="border border-zinc-200/70 rounded-xl p-4">
          <h3 className="text-zinc-600 text-sm font-medium">Average Score</h3>
          <p className="text-3xl font-semibold text-zinc-900 mt-1.5">
            {(analytics?.average_score || 0).toFixed(1)}%
          </p>
        </div>

        <div className="border border-zinc-200/70 rounded-xl p-4">
          <h3 className="text-zinc-600 text-sm font-medium">Weak Topics</h3>
          <p className="text-3xl font-semibold text-zinc-900 mt-1.5">
            {analytics?.weak_topics?.length || 0}
          </p>
        </div>
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-xl font-semibold text-zinc-900 mb-3">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <button
            onClick={() => handleNavigation('quiz-adaptive')}
            className="w-full px-4 py-3 text-left border border-zinc-200 rounded-xl hover:bg-zinc-100/70 transition-colors"
          >
            <div className="font-medium text-zinc-900 text-sm">Adaptive Quiz</div>
            <div className="text-xs text-zinc-600 mt-1">AI-tailored questions from weak areas</div>
          </button>
          <button
            onClick={() => handleNavigation('quiz-custom')}
            className="w-full px-4 py-3 text-left border border-zinc-200 rounded-xl hover:bg-zinc-100/70 transition-colors"
          >
            <div className="font-medium text-zinc-900 text-sm">Custom Quiz</div>
            <div className="text-xs text-zinc-600 mt-1">Choose topic, difficulty, and length</div>
          </button>
        </div>
      </div>

      {/* Weak Topics */}
      {analytics?.weak_topics && analytics.weak_topics.length > 0 && (
        <div>
          <h2 className="text-xl font-semibold text-zinc-900 mb-3">Areas to Focus On</h2>
          <ul className="border border-zinc-200/70 rounded-xl divide-y divide-zinc-200/70 overflow-hidden">
            {analytics.weak_topics.slice(0, 8).map((topic: string, idx: number) => (
              <li key={idx} className="px-4 py-2.5 text-sm text-zinc-800">
                {topic}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Recent Quizzes */}
      {analytics?.recent_quizzes && analytics.recent_quizzes.length > 0 && (
        <div>
          <h2 className="text-xl font-semibold text-zinc-900 mb-3">Recent Results</h2>
          <div className="border border-zinc-200/70 rounded-xl divide-y divide-zinc-200/70 overflow-hidden">
            {analytics.recent_quizzes.slice(0, 8).map((quiz: any, idx: number) => (
              <div key={idx} className="flex items-center justify-between px-4 py-2.5">
                <div>
                  <p className="text-sm font-medium text-zinc-900">{quiz.topic}</p>
                  <p className="text-xs text-zinc-600">{quiz.difficulty} • {quiz.num_questions} questions</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-semibold text-zinc-900">{quiz.score}/{quiz.num_questions}</p>
                  <p className="text-xs text-zinc-500">
                    {Math.round((quiz.score / quiz.num_questions) * 100)}%
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
