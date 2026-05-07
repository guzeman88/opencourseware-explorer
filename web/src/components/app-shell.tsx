"use client";

import { useState } from "react";
import { Navbar } from "@/components/navbar";
import { AuthModal } from "@/components/auth-modal";
import { AuthProvider } from "@/providers/auth-provider";
import { AuthModalProvider } from "@/providers/auth-modal-provider";
import { PwaRegister } from "@/components/pwa-register";

export function AppShell({ children }: { children: React.ReactNode }) {
  const [authOpen, setAuthOpen] = useState(false);

  return (
    <AuthProvider>
      <AuthModalProvider onOpen={() => setAuthOpen(true)}>
        <Navbar onSignInClick={() => setAuthOpen(true)} />
        <main className="min-h-[calc(100vh-4rem)]">
          {children}
        </main>
        <footer className="border-t border-border py-8 text-center text-sm text-muted-foreground">
          <p>
            The Commons — Aggregating free university education
            from MIT, Yale, Stanford, Harvard, NPTEL, Berkeley, and more.
          </p>
          <p className="mt-1">
            All course content belongs to their respective universities and creators.
          </p>
        </footer>
        <PwaRegister />
        {authOpen && <AuthModal onClose={() => setAuthOpen(false)} />}
      </AuthModalProvider>
    </AuthProvider>
  );
}
