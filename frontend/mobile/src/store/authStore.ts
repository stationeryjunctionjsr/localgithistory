import { create } from 'zustand';
import type { User } from '@sj/api-client';

interface AuthState {
  user: User | null;
  setUser: (user: User | null) => void;
  sessionRevokedDetail: any | null;
  setSessionRevokedDetail: (detail: any | null) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  setUser: (user) => set({ user }),
  sessionRevokedDetail: null,
  setSessionRevokedDetail: (detail) => set({ sessionRevokedDetail: detail }),
}));
