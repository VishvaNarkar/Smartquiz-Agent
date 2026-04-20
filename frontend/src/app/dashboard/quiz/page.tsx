'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import toast from 'react-hot-toast';
import { quizAPI } from '@/lib/api';
import { useAuthStore } from '@/store/store';
import { useQuizStore } from '@/store/store';

export default function QuizPage() {
  const router = useRouter();
  const { user, isLoggedIn } = useAuthStore();
  const { currentQuiz, currentTopic, currentDifficulty, currentQuizId } = useQuizStore();
  const [currentQuestionIdx, setCurrentQuestionIdx] = useState(0);
  const [answers, setAnswers] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [timeLeft, setTimeLeft] = useState(300); // 5 minutes

  useEffect(() => {
    if (!isLoggedIn || !user) {
      router.push('/');
      return;
    }

    if (!currentQuiz || currentQuiz.length === 0) {
      toast.error('No quiz loaded. Please generate a quiz first.');
      router.push('/dashboard');
      return;
    }

    setAnswers(new Array(currentQuiz.length).fill(''));
  }, [isLoggedIn, user, currentQuiz, router]);

  // Timer
  useEffect(() => {
    if (timeLeft <= 0) {
      handleSubmitQuiz();
      return;
    }

    const timer = setInterval(() => {
      setTimeLeft((prev) => prev - 1);
    }, 1000);

    return () => clearInterval(timer);
  }, [timeLeft]);

  if (!isLoggedIn || !currentQuiz) {
    return <div>Loading...</div>;
  }

  const currentQuestion = currentQuiz[currentQuestionIdx];
  const progress = ((currentQuestionIdx + 1) / currentQuiz.length) * 100;
  const timeMinutes = Math.floor(timeLeft / 60);
  const timeSeconds = timeLeft % 60;

  const handleSelectAnswer = (optionIndex: number) => {
    const newAnswers = [...answers];
    newAnswers[currentQuestionIdx] = optionIndex.toString();
    setAnswers(newAnswers);
  };

  const handleNext = () => {
    if (currentQuestionIdx < currentQuiz.length - 1) {
      setCurrentQuestionIdx(currentQuestionIdx + 1);
    }
  };

  const handlePrevious = () => {
    if (currentQuestionIdx > 0) {
      setCurrentQuestionIdx(currentQuestionIdx - 1);
    }
  };

  const handleSubmitQuiz = async () => {
    if (!user) return;

    setLoading(true);
    try {
      const answersAsText = currentQuiz.map((question: any, idx: number) => {
        const selectedIndex = answers[idx];
        if (selectedIndex === '' || selectedIndex === undefined) {
          return '';
        }

        const optionIdx = Number(selectedIndex);
        if (Number.isNaN(optionIdx) || !question?.options?.[optionIdx]) {
          return '';
        }

        return String(question.options[optionIdx]);
      });

      const response = await quizAPI.submit(
        user,
        currentTopic,
        currentDifficulty,
        currentQuiz,
        answersAsText,
        currentQuizId || undefined
      );

      if (response.success) {
        toast.success('Quiz submitted!');
        const params = new URLSearchParams({
          score: String(response.score),
          total: String(currentQuiz.length),
          topic: currentTopic,
        });
        if (currentQuizId) {
          params.set('quizId', currentQuizId);
        }
        router.push(`/dashboard/results?${params.toString()}`);
      } else {
        toast.error('Failed to submit quiz');
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Error submitting quiz');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="border border-zinc-200/70 rounded-xl overflow-hidden">
        {/* Header with Progress */}
        <div className="p-4 md:p-5 border-b border-zinc-200/70 bg-white">
          <div className="flex flex-col gap-3 sm:flex-row sm:justify-between sm:items-center mb-3">
            <div>
              <h1 className="text-xl font-semibold tracking-tight text-zinc-900">
                {currentTopic} - {currentDifficulty}
              </h1>
              <p className="text-sm text-zinc-600">
                Question {currentQuestionIdx + 1} of {currentQuiz.length}
              </p>
            </div>
            <div className="text-left sm:text-right">
              <p className="text-xs text-zinc-600">Time Left</p>
              <p className="text-2xl font-semibold text-zinc-900">
                {timeMinutes}:{timeSeconds.toString().padStart(2, '0')}
              </p>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="w-full bg-zinc-200 rounded-full h-2">
            <div
              className="bg-zinc-900 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
        </div>

        {/* Question Content */}
        <div className="p-4 md:p-6">
          {/* Question */}
          <div className="mb-6">
            <h2 className="text-lg md:text-xl font-semibold text-zinc-900 mb-4 leading-relaxed">
              {currentQuestion.question}
            </h2>

            {/* Options */}
            <div className="space-y-2.5">
              {currentQuestion.options.map((option: string, idx: number) => (
                <button
                  key={idx}
                  onClick={() => handleSelectAnswer(idx)}
                  className={`w-full text-left p-3 rounded-lg border transition-colors ${
                    answers[currentQuestionIdx] === idx.toString()
                      ? 'border-zinc-900 bg-zinc-100/80'
                      : 'border-zinc-200 hover:bg-zinc-50'
                  }`}
                >
                  <div className="flex items-center">
                    <div
                      className={`w-5 h-5 rounded-full border mr-3 flex items-center justify-center transition-colors ${
                        answers[currentQuestionIdx] === idx.toString()
                          ? 'border-zinc-900 bg-zinc-900'
                          : 'border-zinc-300'
                      }`}
                    >
                      {answers[currentQuestionIdx] === idx.toString() && (
                        <span className="text-white text-[10px]">✓</span>
                      )}
                    </div>
                    <span className="text-sm text-zinc-700">{option}</span>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Navigation */}
          <div className="flex flex-col gap-3 md:flex-row md:justify-between md:items-center pt-4 border-t border-zinc-200/70">
            <button
              onClick={handlePrevious}
              disabled={currentQuestionIdx === 0}
              className="h-9 px-4 border border-zinc-200 rounded-lg hover:bg-zinc-100/70 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm font-medium"
            >
              ← Previous
            </button>

            {/* Question Navigator */}
            <div className="flex flex-wrap gap-1.5 justify-center max-w-md">
              {currentQuiz.map((_, idx) => (
                <button
                  key={idx}
                  onClick={() => setCurrentQuestionIdx(idx)}
                  className={`w-8 h-8 rounded-full text-xs font-medium transition-colors ${
                    idx === currentQuestionIdx
                      ? 'bg-zinc-900 text-white'
                      : answers[idx]
                      ? 'bg-zinc-700 text-white'
                      : 'bg-zinc-200 text-zinc-700 hover:bg-zinc-300'
                  }`}
                >
                  {idx + 1}
                </button>
              ))}
            </div>

            {currentQuestionIdx === currentQuiz.length - 1 ? (
              <button
                onClick={handleSubmitQuiz}
                disabled={loading}
                className="h-9 px-4 bg-zinc-900 text-white rounded-lg hover:bg-zinc-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm font-medium"
              >
                {loading ? 'Submitting...' : 'Submit Quiz'}
              </button>
            ) : (
              <button
                onClick={handleNext}
                className="h-9 px-4 bg-zinc-900 text-white rounded-lg hover:bg-zinc-800 transition-colors text-sm font-medium"
              >
                Next →
              </button>
            )}
          </div>
        </div>

        {/* Answer Status */}
        <div className="px-4 md:px-6 py-3 border-t border-zinc-200/70">
          <div className="text-center text-xs text-zinc-600">
            <p>Answered: <span className="font-semibold text-zinc-900">{answers.filter((a) => a).length}</span>/{currentQuiz.length}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
