'use client';

import { useEffect, useMemo, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import toast from 'react-hot-toast';
import { Copy, ExternalLink } from 'lucide-react';
import { analyticsAPI, quizAPI, StoredQuiz } from '@/lib/api';
import { useAuthStore } from '@/store/store';
import { useQuizStore } from '@/store/store';

export default function QuizReviewPage() {
  const params = useParams<{ quizId: string }>();
  const quizId = params?.quizId;
  const router = useRouter();
  const { user, isLoggedIn } = useAuthStore();
  const { setQuiz } = useQuizStore();

  const [quiz, setQuizData] = useState<StoredQuiz | null>(null);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [exportLink, setExportLink] = useState('');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!isLoggedIn || !user) {
      router.push('/');
      return;
    }

    if (!quizId) {
      toast.error('Quiz ID is missing.');
      router.push('/dashboard/history');
      return;
    }

    const loadQuiz = async () => {
      try {
        const response = await analyticsAPI.getQuizById(user, quizId);
        setQuizData(response.quiz);
      } catch (error: any) {
        toast.error(error.response?.data?.detail || 'Failed to load quiz details');
        router.push('/dashboard/history');
      } finally {
        setLoading(false);
      }
    };

    loadQuiz();
  }, [isLoggedIn, user, quizId, router]);

  const answeredCount = useMemo(
    () => (quiz?.submitted_answers || []).filter((value) => value && value.trim()).length,
    [quiz]
  );

  const handleRetakeQuiz = () => {
    if (!quiz?.mcqs || quiz.mcqs.length === 0 || !quiz.id) {
      toast.error('This quiz cannot be retaken because questions are missing.');
      return;
    }

    setQuiz(quiz.mcqs, quiz.topic, quiz.difficulty, quiz.id);
    router.push('/dashboard/quiz');
  };

  const handleExportGoogleForm = async () => {
    if (!user || !quiz?.mcqs || quiz.mcqs.length === 0) {
      toast.error('Quiz questions are not available for export.');
      return;
    }

    setExporting(true);
    try {
      const response = await quizAPI.exportToGoogleForm(user, quiz.mcqs, quiz.topic);
      if (response.success && response.link) {
        toast.success('Google Form created successfully');
        setExportLink(response.link);
      } else {
        toast.error('Failed to export quiz to Google Form');
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Error exporting quiz');
    } finally {
      setExporting(false);
    }
  };

  const handleCopyLink = async () => {
    if (!exportLink) return;
    try {
      await navigator.clipboard.writeText(exportLink);
      setCopied(true);
      toast.success('Link copied');
      window.setTimeout(() => setCopied(false), 1400);
    } catch {
      toast.error('Unable to copy link');
    }
  };

  if (!isLoggedIn) {
    return <div>Redirecting...</div>;
  }

  if (loading) {
    return <div className="text-sm text-zinc-500">Loading quiz review...</div>;
  }

  if (!quiz) {
    return <div className="text-sm text-zinc-500">Quiz not found.</div>;
  }

  const scoreText = typeof quiz.score === 'number' ? `${quiz.score}/${quiz.num_questions}` : '-';
  const reviewRows = quiz.results || [];
  const scoreValue = typeof quiz.score === 'number' ? quiz.score : 0;
  const totalQuestions = Math.max(quiz.num_questions || 0, 1);
  const percentage = Math.round((scoreValue / totalQuestions) * 100);

  const getResultFeedback = (value: number) => {
    if (value >= 90) return 'Excellent performance';
    if (value >= 80) return 'Great job';
    if (value >= 70) return 'Good work';
    if (value >= 60) return 'Keep practicing';
    return 'Keep improving';
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 mb-1">Quiz Review</h1>
        <p className="text-sm text-zinc-600">{quiz.topic} • {quiz.difficulty}</p>
      </div>

      <div className="border border-zinc-200/70 rounded-xl p-6 text-center">
        <p className="text-sm text-zinc-600 mb-3">Your Score</p>
        <div className="mb-5">
          <div className="relative w-36 h-36 mx-auto">
            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="45" fill="none" stroke="#e5e7eb" strokeWidth="8" />
              <circle
                cx="50"
                cy="50"
                r="45"
                fill="none"
                stroke="#18181b"
                strokeWidth="8"
                strokeDasharray={`${(percentage / 100) * 282.7} 282.7`}
                strokeLinecap="round"
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <p className="text-3xl font-semibold text-zinc-900">{percentage}%</p>
              <p className="text-zinc-600 text-xs">{scoreText}</p>
            </div>
          </div>
        </div>
        <h2 className="text-xl font-semibold tracking-tight text-zinc-900 mb-1.5">
          {getResultFeedback(percentage)}
        </h2>
        <p className="text-zinc-600 text-sm">
          Answered {answeredCount} out of {quiz.num_questions} questions.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="border border-zinc-200/70 rounded-xl p-4 text-center">
          <h3 className="text-zinc-600 text-sm font-medium">Correct Answers</h3>
          <p className="text-2xl font-semibold text-zinc-900">{scoreValue}</p>
        </div>
        <div className="border border-zinc-200/70 rounded-xl p-4 text-center">
          <h3 className="text-zinc-600 text-sm font-medium">Incorrect Answers</h3>
          <p className="text-2xl font-semibold text-zinc-900">{Math.max(quiz.num_questions - scoreValue, 0)}</p>
        </div>
      </div>

      {!quiz.results || quiz.results.length === 0 ? (
        <div className="border border-zinc-200/70 rounded-xl p-5 space-y-3">
          <p className="text-sm text-zinc-700">
            This quiz does not yet have a submitted answer review. You can retake it now.
          </p>
          <button
            onClick={handleRetakeQuiz}
            className="btn px-5"
          >
            Start Quiz
          </button>
        </div>
      ) : (
        <div className="border border-zinc-200/70 rounded-xl overflow-hidden divide-y divide-zinc-200/70">
          {reviewRows.map((row, idx) => {
            const isCorrect = row.status === '✅';
            return (
              <div key={idx} className="p-4 space-y-2">
                <p className="text-sm font-medium text-zinc-900">Q{idx + 1}. {row.question}</p>
                <p className="text-xs text-zinc-600">
                  Your answer: <span className={isCorrect ? 'text-zinc-900 font-medium' : 'text-zinc-700'}>{row.your_answer || '(No answer)'}</span>
                </p>
                <p className="text-xs text-zinc-600">
                  Correct answer: <span className="font-medium text-zinc-900">{row.correct}</span>
                </p>
                <p className="text-xs font-medium text-zinc-900">
                  {isCorrect ? 'Correct' : 'Incorrect'}
                </p>
              </div>
            );
          })}
        </div>
      )}

      <div className="flex flex-col sm:flex-row gap-2.5 sm:justify-end">
        <button
          onClick={() => router.push('/dashboard/history')}
          className="interactive-soft h-10 px-4 rounded-lg border border-zinc-200 text-zinc-700 text-sm hover:bg-zinc-100/70"
        >
          Back to History
        </button>
        <button
          onClick={handleExportGoogleForm}
          disabled={exporting || !quiz?.mcqs || quiz.mcqs.length === 0}
          className="interactive-soft h-10 px-4 rounded-lg border border-zinc-200 text-zinc-800 text-sm hover:bg-zinc-100/70 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {exporting ? 'Exporting...' : 'Export to Google Form'}
        </button>

        {exportLink && (
          <div className="border border-zinc-200/70 rounded-xl p-3 flex items-center gap-2 w-full sm:w-auto sm:min-w-[460px]">
            <input value={exportLink} readOnly className="input h-9 flex-1" />

            <span className="tooltip-wrap">
              <button
                type="button"
                onClick={() => window.open(exportLink, '_blank', 'noopener,noreferrer')}
                className="interactive-soft h-9 w-9 rounded-lg border border-zinc-200 text-zinc-700"
                aria-label="Open link"
              >
                <ExternalLink size={16} className="mx-auto" />
              </button>
              <span className="tooltip-bubble">Open form</span>
            </span>

            <span className="tooltip-wrap">
              <button
                type="button"
                onClick={handleCopyLink}
                className="interactive-soft h-9 w-9 rounded-lg border border-zinc-200 text-zinc-700"
                aria-label="Copy link"
              >
                <Copy size={16} className="mx-auto" />
              </button>
              <span className="tooltip-bubble">{copied ? 'Copied!' : 'Copy response'}</span>
            </span>
          </div>
        )}

        <button
          onClick={handleRetakeQuiz}
          className="btn px-5"
        >
          Retake Quiz
        </button>
      </div>
    </div>
  );
}
