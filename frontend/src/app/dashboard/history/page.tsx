'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import toast from 'react-hot-toast';
import { analyticsAPI, StoredQuiz } from '@/lib/api';
import { useAuthStore } from '@/store/store';

export default function QuizHistoryPage() {
  const router = useRouter();
  const { user, isLoggedIn } = useAuthStore();
  const [quizzes, setQuizzes] = useState<StoredQuiz[]>([]);
  const [loading, setLoading] = useState(true);
  const [deletingQuizId, setDeletingQuizId] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoggedIn || !user) {
      router.push('/');
      return;
    }

    const loadQuizzes = async () => {
      try {
        const response = await analyticsAPI.getRecentQuizzes(user);
        setQuizzes(response.quizzes || []);
      } catch (error: any) {
        toast.error(error.response?.data?.detail || 'Failed to load quiz history');
      } finally {
        setLoading(false);
      }
    };

    loadQuizzes();
  }, [isLoggedIn, user, router]);

  const orderedQuizzes = useMemo(
    () =>
      [...quizzes].sort(
        (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
      ),
    [quizzes]
  );

  const handleOpenQuiz = (quiz: StoredQuiz) => {
    if (!quiz.id) {
      toast.error('This quiz cannot be opened because it has no ID.');
      return;
    }

    router.push(`/dashboard/history/${quiz.id}`);
  };

  const handleDeleteQuiz = async (quizId?: string) => {
    if (!user) return;
    if (!quizId) {
      toast.error('This quiz cannot be deleted because it has no ID.');
      return;
    }

    const confirmed = window.confirm('Delete this quiz permanently?');
    if (!confirmed) return;

    setDeletingQuizId(quizId);
    try {
      await analyticsAPI.deleteQuiz(user, quizId);
      setQuizzes((prev) => prev.filter((quiz) => quiz.id !== quizId));
      toast.success('Quiz deleted');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to delete quiz');
    } finally {
      setDeletingQuizId(null);
    }
  };

  const formatDate = (value: string) => {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return '-';
    return date.toLocaleString();
  };

  if (!isLoggedIn) {
    return <div>Redirecting...</div>;
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 mb-1.5">Quiz History</h1>
        <p className="text-sm text-zinc-600">
          Review previous quizzes, check scores, reopen any quiz, or delete old ones.
        </p>
      </div>

      <div className="border border-zinc-200/70 rounded-xl overflow-hidden">
        {loading ? (
          <div className="px-4 py-4 text-sm text-zinc-500">Loading quiz history...</div>
        ) : orderedQuizzes.length === 0 ? (
          <div className="px-4 py-5 text-sm text-zinc-500">No saved quizzes yet.</div>
        ) : (
          <div className="divide-y divide-zinc-200/70">
            {orderedQuizzes.map((quiz) => (
              <div key={quiz.id} className="px-4 py-3 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div className="min-w-0">
                  <p className="text-sm font-medium text-zinc-900 truncate">{quiz.topic}</p>
                  <p className="text-xs text-zinc-500 mt-0.5">
                    {quiz.difficulty} • {quiz.num_questions} questions • {formatDate(quiz.timestamp)}
                  </p>
                </div>

                <div className="flex items-center gap-2 sm:gap-3">
                  <div className="text-right min-w-[74px]">
                    <p className="text-xs text-zinc-500">Score</p>
                    <p className="text-sm font-semibold text-zinc-900">
                      {typeof quiz.score === 'number' ? `${quiz.score}/${quiz.num_questions}` : '-'}
                    </p>
                  </div>

                  <button
                    onClick={() => handleOpenQuiz(quiz)}
                    className="interactive-soft h-9 px-3 rounded-lg border border-zinc-200 text-zinc-800 text-sm hover:bg-zinc-100/70"
                  >
                    Open
                  </button>

                  <button
                    onClick={() => handleDeleteQuiz(quiz.id)}
                    disabled={deletingQuizId === quiz.id}
                    className="interactive-soft h-9 px-3 rounded-lg border border-zinc-900 bg-zinc-900 text-white text-sm hover:bg-zinc-800 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {deletingQuizId === quiz.id ? 'Deleting...' : 'Delete'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
