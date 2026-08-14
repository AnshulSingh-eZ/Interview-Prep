import React, { createContext, useContext, useState, ReactNode } from 'react';
import * as authService from '../services/auth';

interface AuthContextProps {
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextProps | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [token, setToken] = useState<string | null>(authService.getToken());

  const login = async (email: string, password: string) => {
    const t = await authService.login(email, password);
    setToken(t);
  };

  const logout = () => {
    authService.logout();
    setToken(null);
  };

  const value: AuthContextProps = {
    token,
    login,
    logout,
    isAuthenticated: !!token,
  };

  return (
    <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextProps => {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return ctx;
};
