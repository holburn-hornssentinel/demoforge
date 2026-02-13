import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { createProject } from '../lib/api'
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

  const createMutation = useMutation({
    mutationFn: createProject,
    onSuccess: (project) => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      navigate(`/projects/${project.id}`)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (!formData.name || (!formData.repo_url && !formData.website_url)) {
      alert('Please provide a name and at least one URL')
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
    <div className="max-w-2xl mx-auto">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">New Project</h2>

      <form onSubmit={handleSubmit} className="bg-white rounded-lg border border-gray-200 p-6 space-y-6">
        {/* Project Name */}
        <div>
          <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
            Project Name *
          </label>
          <input
            type="text"
            id="name"
            required
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            placeholder="My Awesome Demo"
          />
        </div>

        {/* Repository URL */}
        <div>
          <label htmlFor="repo_url" className="block text-sm font-medium text-gray-700 mb-2">
            GitHub Repository URL
          </label>
          <input
            type="url"
            id="repo_url"
            value={formData.repo_url}
            onChange={(e) => setFormData({ ...formData, repo_url: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            placeholder="https://github.com/username/repo"
          />
        </div>

        {/* Website URL */}
        <div>
          <label htmlFor="website_url" className="block text-sm font-medium text-gray-700 mb-2">
            Website URL
          </label>
          <input
            type="url"
            id="website_url"
            value={formData.website_url}
            onChange={(e) => setFormData({ ...formData, website_url: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            placeholder="https://example.com"
          />
          <p className="text-xs text-gray-500 mt-1">
            At least one URL (repo or website) is required
          </p>
        </div>

        {/* Audience */}
        <div>
          <label htmlFor="audience" className="block text-sm font-medium text-gray-700 mb-2">
            Target Audience
          </label>
          <select
            id="audience"
            value={formData.audience}
            onChange={(e) => setFormData({ ...formData, audience: e.target.value as AudienceType })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="investor">Investor</option>
            <option value="customer">Customer</option>
            <option value="developer">Developer</option>
            <option value="technical">Technical</option>
          </select>
        </div>

        {/* Target Length */}
        <div>
          <label htmlFor="target_length" className="block text-sm font-medium text-gray-700 mb-2">
            Target Video Length (seconds)
          </label>
          <input
            type="number"
            id="target_length"
            min="30"
            max="300"
            value={formData.target_length}
            onChange={(e) => setFormData({ ...formData, target_length: parseInt(e.target.value) })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
          <p className="text-xs text-gray-500 mt-1">30-300 seconds recommended</p>
        </div>

        {/* Submit */}
        <div className="flex justify-end space-x-3">
          <button
            type="button"
            onClick={() => navigate('/projects')}
            className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={createMutation.isPending}
            className="px-4 py-2 bg-primary-600 text-white rounded-md text-sm font-medium hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {createMutation.isPending ? 'Creating...' : 'Create Project'}
          </button>
        </div>

        {createMutation.isError && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <p className="text-red-800 text-sm">
              Failed to create project: {String(createMutation.error)}
            </p>
          </div>
        )}
      </form>
    </div>
  )
}
