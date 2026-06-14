import type { Metadata, Viewport } from "next";
import "./globals.css";
import RegisterSW from "./register-sw";

export const metadata: Metadata = {
  title: "Consultas DETRAN-PA",
  description: "Consultas de veículo, infrações, licenciamento e CNH do DETRAN-PA",
  manifest: "/manifest.webmanifest",
  appleWebApp: { capable: true, statusBarStyle: "black-translucent", title: "DETRAN-PA" },
  icons: { icon: "/icon-192.png", apple: "/icon-192.png" },
};

export const viewport: Viewport = {
  themeColor: "#6366f1",
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        <RegisterSW />
        <header className="topbar">
          <div className="container topbar-inner">
            <span className="logo">
              <span className="logo-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M19 17h2c.6 0 1-.4 1-1v-3c0-.9-.7-1.7-1.5-1.9C18.7 10.6 16 10 16 10s-1.3-1.4-2.2-2.3c-.5-.4-1.2-.7-1.9-.7H5c-.6 0-1.1.4-1.4.9l-1.4 2.2C1.8 10.9 1.5 12 1.5 13v3c0 .6.4 1 1 1h1"/>
                  <circle cx="7" cy="17" r="2"/><circle cx="17" cy="17" r="2"/>
                </svg>
              </span>
              Consultas DETRAN-PA
            </span>
            <span className="tag">Beta</span>
          </div>
        </header>
        <main className="container">{children}</main>
        <footer className="footer container">
          Sistema independente de consultas. Dados obtidos diretamente do DETRAN-PA.
        </footer>
      </body>
    </html>
  );
}