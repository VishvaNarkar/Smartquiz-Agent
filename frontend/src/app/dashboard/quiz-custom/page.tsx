'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import toast from 'react-hot-toast';
import { quizAPI } from '@/lib/api';
import { useAuthStore } from '@/store/store';
import { useQuizStore } from '@/store/store';

const DIFFICULTIES = ['Easy', 'Medium', 'Hard', 'Expert'];
const MODES = ['topic', 'document'] as const;

export default function CustomQuizPage() {
  const router = useRouter();
  const { user, isLoggedIn } = useAuthStore();
  const { setQuiz } = useQuizStore();
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState<(typeof MODES)[number]>('topic');
  const [selectedTopic, setSelectedTopic] = useState('');
  const [selectedDifficulty, setSelectedDifficulty] = useState('Medium');
  const [numQuestions, setNumQuestions] = useState(5);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  useEffect(() => {
    if (!isLoggedIn || !user) {
      router.push('/');
    }
  }, [isLoggedIn, user, router]);

  const handleGenerateQuiz = async () => {
    if (!user) {
      toast.error('Please login again');
      return;
    }

    if (mode === 'topic' && !selectedTopic.trim()) {
      toast.error('Please enter a topic');
      return;
    }

    if (mode === 'document' && !selectedFile) {
      toast.error('Please choose a document to upload');
      return;
    }

    setLoading(true);
    try {
      const response =
        mode === 'document'
          ? await quizAPI.generateFromDocument(
              user,
              selectedFile as File,
              selectedDifficulty,
              numQuestions,
              selectedTopic.trim() || undefined
            )
          : await quizAPI.generateCustom(
              user,
              selectedTopic,
              selectedDifficulty,
              numQuestions
            );
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
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 mb-1.5">Custom Quiz</h1>
        <p className="text-sm text-zinc-600">
          Create a quiz on any topic or generate one from an uploaded document
        </p>
      </div>

      {/* Quiz Form */}
      <div className="border border-zinc-200/70 rounded-xl p-5">
        {/* Mode Selection */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-zinc-700 mb-2">
            Quiz Source
          </label>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => setMode('topic')}
              className={`h-10 rounded-lg border transition-colors text-sm font-medium ${
                mode === 'topic'
                  ? 'border-zinc-900 bg-zinc-900 text-white'
                  : 'border-zinc-200 text-zinc-700 hover:bg-zinc-100/70'
              }`}
            >
              Topic
            </button>
            <button
              type="button"
              onClick={() => setMode('document')}
              className={`h-10 rounded-lg border transition-colors text-sm font-medium ${
                mode === 'document'
                  ? 'border-zinc-900 bg-zinc-900 text-white'
                  : 'border-zinc-200 text-zinc-700 hover:bg-zinc-100/70'
              }`}
            >
              Document Upload
            </button>
          </div>
        </div>

        {/* Topic Selection */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-zinc-700 mb-2">
            {mode === 'document' ? 'Optional Topic Focus' : 'Enter Topic'}
          </label>
          <input
            type="text"
            value={selectedTopic}
            onChange={(e) => setSelectedTopic(e.target.value)}
            className="input"
            placeholder={
              mode === 'document'
                ? 'Optional: narrow the quiz to a subject within the document'
                : 'Type any topic (e.g., Mathematics, AI, History)'
            }
            maxLength={100}
          />
        </div>

        {mode === 'document' && (
          <div className="mb-6">
            <label className="block text-sm font-medium text-zinc-700 mb-2">
              Upload Document
            </label>
            <input
              type="file"
              accept=".pdf,.ppt,.pptx,.doc,.docx,application/pdf,application/vnd.ms-powerpoint,application/vnd.openxmlformats-officedocument.presentationml.presentation,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
              className="input h-10 file:mr-3 file:border-0 file:bg-transparent file:text-sm file:font-medium"
            />
            <p className="text-xs text-zinc-500 mt-1.5">
              PDF, PPT/PPTX, DOCX, and most DOC files are supported. Files are processed once and not stored.
            </p>
            {selectedFile && (
              <p className="text-xs text-zinc-600 mt-1.5">
                Selected file: <span className="font-medium text-zinc-900">{selectedFile.name}</span>
              </p>
            )}
          </div>
        )}

        {/* Difficulty Selection */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-zinc-700 mb-2">
            Difficulty Level
          </label>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {DIFFICULTIES.map((difficulty) => (
              <button
                key={difficulty}
                type="button"
                onClick={() => setSelectedDifficulty(difficulty)}
                className={`h-10 rounded-lg border transition-colors text-sm font-medium ${
                  selectedDifficulty === difficulty
                    ? 'border-zinc-900 bg-zinc-900 text-white'
                    : 'border-zinc-200 text-zinc-700 hover:bg-zinc-100/70'
                }`}
              >
                {difficulty}
              </button>
            ))}
          </div>
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
          {loading ? 'Generating Quiz...' : mode === 'document' ? 'Start Document Quiz' : 'Start Custom Quiz'}
        </button>
      </div>

      {/* Info Section */}
      <div className="border border-zinc-200/70 rounded-xl p-5">
        <h3 className="text-base font-semibold text-zinc-900 mb-2">Custom Quiz Features</h3>
        <ul className="space-y-1.5 text-zinc-700 text-sm list-disc pl-5">
          <li>Select from multiple academic topics.</li>
          <li>Choose difficulty from Easy to Expert.</li>
          <li>Set quiz length based on your available time.</li>
          <li>Repeat with different settings to practice progressively.</li>
          <li>Upload a document and generate quiz questions from its content.</li>
        </ul>
      </div>
    </div>
  );
}
