import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { GoogleLogin } from '@react-oauth/google';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';

const Login = () => {
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleGoogleSuccess = async (credentialResponse) => {
    setError('');
    setIsLoading(true);
    
    try {
      const resp = await axios.post(`${API_BASE_URL}/api/auth/google`, {
        credential: credentialResponse.credential
      });
      
      login(resp.data.access_token);
      navigate('/dashboard'); // Direct to dashboard if already setup or logic handles it
    } catch (err) {
      console.error("Auth failed:", err);
      setError(err.response?.data?.detail || 'Authentication failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleError = () => {
    setError('Google Login failed. Please check your credentials or network.');
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[70vh] animate-in fade-in slide-in-from-bottom-8 duration-1000">
      <div className="w-full max-w-md bg-surface_container_low p-8 rounded-3xl border border-outline_variant shadow-xl backdrop-blur-sm">
        <div className="text-center mb-10">
          <h1 className="text-4xl font-display font-bold text-on_background tracking-tight">Welcome</h1>
          <p className="text-on_surface_variant mt-2 text-sm">Sign in with your Google account to manage assignments</p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-error_container text-on_error_container rounded-xl text-sm font-medium border border-error/20 flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {error}
          </div>
        )}

        <div className="flex flex-col items-center gap-4 py-4">
          <div className="scale-110 hover:scale-115 transition-transform duration-300">
            <GoogleLogin
               onSuccess={handleGoogleSuccess}
               onError={handleGoogleError}
               theme="filled_blue"
               shape="pill"
               size="large"
               text="continue_with"
               useOneTap
            />
          </div>
          
          {isLoading && (
            <div className="flex items-center gap-2 text-primary font-medium animate-pulse mt-2">
              <div className="w-2 h-2 bg-primary rounded-full animate-bounce" />
              <div className="w-2 h-2 bg-primary rounded-full animate-bounce [animation-delay:0.2s]" />
              <div className="w-2 h-2 bg-primary rounded-full animate-bounce [animation-delay:0.4s]" />
              <span>Verifying account...</span>
            </div>
          )}
        </div>

        <div className="mt-8 pt-8 border-t border-outline_variant/30">
          <p className="text-center text-[10px] text-on_surface_variant/60 leading-relaxed">
            By signing in, you agree to our Terms of Service and Privacy Policy. 
            All your data is securely handled and isolated.
          </p>
        </div>
      </div>
      
      <p className="mt-8 text-[10px] text-on_surface_variant/40 uppercase tracking-[0.2em] font-bold">
        PiEMR Automation Platform 1.0
      </p>
    </div>
  );
};

export default Login;
