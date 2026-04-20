import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface AuthState {
  user: string | null;
  token: string | null;
  isLoggedIn: boolean;
  hasHydrated: boolean;
  setHasHydrated: (state: boolean) => void;
  login: (username: string, token: string) => void;
  setToken: (token: string | null) => void;
  logout: () => void;
}

// Persisted auth/session state used by route guards and API interceptors.
export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isLoggedIn: false,
      hasHydrated: false,
      setHasHydrated: (state: boolean) => set({ hasHydrated: state }),
      login: (username: string, token: string) => set({ user: username, token, isLoggedIn: true }),
      setToken: (token: string | null) => set({ token, isLoggedIn: Boolean(token) }),
      logout: () => set({ user: null, token: null, isLoggedIn: false }),
    }),
    {
      name: 'auth-store',
      onRehydrateStorage: () => (state) => {
        state?.setHasHydrated(true);
      },
    }
  )
);

export interface UIState {
  currentPage: string;
  setCurrentPage: (page: string) => void;
  loading: boolean;
  setLoading: (loading: boolean) => void;
  error: string | null;
  setError: (error: string | null) => void;
}

export const useUIStore = create<UIState>((set) => ({
  currentPage: 'login',
  setCurrentPage: (page: string) => set({ currentPage: page }),
  loading: false,
  setLoading: (loading: boolean) => set({ loading }),
  error: null,
  setError: (error: string | null) => set({ error }),
}));

export interface QuizState {
  currentQuiz: any[] | null;
  currentTopic: string;
  currentDifficulty: string;
  currentQuizId: string | null;
  setQuiz: (quiz: any[], topic: string, difficulty: string, quizId?: string) => void;
  clearQuiz: () => void;
}

// In-memory quiz-taking session state.
export const useQuizStore = create<QuizState>((set) => ({
  currentQuiz: null,
  currentTopic: '',
  currentDifficulty: '',
  currentQuizId: null,
  setQuiz: (quiz, topic, difficulty, quizId) =>
    set({ currentQuiz: quiz, currentTopic: topic, currentDifficulty: difficulty, currentQuizId: quizId || null }),
  clearQuiz: () =>
    set({ currentQuiz: null, currentTopic: '', currentDifficulty: '', currentQuizId: null }),
}));
