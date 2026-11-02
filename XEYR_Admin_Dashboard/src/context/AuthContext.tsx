import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { User } from '../types';
import { authApi } from '../services/api';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  authMessage: string | null;
  setAuthMessage: (msg: string | null) => void;
  login: (credentials: { username: string; password: string }) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [authMessage, setAuthMessage] = useState<string | null>(null);

  const refreshUser = useCallback(async () => {
    try {
      const data = await authApi.getMe();
      if (data && data.username) {
        setUser(data);
      } else {
        setUser(null);
      }
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  // Handle session expiration events dispatched by apiFetch
  useEffect(() => {
    const handleAuthExpired = (event: any) => {
      setUser(null);
      setAuthMessage(event?.detail?.message || 'Your administrative session has expired. Please sign in again.');
    };

    if (typeof window !== 'undefined') {
      window.addEventListener('xeyr:auth_expired', handleAuthExpired);
      return () => window.removeEventListener('xeyr:auth_expired', handleAuthExpired);
    }
  }, []);

  const login = async (credentials: { username: string; password: string }) => {
    setLoading(true);
    setAuthMessage(null);
    try {
      const res = await authApi.login(credentials);
      if (res && res.user) {
        setUser(res.user);
      }
      // Re-verify session identity with Django
      await refreshUser();
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      await authApi.logout();
    } catch {
      // Ignored
    } finally {
      setUser(null);
      setAuthMessage('You have been securely signed out.');
    }
  };

  return (
    <AuthContext.Provider value={{
      user,
      loading,
      isAuthenticated: !!user,
      authMessage,
      setAuthMessage,
      login,
      logout,
      refreshUser
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
