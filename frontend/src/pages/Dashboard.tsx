import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { useState, useMemo } from 'react'
import { Search, Filter, ArrowUpDown } from 'lucide-react'
import { listProjects } from '../lib/api'

type SortField = 'name' | 'updated_at' | 'current_stage'
type SortOrder = 'asc' | 'desc'

export default function Dashboard() {
  const { data: projects, isLoading, error } = useQuery({
    queryKey: ['projects'],
    queryFn: listProjects,
  })

  const [searchQuery, setSearchQuery] = useState('')
  const [filterStage, setFilterStage] = useState<string>('all')
  const [filterAudience, setFilterAudience] = useState<string>('all')
  const [sortField, setSortField] = useState<SortField>('updated_at')
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc')

  // Filter and sort projects
  const filteredProjects = useMemo(() => {
    if (!projects) return []

    return projects
      .filter((project) => {
        // Search filter
        const matchesSearch =
          searchQuery === '' ||
          project.name.toLowerCase().includes(searchQuery.toLowerCase())

        // Stage filter
        const matchesStage =
          filterStage === 'all' || project.current_stage === filterStage

        // Audience filter
        const matchesAudience =
          filterAudience === 'all' || project.audience === filterAudience

        return matchesSearch && matchesStage && matchesAudience
      })
      .sort((a, b) => {
        let comparison = 0

        if (sortField === 'name') {
          comparison = a.name.localeCompare(b.name)
        } else if (sortField === 'updated_at') {
          comparison = new Date(a.updated_at).getTime() - new Date(b.updated_at).getTime()
        } else if (sortField === 'current_stage') {
          comparison = a.current_stage.localeCompare(b.current_stage)
        }

        return sortOrder === 'asc' ? comparison : -comparison
      })
  }, [projects, searchQuery, filterStage, filterAudience, sortField, sortOrder])

  const toggleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortOrder('asc')
    }
  }

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <p className="text-red-800">Failed to load projects: {String(error)}</p>
      </div>
    )
  }

  return (
    <div>
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-2">Your Projects</h2>
        <p className="text-gray-700">Create and manage automated demo videos</p>
      </div>

      {/* Search and Filters */}
      {projects && projects.length > 0 && (
        <div className="mb-6 space-y-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              placeholder="Search projects..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>

          {/* Filters and Sort */}
          <div className="flex flex-wrap gap-3">
            {/* Stage Filter */}
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-gray-500" />
              <select
                value={filterStage}
                onChange={(e) => setFilterStage(e.target.value)}
                className="px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              >
                <option value="all">All Stages</option>
                <option value="analyze">Analyze</option>
                <option value="script">Script</option>
                <option value="capture">Capture</option>
                <option value="voice">Voice</option>
                <option value="assemble">Assemble</option>
                <option value="complete">Complete</option>
                <option value="failed">Failed</option>
              </select>
            </div>

            {/* Audience Filter */}
            <select
              value={filterAudience}
              onChange={(e) => setFilterAudience(e.target.value)}
              className="px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value="all">All Audiences</option>
              <option value="developer">Developer</option>
              <option value="investor">Investor</option>
              <option value="customer">Customer</option>
              <option value="technical">Technical</option>
            </select>

            {/* Sort */}
            <div className="flex items-center gap-2 ml-auto">
              <ArrowUpDown className="w-4 h-4 text-gray-500" />
              <button
                onClick={() => toggleSort('name')}
                className={`px-3 py-1.5 border rounded-md text-sm ${
                  sortField === 'name'
                    ? 'border-primary-500 bg-primary-50 text-primary-700'
                    : 'border-gray-300 text-gray-700'
                }`}
              >
                Name {sortField === 'name' && (sortOrder === 'asc' ? '↑' : '↓')}
              </button>
              <button
                onClick={() => toggleSort('updated_at')}
                className={`px-3 py-1.5 border rounded-md text-sm ${
                  sortField === 'updated_at'
                    ? 'border-primary-500 bg-primary-50 text-primary-700'
                    : 'border-gray-300 text-gray-700'
                }`}
              >
                Date {sortField === 'updated_at' && (sortOrder === 'asc' ? '↑' : '↓')}
              </button>
            </div>
          </div>

          {/* Results count */}
          <p className="text-sm text-gray-600">
            Showing {filteredProjects.length} of {projects.length} projects
          </p>
        </div>
      )}

      {!projects || projects.length === 0 ? (
        <div className="text-center py-20 bg-white rounded-xl border border-gray-200 shadow-sm">
          <div className="w-20 h-20 bg-primary-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
            <svg className="w-10 h-10 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
          </div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">No projects yet</h3>
          <p className="text-gray-700 mb-6 max-w-md mx-auto">
            Get started by creating your first automated demo video from a GitHub repository or website
          </p>
          <Link
            to="/projects/new"
            className="inline-flex items-center px-6 py-3 bg-primary-600 text-white rounded-lg font-semibold hover:bg-primary-700 transition-colors shadow-sm"
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Create Your First Project
          </Link>
        </div>
      ) : filteredProjects.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg border border-gray-200">
          <p className="text-gray-600">No projects match your filters</p>
          <button
            onClick={() => {
              setSearchQuery('')
              setFilterStage('all')
              setFilterAudience('all')
            }}
            className="mt-3 text-primary-600 hover:text-primary-700 font-medium"
          >
            Clear filters
          </button>
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {filteredProjects.map((project) => (
            <Link
              key={project.id}
              to={`/projects/${project.id}`}
              className="group block bg-white rounded-xl border border-gray-200 p-6 hover:border-primary-400 hover:shadow-lg transition-all duration-200"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900 mb-1 group-hover:text-primary-600 transition-colors">
                    {project.name}
                  </h3>
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                      project.current_stage === 'complete'
                        ? 'bg-green-100 text-green-800'
                        : project.current_stage === 'failed'
                        ? 'bg-red-100 text-red-800'
                        : 'bg-blue-100 text-blue-800'
                    }`}
                  >
                    {project.current_stage === 'complete' && '✓ '}
                    {project.current_stage === 'failed' && '✗ '}
                    {project.current_stage}
                  </span>
                </div>
              </div>

              <div className="space-y-2 text-sm">
                <div className="flex items-center text-gray-700">
                  <svg className="w-4 h-4 mr-2 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                  {project.audience}
                </div>
                <div className="flex items-center text-gray-700">
                  <svg className="w-4 h-4 mr-2 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  {project.target_length}s video
                </div>
                <div className="flex items-center text-xs text-gray-600 pt-2 border-t border-gray-200">
                  <svg className="w-3.5 h-3.5 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  {new Date(project.updated_at).toLocaleDateString()} at {new Date(project.updated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
