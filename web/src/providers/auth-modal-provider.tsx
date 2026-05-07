"use client";

import { createContext, useContext, useState, type ReactNode } from "react";

interface AuthModalContextValue {
  openAuthModal: () => void;
}

const AuthModalContext = createContext<AuthModalContextValue | null>(null);

export function AuthModalProvider({
  children,
  onOpen,
}: {
  children: ReactNode;
  onOpen: () => void;
}) {
  return (
    <AuthModalContext.Provider value={{ openAuthModal: onOpen }}>
      {children}
    </AuthModalContext.Provider>
  );
}

export function useAuthModal(): AuthModalContextValue {
  const ctx = useContext(AuthModalContext);
  if (!ctx) throw new Error("useAuthModal must be used inside AuthModalProvider");
  return ctx;
}
