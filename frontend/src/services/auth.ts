import { api } from './api';

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

/**
 * Perform user login.
 * Returns the JWT token on success.
 */
export async function login(email: string, password: string): Promise<string> {
  const data = await api<LoginResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
  const token = data.access_token;
  localStorage.setItem('access_token', token);
  return token;
}

/**
 * Register a new user.
 */
export async function register(name: string, email: string, password: string): Promise<void> {
  await api<void>('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ name, email, password }),
  });
}

/**
 * Logout the current user – clears the stored token.
 */
export function logout(): void {
  localStorage.removeItem('access_token');
}

/** Retrieve the stored JWT token, if any. */
export function getToken(): string | null {
  return localStorage.getItem('access_token');
}

/** Simple auth check based on token existence. */
export function isAuthenticated(): boolean {
  return !!getToken();
}
