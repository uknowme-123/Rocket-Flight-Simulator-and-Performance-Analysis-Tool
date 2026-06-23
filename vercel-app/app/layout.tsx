import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Rocket Flight Simulator',
  description: 'Vercel-compatible rocket simulation dashboard',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
