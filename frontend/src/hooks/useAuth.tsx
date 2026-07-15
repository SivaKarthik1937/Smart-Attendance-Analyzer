/**
 * hooks/useAuth.tsx
 * ===================
 * App-wide authentication state. Wrap the app in <AuthProvider> once (see
 * main.tsx), then call useAuth() from any component to read the current
 * user or trigger login/register/logout.
 */

import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { authApi, clearSession, getStoredToken, saveSession } from "@/services/api";
import type { CurrentUser, Role, UserRegisterPayload } from "@/types";

interface AuthContextValue {
  user: CurrentUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<CurrentUser>;
  register: (payload: UserRegisterPayload) => Promise<CurrentUser>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // On first load, if a token is already stored, restore the session by
  // fetching the current user's identity from the API.
  useEffect(() => {
    const token = getStoredToken();
    if (!token) {
      setIsLoading(false);
      return;
    }
    authApi
      .me()
      .then((currentUser) => setUser(currentUser))
      .catch(() => clearSession())
      .finally(() => setIsLoading(false));
  }, []);

  async function login(username: string, password: string): Promise<CurrentUser> {
    const token = await authApi.login(username, password);
    saveSession(token);
    const currentUser = await authApi.me();
    setUser(currentUser);
    return currentUser;
  }

  async function register(payload: UserRegisterPayload): Promise<CurrentUser> {
    const token = await authApi.register(payload);
    saveSession(token);
    const currentUser = await authApi.me();
    setUser(currentUser);
    return currentUser;
  }

  function logout(): void {
    clearSession();
    setUser(null);
  }

  const value: AuthContextValue = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    register,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an <AuthProvider>");
  }
  return context;
}

/** Convenience helper for role checks in components/route guards. */
export function hasRole(user: CurrentUser | null, ...roles: Role[]): boolean {
  return !!user && roles.includes(user.role);
}
