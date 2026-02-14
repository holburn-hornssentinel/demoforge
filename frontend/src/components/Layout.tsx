import { Outlet, Link, useLocation } from 'react-router-dom'
import { useState } from 'react'
import { Menu, X } from 'lucide-react'

export default function Layout() {
  const location = useLocation()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const closeMobileMenu = () => setMobileMenuOpen(false)

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-8">
              <Link to="/" className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-primary-600 rounded-lg flex items-center justify-center shadow-md">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                </div>
                <div>
                  <h1 className="text-xl font-bold text-gray-900">
                    DemoForge
                  </h1>
                  <p className="text-xs text-gray-600">Automated Demo Videos</p>
                </div>
              </Link>
              {/* Desktop Navigation */}
              <nav className="hidden md:flex space-x-2">
                <Link
                  to="/projects"
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    location.pathname.startsWith('/projects')
                      ? 'bg-primary-100 text-primary-700'
                      : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
                  }`}
                >
                  Projects
                </Link>
              </nav>
            </div>

            {/* Desktop Actions */}
            <div className="hidden md:flex items-center space-x-3">
              <Link
                to="/projects/new"
                className="px-6 py-2.5 bg-primary-600 text-white rounded-lg text-sm font-semibold hover:bg-primary-700 transition-colors shadow-sm"
              >
                + New Project
              </Link>
            </div>

            {/* Mobile Menu Button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
            >
              {mobileMenuOpen ? (
                <X className="w-6 h-6" />
              ) : (
                <Menu className="w-6 h-6" />
              )}
            </button>
          </div>
        </div>

        {/* Mobile Navigation Slide-out */}
        {mobileMenuOpen && (
          <>
            {/* Backdrop */}
            <div
              className="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden"
              onClick={closeMobileMenu}
            />

            {/* Slide-out Menu */}
            <div className="fixed top-16 right-0 bottom-0 w-64 bg-white shadow-xl z-50 md:hidden transform transition-transform duration-200 ease-in-out">
              <nav className="flex flex-col p-4 space-y-2">
                <Link
                  to="/projects"
                  onClick={closeMobileMenu}
                  className={`px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                    location.pathname.startsWith('/projects')
                      ? 'bg-primary-100 text-primary-700'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  Projects
                </Link>

                <Link
                  to="/projects/new"
                  onClick={closeMobileMenu}
                  className="px-4 py-3 bg-primary-600 text-white rounded-lg text-sm font-semibold hover:bg-primary-700 transition-colors text-center"
                >
                  + New Project
                </Link>
              </nav>

              {/* Mobile Footer Links */}
              <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-200 bg-gray-50">
                <div className="flex flex-col space-y-2 text-sm">
                  <a href="#" className="text-gray-600 hover:text-primary-600 transition-colors">
                    Documentation
                  </a>
                  <a href="#" className="text-gray-600 hover:text-primary-600 transition-colors">
                    GitHub
                  </a>
                  <a href="#" className="text-gray-600 hover:text-primary-600 transition-colors">
                    API
                  </a>
                </div>
              </div>
            </div>
          </>
        )}
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
            <p className="text-sm text-gray-600">
              <span className="font-semibold text-gray-900">DemoForge</span> v0.1.0 - Transform repos into polished demo videos
            </p>
            <div className="flex space-x-6 text-sm text-gray-600">
              <a href="#" className="hover:text-primary-600 transition-colors font-medium">Documentation</a>
              <a href="#" className="hover:text-primary-600 transition-colors font-medium">GitHub</a>
              <a href="#" className="hover:text-primary-600 transition-colors font-medium">API</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
