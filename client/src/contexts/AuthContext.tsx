import { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import { login as apiLogin, register as apiRegister, getCurrentUser } from '../lib/api';

interface User {
  id: string;
  email: string;
  created_at: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_KEY = 'skout_auth_token';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Initialize auth state from localStorage
  useEffect(() => {
    const initAuth = async () => {
      const storedToken = localStorage.getItem(TOKEN_KEY);

      if (storedToken) {
        try {
          // Verify token is still valid
          const currentUser = await getCurrentUser(storedToken);
          setToken(storedToken);
          setUser(currentUser);
        } catch (error) {
          // Token is invalid or expired, clear it
          localStorage.removeItem(TOKEN_KEY);
        }
      }

      setLoading(false);
    };

    initAuth();
  }, []);

  const login = async (email: string, password: string) => {
    const response = await apiLogin(email, password);
    setToken(response.token);
    setUser(response.user);
    localStorage.setItem(TOKEN_KEY, response.token);
  };

  const register = async (email: string, password: string) => {
    const response = await apiRegister(email, password);
    setToken(response.token);
    setUser(response.user);
    localStorage.setItem(TOKEN_KEY, response.token);
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem(TOKEN_KEY);
  };

  const value: AuthContextType = {
    user,
    token,
    login,
    register,
    logout,
    loading,
    isAuthenticated: !!token && !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
