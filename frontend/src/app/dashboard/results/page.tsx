'use client';

import { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { useRouter } from 'next/navigation';
import toast from 'react-hot-toast';
import { Copy, ExternalLink } from 'lucide-react';
import { analyticsAPI, quizAPI } from '@/lib/api';
import { useAuthStore } from '@/store/store';
import { useQuizStore } from '@/store/store';

export default function ResultsPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { user } = useAuthStore();
  const { currentQuiz } = useQuizStore();
  const score = parseInt(searchParams.get('score') || '0');
  const total = parseInt(searchParams.get('total') || '5');
  const quizId = searchParams.get('quizId') || '';
  const topicFromQuery = searchParams.get('topic') || '';
  const percentage = Math.round((score / total) * 100);
  const [exporting, setExporting] = useState(false);
  const [quizMcqs, setQuizMcqs] = useState<any[] | null>(null);
  const [quizTopic, setQuizTopic] = useState<string>(topicFromQuery);
  const [reviewRows, setReviewRows] = useState<any[]>([]);
  const [exportLink, setExportLink] = useState('');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const loadQuizForExport = async () => {
      if (quizId && user) {
        try {
          const response = await analyticsAPI.getQuizById(user, quizId);
          if (response?.success && Array.isArray(response?.quiz?.mcqs)) {
            setQuizMcqs(response.quiz.mcqs);
            setQuizTopic(response.quiz.topic || topicFromQuery);
            if (Array.isArray(response.quiz.results)) {
              setReviewRows(response.quiz.results);
            }
            return;
          }
        } catch {
          // Fallback to store-based quiz payload if API lookup fails.
        }
      }

      if (Array.isArray(currentQuiz) && currentQuiz.length > 0) {
        setQuizMcqs(currentQuiz);
      }
      if (topicFromQuery) {
        setQuizTopic(topicFromQuery);
      }
    };

    loadQuizForExport();
  }, [quizId, user, currentQuiz, topicFromQuery]);

  const handleExportGoogleForm = async () => {
    if (!user || !quizMcqs || quizMcqs.length === 0) {
      toast.error('Quiz data not found for export.');
      return;
    }

    setExporting(true);
    try {
      const response = await quizAPI.exportToGoogleForm(user, quizMcqs, quizTopic);
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

  const getResultFeedback = (percentage: number) => {
    if (percentage >= 90) return 'Excellent performance';
    if (percentage >= 80) return 'Great job';
    if (percentage >= 70) return 'Good work';
    if (percentage >= 60) return 'Keep practicing';
    return 'Keep improving';
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Score Card */}
      <div className="border border-zinc-200/70 rounded-xl p-6 text-center">
        <p className="text-sm text-zinc-600 mb-3">Your Score</p>
        <div className="mb-5">
          <div className="relative w-40 h-40 mx-auto">
            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
              <circle
                cx="50"
                cy="50"
                r="45"
                fill="none"
                stroke="#e5e7eb"
                strokeWidth="8"
              />
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
              <p className="text-4xl font-semibold text-zinc-900">{percentage}%</p>
              <p className="text-zinc-600 text-xs">{score}/{total}</p>
            </div>
          </div>
        </div>

        <h2 className="text-2xl font-semibold tracking-tight text-zinc-900 mb-1.5">
          {getResultFeedback(percentage)}
        </h2>
        <p className="text-zinc-600 text-sm">
          You answered {score} out of {total} questions correctly.
        </p>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-2 gap-3">
        <div className="border border-zinc-200/70 rounded-xl p-4 text-center">
          <h3 className="text-zinc-600 text-sm font-medium">Correct Answers</h3>
          <p className="text-2xl font-semibold text-zinc-900">{score}</p>
        </div>
        <div className="border border-zinc-200/70 rounded-xl p-4 text-center">
          <h3 className="text-zinc-600 text-sm font-medium">Incorrect Answers</h3>
          <p className="text-2xl font-semibold text-zinc-900">{total - score}</p>
        </div>
      </div>

      {/* Feedback */}
      <div className="border border-zinc-200/70 rounded-xl p-5">
        <h3 className="text-base font-semibold text-zinc-900 mb-3">Feedback</h3>
        <div className="space-y-2 text-sm text-zinc-700">
          {percentage >= 80 && (
            <>
              <p>Great job. You demonstrated solid knowledge on this topic.</p>
              <p>Try the next difficulty level to keep challenging yourself.</p>
            </>
          )}
          {percentage >= 60 && percentage < 80 && (
            <>
              <p>You are making progress. Review the topics where you missed questions.</p>
              <p>Consider retaking this quiz or trying the same topic at a lower difficulty.</p>
            </>
          )}
          {percentage < 60 && (
            <>
              <p>Keep practicing. This topic needs more review.</p>
              <p>Focus on understanding the concepts and try again.</p>
            </>
          )}
        </div>
      </div>

      {/* Detailed Review */}
      {reviewRows.length > 0 && (
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

      {/* Action Buttons */}
      <div className="space-y-2.5">
        <button
          onClick={handleExportGoogleForm}
          disabled={exporting || !quizMcqs || quizMcqs.length === 0}
          className="w-full h-10 border border-zinc-200 text-zinc-800 rounded-lg hover:bg-zinc-100/70 transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {exporting ? 'Exporting...' : 'Export to Google Form'}
        </button>

        {exportLink && (
          <div className="border border-zinc-200/70 rounded-xl p-3 flex items-center gap-2">
            <input
              value={exportLink}
              readOnly
              className="input h-9 flex-1"
            />

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
          onClick={() => router.push('/dashboard/quiz-adaptive')}
          className="w-full h-10 bg-zinc-900 text-white rounded-lg hover:bg-zinc-800 transition-colors text-sm font-medium"
        >
          Take Another Adaptive Quiz
        </button>
        <button
          onClick={() => router.push('/dashboard/quiz-custom')}
          className="w-full h-10 bg-zinc-900 text-white rounded-lg hover:bg-zinc-800 transition-colors text-sm font-medium"
        >
          Create Custom Quiz
        </button>
        <button
          onClick={() => router.push('/dashboard')}
          className="w-full h-10 bg-white border border-zinc-200 text-zinc-700 rounded-lg hover:bg-zinc-100/70 transition-colors text-sm font-medium"
        >
          ← Back to Dashboard
        </button>
      </div>
    </div>
  );
}
