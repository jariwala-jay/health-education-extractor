import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Layout from "@/components/Layout";
import { Toaster } from "react-hot-toast";

const inter = Inter({
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Health Education Extractor",
  description: "Extract and process health education content from PDFs",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.className} antialiased`}>
        <Layout>
          {children}
        </Layout>
        <Toaster position="top-right" />
      </body>
    </html>
  );
}
