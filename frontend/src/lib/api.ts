import axios, { AxiosInstance } from 'axios';
import toast from 'react-hot-toast';
import { useAuthStore } from '@/store/store';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const apiClient: AxiosInstance = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

const TOKEN_REFRESH_WINDOW_SECONDS = 5 * 60;
const SESSION_EXPIRED_FLAG = 'session-expired-toast-shown';
let refreshPromise: Promise<string | null> | null = null;

const getPersistedAuthToken = (): string | null => {
  if (typeof window === 'undefined') return null;
  const rawState = window.localStorage.getItem('auth-store');
  if (!rawState) return null;

  try {
    const parsed = JSON.parse(rawState);
    return parsed?.state?.token || null;
  } catch {
    return null;
  }
};

const getActiveAuthToken = (): string | null => {
  const storeToken = useAuthStore.getState().token;
  return storeToken || getPersistedAuthToken();
};

const decodeTokenPayload = (token: string): { exp?: number } | null => {
  try {
    const parts = token.split('.');
    if (parts.length !== 2) return null;
    const payload = parts[0];
    const normalized = payload.replace(/-/g, '+').replace(/_/g, '/');
    const padded = normalized + '='.repeat((4 - (normalized.length % 4)) % 4);
    const parsed = JSON.parse(window.atob(padded));
    return parsed;
  } catch {
    return null;
  }
};

const getTokenExpiryEpoch = (token: string): number | null => {
  if (typeof window === 'undefined') return null;
  const payload = decodeTokenPayload(token);
  if (!payload?.exp || typeof payload.exp !== 'number') return null;
  return payload.exp;
};

const isTokenExpired = (token: string): boolean => {
  const exp = getTokenExpiryEpoch(token);
  if (!exp) return false;
  return exp <= Math.floor(Date.now() / 1000);
};

const shouldRefreshToken = (token: string): boolean => {
  const exp = getTokenExpiryEpoch(token);
  if (!exp) return false;
  const now = Math.floor(Date.now() / 1000);
  return exp - now <= TOKEN_REFRESH_WINDOW_SECONDS;
};

const handleSessionExpired = () => {
  if (typeof window === 'undefined') return;

  useAuthStore.getState().logout();

  if (!window.sessionStorage.getItem(SESSION_EXPIRED_FLAG)) {
    window.sessionStorage.setItem(SESSION_EXPIRED_FLAG, '1');
    toast.error('Session expired, please login.');
  }

  if (window.location.pathname !== '/') {
    window.location.assign('/');
  }
};

