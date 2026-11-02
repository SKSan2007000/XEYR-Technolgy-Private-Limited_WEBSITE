import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Lock, User, Eye, EyeOff, ShieldCheck, ArrowLeft, Loader2 } from 'lucide-react';

export const LoginView: React.FC = () => {
  const { login, authMessage, setAuthMessage } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password) {
      setError('Please enter both username and password.');
      return;
    }
    setError(null);
    setAuthMessage(null);
    setIsSubmitting(true);
    try {
      await login({ username: username.trim(), password });
    } catch (err: any) {
      setError(err.message || 'Invalid administrator credentials. Access denied.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'radial-gradient(circle at 50% 10%, #0d214d 0%, #04091a 100%)',
      padding: '24px',
      position: 'relative'
    }}>
      {/* Return to website link */}
      <a
        href="http://127.0.0.1:8000/"
        style={{
          position: 'absolute',
          top: '28px',
          left: '28px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          color: '#94a3b8',
          textDecoration: 'none',
          fontSize: '0.88rem',
          fontWeight: 600,
          background: 'rgba(255, 255, 255, 0.05)',
          padding: '8px 16px',
          borderRadius: '99px',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          backdropFilter: 'blur(8px)',
          transition: 'all 0.2s'
        }}
      >
        <ArrowLeft size={16} /> Public Website
      </a>

      <div style={{
        width: 'min(440px, 94vw)',
        background: '#07132e',
        border: '1px solid rgba(95, 159, 255, 0.18)',
        borderRadius: '24px',
        padding: '40px 36px',
        boxShadow: '0 25px 80px rgba(0, 0, 0, 0.6), 0 0 40px rgba(20, 101, 244, 0.15)',
        display: 'flex',
        flexDirection: 'column',
        gap: '24px'
      }}>
        {/* Brand Header */}
        <div style={{ textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '10px' }}>
          <img
            src="/xeyr-symbol.png"
            alt="XEYR Technologies"
            style={{ width: '56px', height: '56px', objectFit: 'contain' }}
          />
          <div>
            <h1 style={{
              fontFamily: "'Manrope', sans-serif",
              fontSize: '1.45rem',
              fontWeight: 800,
              color: '#ffffff',
              letterSpacing: '0.04em'
            }}>
              XEYR Technologies
            </h1>
            <p style={{
              fontSize: '0.74rem',
              color: '#38bdf8',
              letterSpacing: '0.14em',
              fontWeight: 700,
              textTransform: 'uppercase',
              marginTop: '2px'
            }}>
              Enterprise Executive OS
            </p>
          </div>
          <p style={{ fontSize: '0.84rem', color: '#94a3b8', marginTop: '4px', lineHeight: 1.4 }}>
            Sign in with authorized administrator credentials to access executive controls and business telemetry.
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <div style={{
            background: 'rgba(239, 68, 68, 0.12)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: '10px',
            padding: '12px 14px',
            color: '#f87171',
            fontSize: '0.84rem',
            lineHeight: 1.4
          }}>
            {error}
          </div>
        )}

        {/* Informational Message (e.g. Session Expired or Sign Out) */}
        {authMessage && !error && (
          <div style={{
            background: 'rgba(56, 189, 248, 0.1)',
            border: '1px solid rgba(56, 189, 248, 0.3)',
            borderRadius: '10px',
            padding: '12px 14px',
            color: '#38bdf8',
            fontSize: '0.84rem',
            lineHeight: 1.4
          }}>
            {authMessage}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
          <div className="form-group" style={{ margin: 0 }}>
            <label className="form-label" style={{ color: '#cbd5e1', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <User size={14} color="#38bdf8" /> Administrator Username / ID
            </label>
            <input
              type="text"
              className="form-input"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="e.g. admin"
              required
              autoComplete="username"
              style={{
                background: 'rgba(4, 9, 26, 0.7)',
                color: '#ffffff',
                borderColor: 'rgba(255, 255, 255, 0.12)'
              }}
            />
          </div>

          <div className="form-group" style={{ margin: 0 }}>
            <label className="form-label" style={{ color: '#cbd5e1', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Lock size={14} color="#38bdf8" /> Secure Password
            </label>
            <div style={{ position: 'relative' }}>
              <input
                type={showPassword ? 'text' : 'password'}
                className="form-input"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                required
                autoComplete="current-password"
                style={{
                  background: 'rgba(4, 9, 26, 0.7)',
                  color: '#ffffff',
                  borderColor: 'rgba(255, 255, 255, 0.12)',
                  paddingRight: '42px'
                }}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  position: 'absolute',
                  right: '12px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'transparent',
                  border: 0,
                  color: '#94a3b8',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center'
                }}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            disabled={isSubmitting}
            style={{
              padding: '12px',
              fontSize: '0.95rem',
              fontWeight: 700,
              marginTop: '6px',
              justifyContent: 'center',
              boxShadow: '0 4px 20px rgba(20, 101, 244, 0.4)'
            }}
          >
            {isSubmitting ? (
              <>
                <Loader2 size={18} className="spin" style={{ animation: 'spin 1s linear infinite' }} />
                Authenticating...
              </>
            ) : (
              <>
                <ShieldCheck size={18} /> Enter Business Management OS
              </>
            )}
          </button>
        </form>

        {/* Security Notice */}
        <div style={{
          borderTop: '1px solid rgba(255, 255, 255, 0.08)',
          paddingTop: '16px',
          textAlign: 'center',
          fontSize: '0.74rem',
          color: '#64748b'
        }}>
          Protected enterprise system with PostgreSQL audit logging.
          <br />Session authenticated via secure HTTP-only cookies.
        </div>
      </div>
    </div>
  );
};
