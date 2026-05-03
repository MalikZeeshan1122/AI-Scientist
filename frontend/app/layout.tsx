import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import { MobileTopBar, Sidebar } from "@/components/Sidebar";
import { ThemeProvider } from "@/components/ThemeProvider";
import { ToastProvider } from "@/components/Toast";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

const jetBrains = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "AI Scientist · Autonomous research workspace",
  description:
    "Read papers, propose ideas, run experiments, and draft papers — autonomously.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${jetBrains.variable}`} suppressHydrationWarning>
      <body className="font-sans antialiased">
        <ThemeProvider>
          <ToastProvider>
            <div className="relative min-h-screen flex">
              <Sidebar />
              <div className="flex-1 min-w-0 flex flex-col">
                <MobileTopBar />
                <main className="flex-1 px-4 sm:px-8 lg:px-12 py-6 lg:py-10 max-w-7xl w-full mx-auto">
                  {children}
                </main>
              </div>
            </div>
          </ToastProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
