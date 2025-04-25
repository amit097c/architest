import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Menu, X } from 'lucide-react';

const Header: React.FC = () => {
  const location = useLocation();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  
  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };
  
  return (
    <header className="sticky top-0 z-10 bg-[#43A29E] text-white border-b py-3 px-4 sm:px-6">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center">
          <Link to="/dashboard" className="flex items-center">
            <h1 className="text-xl sm:text-2xl font-bold mr-2">ArchiTest</h1>
            <span className="hidden sm:inline text-sm text-white/80">AI-Powered Testing</span>
          </Link>
        </div>
        
        {/* Mobile menu button */}
        <button 
          className="sm:hidden text-white"
          onClick={toggleMobileMenu}
          aria-label="Toggle menu"
        >
          {isMobileMenuOpen ? (
            <X className="h-6 w-6" />
          ) : (
            <Menu className="h-6 w-6" />
          )}
        </button>
        
        {/* Desktop navigation */}
        <nav className="hidden sm:block">
          <ul className="flex items-center gap-1">
            <li>
              <Button 
                variant={location.pathname === '/dashboard' ? 'default' : 'ghost'} 
                size="sm"
                className={location.pathname !== '/dashboard' ? "text-white hover:bg-white/10" : ""}
                asChild
              >
                <Link to="/dashboard">Dashboard</Link>
              </Button>
            </li>
            <li>
              <Button 
                variant={location.pathname === '/create' ? 'default' : 'ghost'} 
                size="sm"
                className={location.pathname !== '/create' ? "text-white hover:bg-white/10" : ""}
                asChild
              >
                <Link to="/create">Create Test</Link>
              </Button>
            </li>
            <li>
              <Button 
                variant={location.pathname === '/collections' || location.pathname.startsWith('/collection/') ? 'default' : 'ghost'} 
                size="sm"
                className={!location.pathname.startsWith('/collection') && location.pathname !== '/collections' ? "text-white hover:bg-white/10" : ""}
                asChild
              >
                <Link to="/collections">Collections</Link>
              </Button>
            </li>
            <li>
              <Button 
                variant={location.pathname === '/history' ? 'default' : 'ghost'} 
                size="sm"
                className={location.pathname !== '/history' ? "text-white hover:bg-white/10" : ""}
                asChild
              >
                <Link to="/history">History</Link>
              </Button>
            </li>
          </ul>
        </nav>
      </div>

      {/* Mobile navigation */}
      {isMobileMenuOpen && (
        <nav className="sm:hidden pt-4 pb-2">
          <ul className="flex flex-col space-y-2">
            <li>
              <Button 
                variant={location.pathname === '/dashboard' ? 'default' : 'ghost'} 
                className={`w-full justify-start ${location.pathname !== '/dashboard' ? "text-white hover:bg-white/10" : ""}`}
                onClick={() => setIsMobileMenuOpen(false)}
                asChild
              >
                <Link to="/dashboard">Dashboard</Link>
              </Button>
            </li>
            <li>
              <Button 
                variant={location.pathname === '/create' ? 'default' : 'ghost'} 
                className={`w-full justify-start ${location.pathname !== '/create' ? "text-white hover:bg-white/10" : ""}`}
                onClick={() => setIsMobileMenuOpen(false)}
                asChild
              >
                <Link to="/create">Create Test</Link>
              </Button>
            </li>
            <li>
              <Button 
                variant={location.pathname === '/collections' || location.pathname.startsWith('/collection/') ? 'default' : 'ghost'} 
                className={`w-full justify-start ${!location.pathname.startsWith('/collection') && location.pathname !== '/collections' ? "text-white hover:bg-white/10" : ""}`}
                onClick={() => setIsMobileMenuOpen(false)}
                asChild
              >
                <Link to="/collections">Collections</Link>
              </Button>
            </li>
            <li>
              <Button 
                variant={location.pathname === '/history' ? 'default' : 'ghost'} 
                className={`w-full justify-start ${location.pathname !== '/history' ? "text-white hover:bg-white/10" : ""}`}
                onClick={() => setIsMobileMenuOpen(false)}
                asChild
              >
                <Link to="/history">History</Link>
              </Button>
            </li>
          </ul>
        </nav>
      )}
    </header>
  );
};

export default Header; 