const refreshAccessToken = async (currentToken: string): Promise<string | null> => {
  // Deduplicate refresh calls when multiple requests race near token expiry.
  if (!refreshPromise) {
    refreshPromise = axios
      .post(
        `${API_URL}/auth/refresh`,
        {},
        {
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${currentToken}`,
          },
        }
      )
      .then((response) => {
        const refreshedToken = response?.data?.access_token || null;
        if (!refreshedToken) return null;
        useAuthStore.getState().setToken(refreshedToken);
        return refreshedToken;
      })
      .catch(() => {
        handleSessionExpired();
        return null;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }

  return refreshPromise;
};

apiClient.interceptors.request.use(async (config) => {
  // Attach token for protected endpoints and proactively refresh if close to expiry.
  let token = getActiveAuthToken();
  if (!token) return config;

  const requestUrl = config.url || '';
  const isAuthRequest = requestUrl.includes('/auth/login') || requestUrl.includes('/auth/register') || requestUrl.includes('/auth/refresh');

  if (isTokenExpired(token)) {
    handleSessionExpired();
    return Promise.reject(new Error('Session expired'));
  }

  if (!isAuthRequest && shouldRefreshToken(token)) {
    const refreshedToken = await refreshAccessToken(token);
    if (refreshedToken) {
      token = refreshedToken;
    }
  }

  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Any 401 outside auth routes triggers a controlled logout + redirect.
    const status = error?.response?.status;
    const requestUrl = error?.config?.url || '';
    const isAuthRequest = requestUrl.includes('/auth/login') || requestUrl.includes('/auth/register') || requestUrl.includes('/auth/refresh');

    if (status === 401 && !isAuthRequest) {
      handleSessionExpired();
    }

    return Promise.reject(error);
  }
);

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  password: string;
  email?: string;
}

export interface AuthResponse {
  success: boolean;
  message: string;
  user?: string;
  access_token?: string;
  token_type?: string;
}

export const authAPI = {
  login: async (credentials: LoginRequest): Promise<AuthResponse> => {
    const response = await apiClient.post('/auth/login', credentials);
    return response.data;
  },

  register: async (data: RegisterRequest): Promise<AuthResponse> => {
    const response = await apiClient.post('/auth/register', data);
    return response.data;
  },
};

export interface QuizResponse {
  success: boolean;
  quiz_id?: string;
  quiz: any[];
  topic: string;
  difficulty: string;
}

export const quizAPI = {
  generateCustom: async (
    username: string,
    topic: string,
    difficulty: string,
    numQuestions: number = 5
  ): Promise<QuizResponse> => {
    const response = await apiClient.post('/quiz/custom', {
      username,
      topic,
      difficulty,
      num_questions: numQuestions,
    });
    return response.data;
  },

  generateAdaptive: async (
    username: string,
    numQuestions: number = 5
  ): Promise<QuizResponse> => {
    const response = await apiClient.post('/quiz/adaptive', {
      username,
      num_questions: numQuestions,
    });
    return response.data;
  },

  submit: async (
    username: string,
    topic: string,
    difficulty: string,
    questions: any[],
    answers: string[],
    quizId?: string
  ) => {
    const response = await apiClient.post('/quiz/submit', {
      username,
      topic,
      difficulty,
      questions,
      answers,
      quiz_id: quizId,
    });
    return response.data;
  },

  exportToGoogleForm: async (username: string, mcqs: any[], topic?: string) => {
    const response = await apiClient.post('/quiz/export-google-form', {
      username,
      mcqs,
      topic,
    });
    return response.data;
  },
};

export interface Analytics {
  total_quizzes: number;
  average_score: number;
  weak_topics: string[];
  recent_quizzes: any[];
  topic_performance: Record<string, any>;
}

export interface StoredQuiz {
  id: string;
  topic: string;
  difficulty: string;
  num_questions: number;
  score?: number;
  timestamp: string;
  mcqs?: any[];
  submitted_answers?: string[];
  results?: Array<{
    question: string;
    correct: string;
    your_answer: string;
    status: string;
  }>;
  submitted_at?: string;
}

export interface StoredQuizzesResponse {
  success: boolean;
  quizzes: StoredQuiz[];
}

export const analyticsAPI = {
  getAnalytics: async (username: string) => {
    const response = await apiClient.get(`/user/${username}/analytics`);
    return response.data;
  },

  getRecentQuizzes: async (username: string): Promise<StoredQuizzesResponse> => {
    const response = await apiClient.get(`/user/${username}/quizzes`);
    return response.data;
  },

  getQuizById: async (username: string, quizId: string) => {
    const response = await apiClient.get(`/user/${username}/quizzes/${quizId}`);
    return response.data;
  },

  deleteQuiz: async (username: string, quizId: string) => {
    try {
      const response = await apiClient.delete('/user/quiz', {
        data: {
          username,
          quiz_id: quizId,
        },
      });
      return response.data;
    } catch (error: any) {
      if (error?.response?.status === 404 || error?.response?.status === 405) {
        const fallback = await apiClient.post('/user/quiz/delete', {
          username,
          quiz_id: quizId,
        });
        return fallback.data;
      }
      throw error;
    }
  },
};

export const settingsAPI = {
  getAISettings: async () => {
    const response = await apiClient.get('/settings/ai');
    return response.data;
  },

  saveAISettings: async (
    aiSource: string,
    aiModel: string,
    aiApiUrl: string,
    aiApiKey: string
  ) => {
    const response = await apiClient.post('/settings/ai', {
      ai_source: aiSource,
      ai_model: aiModel,
      ai_api_url: aiApiUrl,
      ai_api_key: aiApiKey,
    });
    return response.data;
  },

  uploadCredentials: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post('/credentials/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};

export default apiClient;
