'use client';

import { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { useAuthStore } from '@/store/store';
import { settingsAPI } from '@/lib/api';

const OLLAMA_DEFAULT_URL = 'http://localhost:11434/api/generate';

const OLLAMA_MODELS = [
  { value: 'llama3.1:8b', label: 'Llama 3.1 8B' },
  { value: 'llama3.1:70b', label: 'Llama 3.1 70B' },
  { value: 'llama2:7b', label: 'Llama 2 7B' },
  { value: 'llama2:13b', label: 'Llama 2 13B' },
  { value: 'mistral:7b', label: 'Mistral 7B' },
  { value: 'codellama:7b', label: 'Code Llama 7B' },
];

const EXTERNAL_PROVIDER_CONFIG = {
  groq: {
    label: 'Groq',
    apiUrl: 'https://api.groq.com/openai/v1/chat/completions',
    models: [
      { value: 'llama-3.1-8b-instant', label: 'Llama 3.1 8B Instant' },
      { value: 'llama-3.3-70b-versatile', label: 'Llama 3.3 70B Versatile' },
      { value: 'mixtral-8x7b-32768', label: 'Mixtral 8x7B' },
    ],
  },
  gemini_compat: {
    label: 'Google Gemini (OpenAI-compatible)',
    apiUrl: 'https://generativelanguage.googleapis.com/v1beta/openai/chat/completions',
    models: [
      { value: 'gemini-2.5-flash', label: 'Gemini 2.5 Flash' },
      { value: 'gemini-2.5-flash-lite', label: 'Gemini 2.5 Flash-Lite' },
      { value: 'gemini-2.5-pro', label: 'Gemini 2.5 Pro' },
    ],
  },
} as const;

type ExternalProvider = keyof typeof EXTERNAL_PROVIDER_CONFIG;

const detectExternalProvider = (apiUrl: string): ExternalProvider => {
  const url = (apiUrl || '').toLowerCase();
  if (url.includes('api.groq.com')) return 'groq';
  if (url.includes('generativelanguage.googleapis.com')) return 'gemini_compat';
  return 'groq';
};

export default function SettingsPage() {
  const { user, isLoggedIn } = useAuthStore();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [uploadingCredentials, setUploadingCredentials] = useState(false);
  const [credentialsFile, setCredentialsFile] = useState<File | null>(null);
  const [settings, setSettings] = useState({
    ai_source: 'ollama',
    ai_model: 'llama3.1:8b',
    ai_api_url: OLLAMA_DEFAULT_URL,
    ai_api_key: '',
  });
  const [externalProvider, setExternalProvider] = useState<ExternalProvider>('groq');
  const externalModels = EXTERNAL_PROVIDER_CONFIG[externalProvider].models;
  const externalModelExists = externalModels.some((model) => model.value === settings.ai_model);

  useEffect(() => {
    if (!isLoggedIn || !user) return;

    const loadSettings = async () => {
      try {
        const response = await settingsAPI.getAISettings();
        if (response.success) {
          const loadedSettings = response.settings;
          setSettings(loadedSettings);

          if (loadedSettings.ai_source !== 'ollama') {
            setExternalProvider(detectExternalProvider(loadedSettings.ai_api_url));
          }
        }
      } catch (error: any) {
        console.error('Failed to load settings');
        // Use defaults if loading fails
      } finally {
        setLoading(false);
      }
    };

    loadSettings();
  }, [isLoggedIn, user]);

  const handleSave = async () => {
    setSaving(true);
    try {
      const response = await settingsAPI.saveAISettings(
        settings.ai_source,
        settings.ai_model,
        settings.ai_api_url,
        settings.ai_api_key
      );

      if (response.success) {
        toast.success('Settings saved successfully!');
      } else {
        toast.error('Failed to save settings');
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Error saving settings');
    } finally {
      setSaving(false);
    }
  };

  const handleInputChange = (field: string, value: string) => {
    if (field === 'ai_source') {
      if (value === 'ollama') {
        setSettings(prev => ({
          ...prev,
          ai_source: 'ollama',
          ai_model: OLLAMA_MODELS[0].value,
          ai_api_url: OLLAMA_DEFAULT_URL,
          ai_api_key: '',
        }));
        return;
      }

      const providerConfig = EXTERNAL_PROVIDER_CONFIG[externalProvider];
      setSettings(prev => ({
        ...prev,
        ai_source: 'openai',
        ai_model: providerConfig.models[0].value,
        ai_api_url: providerConfig.apiUrl,
      }));
      return;
    }

    setSettings(prev => ({ ...prev, [field]: value }));
  };

  const handleExternalProviderChange = (provider: ExternalProvider) => {
    setExternalProvider(provider);
    const providerConfig = EXTERNAL_PROVIDER_CONFIG[provider];
    setSettings(prev => ({
      ...prev,
      ai_source: 'openai',
      ai_model: providerConfig.models[0].value,
      ai_api_url: providerConfig.apiUrl,
    }));
  };

  const handleUploadCredentials = async () => {
    if (!credentialsFile) {
      toast.error('Please select a credentials.json file first');
      return;
    }

    if (!credentialsFile.name.toLowerCase().endsWith('.json')) {
      toast.error('Please upload a valid JSON file');
      return;
    }

    setUploadingCredentials(true);
    try {
      const response = await settingsAPI.uploadCredentials(credentialsFile);
      if (response.success) {
        toast.success('Credentials uploaded successfully');
        setCredentialsFile(null);
      } else {
        toast.error('Failed to upload credentials');
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Error uploading credentials');
    } finally {
      setUploadingCredentials(false);
    }
  };

  if (!isLoggedIn) {
    return <div>Redirecting...</div>;
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="text-center">
          <p className="text-xl text-zinc-600">Loading settings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 mb-1.5">AI Settings</h1>
        <p className="text-sm text-zinc-600">
          Configure your AI model preferences for quiz generation
        </p>
      </div>

      {/* AI Source Selection */}
      <div className="border border-zinc-200/70 rounded-xl p-5">
        <h2 className="text-xl font-semibold text-zinc-900 mb-5">AI Source</h2>

        <div className="space-y-3.5">
          <div className="flex items-center space-x-3.5">
            <input
              type="radio"
              id="ollama"
              name="ai_source"
              value="ollama"
              checked={settings.ai_source === 'ollama'}
              onChange={(e) => handleInputChange('ai_source', e.target.value)}
              className="w-4 h-4 accent-zinc-900"
            />
            <label htmlFor="ollama" className="flex-1">
              <div className="font-medium text-zinc-900 text-sm">Local Ollama</div>
              <div className="text-xs text-zinc-600 mt-0.5">
                Run AI models locally on your machine. Requires Ollama installation.
              </div>
            </label>
          </div>

          <div className="flex items-center space-x-3.5">
            <input
              type="radio"
              id="openai"
              name="ai_source"
              value="openai"
              checked={settings.ai_source === 'openai'}
              onChange={(e) => handleInputChange('ai_source', e.target.value)}
              className="w-4 h-4 accent-zinc-900"
            />
            <label htmlFor="openai" className="flex-1">
              <div className="font-medium text-zinc-900 text-sm">Cloud API</div>
              <div className="text-xs text-zinc-600 mt-0.5">
                Use cloud models via compatible APIs. Requires API key.
              </div>
            </label>
          </div>
        </div>
      </div>

      {/* Model Configuration */}
      <div className="border border-zinc-200/70 rounded-xl p-5">
        <h2 className="text-xl font-semibold text-zinc-900 mb-5">Model Configuration</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Model Selection */}
          <div>
            <label className="block text-sm font-medium text-zinc-700 mb-1.5">
              Model
            </label>
            <select
              value={settings.ai_model}
              onChange={(e) => handleInputChange('ai_model', e.target.value)}
              className="input w-full"
            >
              {settings.ai_source === 'ollama'
                ? OLLAMA_MODELS.map((model) => (
                    <option key={model.value} value={model.value}>
                      {model.label}
                    </option>
                  ))
                : (
                    <>
                      {!externalModelExists && settings.ai_model && (
                        <option value={settings.ai_model}>{settings.ai_model}</option>
                      )}
                      {externalModels.map((model) => (
                        <option key={model.value} value={model.value}>
                          {model.label}
                        </option>
                      ))}
                    </>
                  )}
            </select>
          </div>

          {settings.ai_source !== 'ollama' && (
            <div>
              <label className="block text-sm font-medium text-zinc-700 mb-1.5">
                API Provider
              </label>
              <select
                value={externalProvider}
                onChange={(e) => handleExternalProviderChange(e.target.value as ExternalProvider)}
                className="input w-full"
              >
                {Object.entries(EXTERNAL_PROVIDER_CONFIG).map(([key, provider]) => (
                  <option key={key} value={key}>
                    {provider.label}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        {settings.ai_source !== 'ollama' && (
          <div className="mt-4">
            <label className="block text-sm font-medium text-zinc-700 mb-1.5">
              API URL
            </label>
            <input
              type="text"
              value={settings.ai_api_url}
              readOnly
              className="input w-full bg-zinc-50"
            />
          </div>
        )}

        {/* API Key (only for external APIs) */}
        {settings.ai_source !== 'ollama' && (
          <div className="mt-5">
            <label className="block text-sm font-medium text-zinc-700 mb-1.5">
              API Key
            </label>
            <input
              type="password"
              value={settings.ai_api_key}
              onChange={(e) => handleInputChange('ai_api_key', e.target.value)}
              className="input w-full"
              placeholder="Enter your API key"
            />
            <p className="text-xs text-zinc-500 mt-1.5">
              Your API key is stored locally and never sent to our servers.
            </p>
          </div>
        )}

        <div className="mt-5 pt-4 border-t border-zinc-200/70 flex justify-end">
          <button
            onClick={handleSave}
            disabled={saving}
            className="btn px-5 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>

      {/* Info Section */}
      <div className="border border-zinc-200/70 rounded-xl p-5">
        <h3 className="text-base font-semibold text-zinc-900 mb-2">Setup Instructions</h3>
        <div className="text-zinc-700 space-y-1.5 text-sm">
          <p>
            <strong>For Ollama:</strong> Install from <a href="https://ollama.ai" className="underline" target="_blank" rel="noopener noreferrer">ollama.ai</a>,
            then run <code className="px-1 border border-zinc-200 rounded-md">ollama pull llama3.1:8b</code> and <code className="px-1 border border-zinc-200 rounded-md">ollama serve</code>.
          </p>
          <p>
            <strong>For Cloud APIs:</strong> Pick a provider from the dropdown and use that provider's API key.
            Groq and Gemini usually offer a free tier for testing.
          </p>
        </div>
      </div>

      {/* Google Credentials Upload */}
      <div className="border border-zinc-200/70 rounded-xl p-5">
        <h3 className="text-base font-semibold text-zinc-900 mb-2">Google Forms Credentials</h3>
        <p className="text-sm text-zinc-600 mb-4">
          Upload your Google Forms API credentials.json file to enable quiz export to Google Forms.
        </p>

        <div className="space-y-3">
          <input
            type="file"
            accept=".json,application/json"
            onChange={(e) => setCredentialsFile(e.target.files?.[0] || null)}
            className="input h-10 file:mr-3 file:border-0 file:bg-transparent file:text-sm file:font-medium"
          />

          {credentialsFile && (
            <p className="text-xs text-zinc-600">
              Selected file: <span className="font-medium text-zinc-900">{credentialsFile.name}</span>
            </p>
          )}

          <div className="flex justify-end">
            <button
              onClick={handleUploadCredentials}
              disabled={uploadingCredentials}
              className="btn px-5 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {uploadingCredentials ? 'Uploading...' : 'Upload credentials.json'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
