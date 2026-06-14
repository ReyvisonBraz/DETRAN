"use client";

import { useAuth } from "@/lib/auth";
import { useRouter, usePathname } from "next/navigation";
import { useState } from "react";

const NAV_ITEMS = [
  {
    href: "/dashboard",
    label: "Início",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>
      </svg>
    ),
  },
  {
    href: "/consultas",
    label: "Nova Consulta",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
      </svg>
    ),
  },
  {
    href: "/historico",
    label: "Histórico",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
      </svg>
    ),
  },
  {
    href: "/creditos",
    label: "Créditos",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="8"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/>
      </svg>
    ),
  },
  {
    href: "/perfil",
    label: "Perfil",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
      </svg>
    ),
  },
];

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { user, profile, logout, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  if (loading) {
    return (
      <div className="center">
        <div className="spinner" style={{ width: 36, height: 36 }}></div>
        <p style={{ marginTop: 8, color: "var(--muted)" }}>Carregando...</p>
      </div>
    );
  }

  if (!user) {
    router.push("/login");
    return null;
  }

  if (user && profile && !profile.perfilCompleto) {
    router.push("/completar");
    return null;
  }

  if (!profile) {
    return (
      <div className="center">
        <div className="spinner" style={{ width: 36, height: 36 }}></div>
        <p style={{ marginTop: 8, color: "var(--muted)" }}>Carregando perfil...</p>
      </div>
    );
  }

  const initials = `${profile.nome?.[0] || ""}${profile.sobrenome?.[0] || ""}`.toUpperCase();

  return (
    <div className="app-shell">
      <aside className={`sidebar ${mobileMenuOpen ? "open" : ""}`}>
        <div className="sidebar-header">
          <div className="sidebar-logo">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="var(--primary-2)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M19 17h2c.6 0 1-.4 1-1v-3c0-.9-.7-1.7-1.5-1.9C18.7 10.6 16 10 16 10s-1.3-1.4-2.2-2.3c-.5-.4-1.2-.7-1.9-.7H5c-.6 0-1.1.4-1.4.9l-1.4 2.2C1.8 10.9 1.5 12 1.5 13v3c0 .6.4 1 1 1h1"/>
              <circle cx="7" cy="17" r="2"/><circle cx="17" cy="17" r="2"/>
            </svg>
            <span className="sidebar-brand">DETRAN-PA</span>
          </div>
          <button className="sidebar-close" onClick={() => setMobileMenuOpen(false)}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>

        {profile.role === "admin" && (
          <div className="sidebar-admin-badge">Admin</div>
        )}

        <nav className="sidebar-nav">
          {NAV_ITEMS.map((item) => (
            <a
              key={item.href}
              href={item.href}
              onClick={(e) => { e.preventDefault(); router.push(item.href); setMobileMenuOpen(false); }}
              className={`sidebar-link ${pathname === item.href ? "active" : ""}`}
            >
              {item.icon}
              <span>{item.label}</span>
            </a>
          ))}
          {profile.role === "admin" && (
            <a
              href="/admin/dashboard"
              onClick={(e) => { e.preventDefault(); router.push("/admin/dashboard"); setMobileMenuOpen(false); }}
              className={`sidebar-link admin-link ${pathname?.startsWith("/admin") ? "active" : ""}`}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              </svg>
              <span>Admin</span>
            </a>
          )}
        </nav>

        <div className="sidebar-footer">
          <div className="sidebar-credits">
            <span className="sidebar-credits-num">{profile.saldoCreditos}</span>
            <span className="sidebar-credits-label">créditos</span>
          </div>
          <div className="sidebar-user">
            <div className="sidebar-avatar">{initials}</div>
            <div className="sidebar-user-info">
              <div className="sidebar-user-name">{profile.nome} {profile.sobrenome}</div>
              <div className="sidebar-user-email">{profile.email}</div>
            </div>
            <button className="sidebar-logout" onClick={logout} title="Sair">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>
              </svg>
            </button>
          </div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar-mobile">
          <button className="mobile-menu-btn" onClick={() => setMobileMenuOpen(true)}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
          </button>
          <span className="topbar-mobile-title">
            {NAV_ITEMS.find((i) => i.href === pathname)?.label || "DETRAN-PA"}
          </span>
          <div className="topbar-mobile-credits">{profile.saldoCreditos} cr</div>
        </header>
        <div className="main-scroll">
          {children}
        </div>
      </main>
    </div>
  );
}