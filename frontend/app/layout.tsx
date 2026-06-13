import type { Metadata, Viewport } from "next";
import "./globals.css";
import RegisterSW from "./register-sw";

export const metadata: Metadata = {
  title: "Consultas DETRAN-PA",
  description: "Consultas de veiculo, infracoes, licenciamento e CNH",
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
      <body>
        <RegisterSW />
        <header className="topbar">
          <div className="container topbar-inner">
            <span className="logo">🚗 Consultas DETRAN-PA</span>
            <span className="tag">Beta</span>
          </div>
        </header>
        <main className="container">{children}</main>
        <footer className="footer container">
          Sistema independente de consultas. Os dados sao obtidos diretamente do DETRAN-PA.
        </footer>
      </body>
    </html>
  );
}
