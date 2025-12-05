import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { authAPI } from '../services/api';
import './Login.css';

export const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const [isRegister, setIsRegister] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // Check for email confirmation success/error in URL
  useEffect(() => {
    const confirmed = searchParams.get('confirmed');
    const token = searchParams.get('token_hash');
    const type = searchParams.get('type');
    
    if (confirmed === 'true' || searchParams.get('success') === 'true') {
      setSuccess('Email confirmed successfully! You can now log in.');
      setError('');
    } else if (searchParams.get('error')) {
      setError(`Confirmation failed: ${searchParams.get('error')}`);
    } else if (token && type) {
      // Handle Supabase email confirmation token from URL
      // This happens when user clicks confirmation link
      setSuccess('Processing email confirmation...');
      // The backend endpoint will handle this
    }
  }, [searchParams]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = isRegister
        ? await authAPI.register(email, password)
        : await authAPI.login(email, password);

      // Handle email confirmation case
      if (response && (response as any).requires_confirmation) {
        setError((response as any).message || 'Please check your email to confirm your account.');
        return;
      }

      login(response.access_token, response.user);
      navigate('/notes');
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <h1>{isRegister ? 'Create Account' : 'Welcome Back'}</h1>
        <p className="subtitle">
          {isRegister
            ? 'Sign up to start taking notes'
            : 'Sign in to your account'}
        </p>

        {error && <div className="error-message">{error}</div>}
        {success && <div className="success-message">{success}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="you@example.com"
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="••••••••"
              minLength={6}
            />
          </div>

          <button type="submit" disabled={loading} className="submit-button">
            {loading ? 'Loading...' : isRegister ? 'Sign Up' : 'Sign In'}
          </button>
        </form>

        <p className="switch-mode">
          {isRegister ? 'Already have an account? ' : "Don't have an account? "}
          <button
            type="button"
            onClick={() => {
              setIsRegister(!isRegister);
              setError('');
            }}
            className="link-button"
          >
            {isRegister ? 'Sign In' : 'Sign Up'}
          </button>
        </p>
      </div>
    </div>
  );
};

