import { useState } from 'react'
import { useMutation, useQueryClient } from '@tantml:function_calls>
<invoke name="useNavigate" from 'react-router-dom'
import { createProject } from '../lib/api'
import { FormError } from '../components/FormError'
import type { AudienceType } from '../types'

export default function NewProject() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [formData, setFormData] = useState({
    name: '',
    repo_url: '',
    website_url: '',
    audience: 'developer' as AudienceType,
    target_length: 90,
  })

  const [validationError, setValidationError] = useState<string | null>(null)

  const createMutation = useMutation({
    mutationFn: createProject,
    onSuccess: (project) => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      navigate(`/projects/${project.id}`)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setValidationError(null)

    if (!formData.name) {
      setValidationError('Please provide a project name')
      return
    }

    if (!formData.repo_url && !formData.website_url) {
      setValidationError('Please provide at least one URL (repository or website)')
      return
    }

    createMutation.mutate({
      name: formData.name,
      repo_url: formData.repo_url || undefined,
      website_url: formData.website_url || undefined,
      audience: formData.audience,
      target_length: formData.target_length,
    })
  }

  return (
    <div className="max-w-3xl mx-auto">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-2">Create New Project</h2>
        <p className="text-gray-700">Generate an automated demo video from your repository or website</p>
      </div>

      <form onSubmit={handleSubmit} className="bg-white rounded-xl border border-gray-200 shadow-sm p-8 space-y-6">
        {/* Global validation error */}
        {validationError && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
            <FormError message={validationError} />
          </div>
        )}

        {/* Project Name */}
        <div>
          <label htmlFor="name" className="block text-sm font-semibold text-gray-900 mb-2">
            Project Name *
          </label>
          <input
            type="text"
            id="name"
            required
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            className="w-full px-4 py-3 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors"
            placeholder="My Awesome Demo"
          />
        </div>

        {/* URLs Section */}
        <div className="bg-gray-50 rounded-xl p-6 border border-gray-200">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">Source (at least one required)</h3>

          {/* Repository URL */}
          <div className="mb-4">
            <label htmlFor="repo_url" className="flex items-center text-sm font-medium text-gray-700 mb-2">
              <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
              </svg>
              GitHub Repository
            </label>
            <input
              type="url"
              id="repo_url"
              value={formData.repo_url}
              onChange={(e) => setFormData({ ...formData, repo_url: e.target.value })}
              className="w-full px-4 py-3 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors"
              placeholder="https://github.com/username/repo"
            />
          </div>

          {/* Website URL */}
          <div>
            <label htmlFor="website_url" className="flex items-center text-sm font-medium text-gray-700 mb-2">
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
              </svg>
              Website URL
            </label>
            <input
              type="url"
              id="website_url"
              value={formData.website_url}
              onChange={(e) => setFormData({ ...formData, website_url: e.target.value })}
              className="w-full px-4 py-3 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors"
              placeholder="https://example.com"
            />
          </div>
        </div>

        {/* Configuration Grid */}
        <div className="grid md:grid-cols-2 gap-6">
          {/* Audience */}
          <div>
            <label htmlFor="audience" className="block text-sm font-semibold text-gray-900 mb-2">
              Target Audience
            </label>
            <select
              id="audience"
              value={formData.audience}
              onChange={(e) => setFormData({ ...formData, audience: e.target.value as AudienceType })}
              className="w-full px-4 py-3 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors"
            >
              <option value="investor">💼 Investor</option>
              <option value="customer">🛍️ Customer</option>
              <option value="developer">👨‍💻 Developer</option>
              <option value="technical">🔧 Technical</option>
            </select>
          </div>

          {/* Target Length */}
          <div>
            <label htmlFor="target_length" className="block text-sm font-semibold text-gray-900 mb-2">
              Video Length
            </label>
            <div className="relative">
              <input
                type="number"
                id="target_length"
                min="30"
                max="300"
                value={formData.target_length}
                onChange={(e) => setFormData({ ...formData, target_length: parseInt(e.target.value) })}
                className="w-full px-4 py-3 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors pr-20"
              />
              <span className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 text-sm font-medium">
                seconds
              </span>
            </div>
            <p className="text-xs text-gray-500 mt-1.5">30-300 seconds recommended</p>
          </div>
        </div>

        {/* Submit */}
        <div className="flex justify-end space-x-4 pt-4 border-t border-gray-200">
          <button
            type="button"
            onClick={() => navigate('/projects')}
            className="px-6 py-3 border border-gray-300 rounded-lg text-sm font-semibold text-gray-700 hover:bg-gray-50 hover:border-gray-400 transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={createMutation.isPending}
            className="px-8 py-3 bg-primary-600 text-white rounded-lg font-semibold hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm flex items-center"
          >
            {createMutation.isPending ? (
              <>
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Creating Project...
              </>
            ) : (
              <>
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Create Project
              </>
            )}
          </button>
        </div>

        {createMutation.isError && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start">
            <svg className="w-5 h-5 text-red-600 mr-3 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-red-800 text-sm font-semibold">
              Failed to create project: {String(createMutation.error)}
            </p>
          </div>
        )}
      </form>
    </div>
  )
}
