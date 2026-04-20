'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import toast from 'react-hot-toast';
import { quizAPI } from '@/lib/api';
import { useAuthStore } from '@/store/store';
import { useQuizStore } from '@/store/store';

export default function AdaptiveQuizPage() {
  const router = useRouter();
  const { user, isLoggedIn } = useAuthStore();
  const { setQuiz } = useQuizStore();
  const [loading, setLoading] = useState(false);
  const [numQuestions, setNumQuestions] = useState(5);

  useEffect(() => {
    if (!isLoggedIn || !user) {
      router.push('/');
    }
  }, [isLoggedIn, user, router]);

  const handleGenerateQuiz = async () => {
    if (!user) return;
    
    setLoading(true);
    try {
      const response = await quizAPI.generateAdaptive(user, numQuestions);
      if (response.success) {
        setQuiz(response.quiz, response.topic, response.difficulty, response.quiz_id);
        toast.success('Quiz generated! Starting quiz...');
        router.push('/dashboard/quiz');
      } else {
        toast.error('Failed to generate quiz');
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Error generating quiz');
    } finally {
      setLoading(false);
    }
  };

  if (!isLoggedIn) {
    return <div>Redirecting...</div>;
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 mb-1.5">Adaptive Quiz</h1>
        <p className="text-sm text-zinc-600">
          Questions tailored to your weak topics
        </p>
      </div>

      {/* Quiz Form */}
      <div className="border border-zinc-200/70 rounded-xl p-5">
        <div className="mb-5">
          <p className="text-sm text-zinc-700 mb-3">
            The adaptive quiz system analyzes your performance across all topics and focuses on areas where you need improvement.
          </p>
        </div>

        {/* Number of Questions */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-zinc-700 mb-2">
            Number of Questions: <span className="font-semibold text-zinc-900">{numQuestions}</span>
          </label>
          <input
            type="range"
            min="3"
            max="20"
            value={numQuestions}
            onChange={(e) => setNumQuestions(Number(e.target.value))}
            className="w-full h-2 bg-zinc-300 rounded appearance-none cursor-pointer"
          />
          <div className="flex justify-between text-[11px] text-zinc-500 mt-1.5">
            <span>3</span>
            <span>20</span>
          </div>
        </div>

        {/* Start Button */}
        <button
          onClick={handleGenerateQuiz}
          disabled={loading}
          className="w-full h-10 bg-zinc-900 text-white rounded-lg hover:bg-zinc-800 transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Generating Quiz...' : 'Start Adaptive Quiz'}
        </button>
      </div>

      {/* Info Section */}
      <div className="border border-zinc-200/70 rounded-xl p-5">
        <h3 className="text-base font-semibold text-zinc-900 mb-2">How Adaptive Quizzes Work</h3>
        <ul className="space-y-1.5 text-zinc-700 text-sm list-disc pl-5">
          <li>The system analyzes your quiz history to identify weak topics.</li>
          <li>Questions are generated to target those weak areas.</li>
          <li>Each completed quiz improves future recommendations.</li>
          <li>Take at least one quiz first for better adaptive results.</li>
        </ul>
      </div>
    </div>
  );
}
