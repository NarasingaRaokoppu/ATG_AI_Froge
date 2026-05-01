/**
 * Auth store — keeps the current user in memory.
 * The JWT itself lives in an httpOnly cookie (AD-02).
 */

import { create } from "zustand";

import type { User } from "../types";
import { authApi } from "./endpoints";

interface AuthState {
  user: User | null;
  loading: boolean;
  hydrate: () => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  loading: true,

  hydrate: async () => {
    try {
      const user = await authApi.me();
      set({ user, loading: false });
    } catch {
      set({ user: null, loading: false });
    }
  },

  login: async (email, password) => {
    const user = await authApi.login(email, password);
    set({ user });
  },

  register: async (email, password) => {
    await authApi.register(email, password);
  },

  logout: async () => {
    await authApi.logout();
    set({ user: null });
  },
}));
