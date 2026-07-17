import React from 'react';
import { navItems } from './navItems.js';

export default function Sidebar({ currentPage }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-scroll">
        <nav className="sidebar-nav" aria-label="Primary">
          {navItems.map(({ label, icon: Icon, href, page }) => {
            const isActive = page === currentPage || (page === 'home' && currentPage === 'word');
            const className = ['sidebar-item', isActive ? 'active' : ''].filter(Boolean).join(' ');
            const content = (
              <>
                <Icon aria-hidden="true" size={17} strokeWidth={2} />
                <span>{label}</span>
              </>
            );

            if (href) {
              return (
                <a key={label} className={className} href={href}>
                  {content}
                </a>
              );
            }

            return (
              <div key={label} className={className}>
                {content}
              </div>
            );
          })}
        </nav>
      </div>
    </aside>
  );
}
