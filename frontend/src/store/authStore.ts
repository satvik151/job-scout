import { create } from "zustand";

export interface AuthUser {
  id: number;
  email: string;
  has_resume: boolean;
}

interface AuthState {
  token: string | null;
  user: AuthUser | null;
  hydrated: boolean;
  setAuth: (token: string, user: AuthUser) => void;
  setUser: (user: AuthUser) => void;
  hydrate: () => void;
  logout: () => void;
}

const TOKEN_KEY = "jobscout.token";
const USER_KEY = "jobscout.user";

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  user: null,
  hydrated: false,
  setAuth: (token, user) => {
    if (typeof window !== "undefined") {
      localStorage.setItem(TOKEN_KEY, token);
      localStorage.setItem(USER_KEY, JSON.stringify(user));
    }
    set({ token, user });
  },
  setUser: (user) => {
    if (typeof window !== "undefined") {
      localStorage.setItem(USER_KEY, JSON.stringify(user));
    }
    set({ user });
  },
  hydrate: () => {
    if (typeof window === "undefined") {
      set({ hydrated: true });
      return;
    }
    const token = localStorage.getItem(TOKEN_KEY);
    const userRaw = localStorage.getItem(USER_KEY);
    let user: AuthUser | null = null;
    if (userRaw) {
      try {
        user = JSON.parse(userRaw);
      } catch {
        user = null;
      }
    }
    set({ token, user, hydrated: true });
  },
  logout: () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
    }
    set({ token: null, user: null });
  },
}));