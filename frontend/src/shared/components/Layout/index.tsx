import React from "react";

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <div className="layout">
      <header>
        {/* Header content will go here */}
        <h1>Socrates</h1>
      </header>
      <main>{children}</main>
      <footer>{/* Footer content will go here */}</footer>
    </div>
  );
};
