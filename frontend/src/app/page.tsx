'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import toast from 'react-hot-toast';
import { authAPI } from '@/lib/api';
import { useAuthStore } from '@/store/store';
import { Eye, EyeOff } from 'lucide-react';

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuthStore();
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [email, setEmail] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (isLogin) {
        const response = await authAPI.login({ username, password });
        if (response.success) {
          if (!response.access_token) {
            toast.error('Login succeeded but no access token was received.');
            return;
          }
          login(response.user || username, response.access_token);
          if (typeof window !== 'undefined') {
            window.sessionStorage.removeItem('session-expired-toast-shown');
          }
          toast.success('Login successful!');
          router.push('/dashboard');
        } else {
          toast.error(response.message || 'Login failed');
        }
      } else {
        const response = await authAPI.register({ username, password, email }); 
        if (response.success) {
          toast.success('Registration successful! Please login.');
          setIsLogin(true);
          setPassword('');
          setEmail('');
        } else {
          toast.error(response.message || 'Registration failed');
        }
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center bg-white px-4 pt-10 md:pt-14">
      <div className="w-full max-w-xl">
        <div className="mb-6">
          <h1 className="text-3xl md:text-4xl font-semibold tracking-tight text-zinc-900">SmartQuiz</h1>
        </div>

        <div className="border-b border-zinc-200/70 mb-6 flex gap-5">
          <button
            type="button"
            onClick={() => {
              setIsLogin(true);
              setPassword('');
              setEmail('');
            }}
            className={"interactive-soft pb-2.5 px-1 text-sm font-medium " + (isLogin ? "text-zinc-900 border-b-2 border-zinc-900" : "text-zinc-500 hover:text-zinc-700 border-b-2 border-transparent")}
          >
            Login
          </button>
          <button
            type="button"
            onClick={() => {
              setIsLogin(false);
              setPassword('');
              setEmail('');
            }}
            className={"interactive-soft pb-2.5 px-1 text-sm font-medium " + (!isLogin ? "text-zinc-900 border-b-2 border-zinc-900" : "text-zinc-500 hover:text-zinc-700 border-b-2 border-transparent")}
          >
            Register
          </button>
        </div>

        <h2 className="text-2xl font-semibold tracking-tight text-zinc-900 mb-5">
          {isLogin ? 'Login' : 'Register'}
        </h2>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-zinc-700 mb-2">
              Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="input"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-zinc-700 mb-2">
              Password
            </label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input pr-11"
                required
              />
              <span className="tooltip-wrap absolute right-3 top-1/2 -translate-y-1/2">
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="interactive-soft text-zinc-500 hover:text-zinc-900 rounded-md p-1"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
                <span className="tooltip-bubble">
                  {showPassword ? 'Hide password' : 'Show password'}
                </span>
              </span>
            </div>
          </div>

          {!isLogin && (
            <div>
              <label className="block text-sm font-medium text-zinc-700 mb-2">
                Email (optional)
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input"
              />
            </div>
          )}

          <div className="pt-1">
            <button
              type="submit"
              disabled={loading}
              className="btn px-5 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Please wait...' : isLogin ? 'Login' : 'Register'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
