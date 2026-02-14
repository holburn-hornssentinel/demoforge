import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useParams, useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { getProject, executePipeline, deleteProject } from '../lib/api'
import { useSSE } from '../hooks/useSSE'
import { PipelineProgress, PipelineProgressData } from '../components/PipelineProgress'
import { VideoPlayer } from '../components/VideoPlayer'
import { ConfirmDialog } from '../components/ConfirmDialog'

export default function ProjectDetail() {
  const { projectId } = useParams<{ projectId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [showProgress, setShowProgress] = useState(false)
  const [showExecuteDialog, setShowExecuteDialog] = useState(false)
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)

  const { data: project, isLoading, error } = useQuery({
    queryKey: ['projects', projectId],
    queryFn: () => getProject(projectId!),
    enabled: !!projectId,
  })

  // SSE connection for pipeline progress
  const sseUrl = showProgress && projectId
    ? `${import.meta.env.VITE_API_URL || 'http://localhost:7500'}/api/pipeline/progress/${projectId}`
    : null

  const { data: progressData, isConnected } = useSSE<PipelineProgressData>(sseUrl, {
    enabled: showProgress,
    reconnect: true,
  })

  const executeMutation = useMutation({
    mutationFn: executePipeline,
    onSuccess: () => {
      setShowProgress(true)
      queryClient.invalidateQueries({ queryKey: ['projects', projectId] })
    },
  })

  // Stop showing progress when pipeline completes or fails
  useEffect(() => {
    if (progressData?.stage === 'complete' || progressData?.stage === 'failed') {
      setTimeout(() => {
        setShowProgress(false)
        queryClient.invalidateQueries({ queryKey: ['projects', projectId] })
      }, 2000)
    }
  }, [progressData, projectId, queryClient])

  const deleteMutation = useMutation({
    mutationFn: deleteProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      navigate('/projects')
    },
  })

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (error || !project) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <p className="text-red-800">Failed to load project: {String(error)}</p>
      </div>
    )
  }

  const handleExecute = () => {
    setShowExecuteDialog(true)
  }

  const confirmExecute = () => {
    setShowExecuteDialog(false)
    executeMutation.mutate({ project_id: project.id })
  }

  const handleDelete = () => {
    setShowDeleteDialog(true)
  }

  const confirmDelete = () => {
    setShowDeleteDialog(false)
    deleteMutation.mutate(project.id)
  }

  return (
    <div>
      {/* Header */}
      <div className="flex justify-between items-start mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">{project.name}</h2>
          <p className="text-sm text-gray-500 mt-1">
            Created {new Date(project.created_at).toLocaleString()}
          </p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={handleExecute}
            disabled={executeMutation.isPending}
            className="px-4 py-2 bg-primary-600 text-white rounded-md text-sm font-medium hover:bg-primary-700 disabled:opacity-50"
          >
            {executeMutation.isPending ? 'Starting...' : 'Run Pipeline'}
          </button>
          <button
            onClick={handleDelete}
            disabled={deleteMutation.isPending}
            className="px-4 py-2 bg-red-600 text-white rounded-md text-sm font-medium hover:bg-red-700 disabled:opacity-50"
          >
            Delete
          </button>
        </div>
      </div>

      {/* Pipeline Progress */}
      {showProgress && (
        <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Pipeline Progress
            {isConnected && (
              <span className="ml-2 inline-flex items-center">
                <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse mr-2"></span>
                <span className="text-sm font-normal text-gray-500">Live</span>
              </span>
            )}
          </h3>
          <PipelineProgress data={progressData} />
        </div>
      )}

      {/* Video Player - Show when complete */}
      {project.current_stage === 'complete' && project.output_path && (
        <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Generated Video</h3>
          <VideoPlayer projectId={project.id} projectName={project.name} />
        </div>
      )}

      {/* Project Details */}
      <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Configuration</h3>
        <dl className="grid grid-cols-2 gap-4">
          <div>
            <dt className="text-sm font-medium text-gray-500">Audience</dt>
            <dd className="text-sm text-gray-900 mt-1">{project.audience}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Target Length</dt>
            <dd className="text-sm text-gray-900 mt-1">{project.target_length}s</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Repository</dt>
            <dd className="text-sm text-gray-900 mt-1">
              {project.repo_url ? (
                <a href={project.repo_url} target="_blank" rel="noopener noreferrer" className="text-primary-600 hover:underline">
                  {project.repo_url}
                </a>
              ) : (
                'N/A'
              )}
            </dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Website</dt>
            <dd className="text-sm text-gray-900 mt-1">
              {project.website_url ? (
                <a href={project.website_url} target="_blank" rel="noopener noreferrer" className="text-primary-600 hover:underline">
                  {project.website_url}
                </a>
              ) : (
                'N/A'
              )}
            </dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Current Stage</dt>
            <dd className="text-sm text-gray-900 mt-1">
              <span className={`inline-block px-2 py-1 rounded text-xs font-medium ${
                project.current_stage === 'complete'
                  ? 'bg-green-100 text-green-800'
                  : project.current_stage === 'failed'
                  ? 'bg-red-100 text-red-800'
                  : 'bg-blue-100 text-blue-800'
              }`}>
                {project.current_stage}
              </span>
            </dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Output Path</dt>
            <dd className="text-sm text-gray-900 mt-1">{project.output_path || 'Not generated yet'}</dd>
          </div>
        </dl>
      </div>

      {/* Analysis Results */}
      {project.analysis && (
        <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Analysis</h3>
          <dl className="space-y-3">
            <div>
              <dt className="text-sm font-medium text-gray-500">Product</dt>
              <dd className="text-sm text-gray-900 mt-1">{project.analysis.product_name}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Tagline</dt>
              <dd className="text-sm text-gray-900 mt-1">{project.analysis.tagline}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Category</dt>
              <dd className="text-sm text-gray-900 mt-1">{project.analysis.category}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Key Features</dt>
              <dd className="text-sm text-gray-900 mt-1">
                <ul className="list-disc list-inside space-y-1">
                  {project.analysis.key_features.filter(f => f.demo_worthy).map((feature, i) => (
                    <li key={i}>{feature.name}</li>
                  ))}
                </ul>
              </dd>
            </div>
          </dl>
        </div>
      )}

      {/* Script */}
      {project.script && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Script</h3>
          <p className="text-sm text-gray-600 mb-4">
            {project.script.scenes.length} scenes • {project.script.total_duration}s duration
          </p>
          <div className="space-y-3">
            {project.script.scenes.map((scene, i) => (
              <div key={scene.id} className="border-l-4 border-primary-500 pl-4">
                <p className="text-xs font-medium text-gray-500 mb-1">
                  Scene {i + 1} • {scene.scene_type} • {scene.duration_seconds}s
                </p>
                <p className="text-sm text-gray-900">{scene.narration}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Confirmation Dialogs */}
      <ConfirmDialog
        isOpen={showExecuteDialog}
        title="Start Pipeline Execution?"
        message="This will analyze the repository/website, generate a script, capture screenshots, synthesize voice narration, and assemble the final video. This may take several minutes."
        confirmLabel="Start Pipeline"
        cancelLabel="Cancel"
        onConfirm={confirmExecute}
        onCancel={() => setShowExecuteDialog(false)}
        variant="primary"
      />

      <ConfirmDialog
        isOpen={showDeleteDialog}
        title="Delete Project?"
        message="This will permanently delete this project and all associated data. This action cannot be undone."
        confirmLabel="Delete Project"
        cancelLabel="Cancel"
        onConfirm={confirmDelete}
        onCancel={() => setShowDeleteDialog(false)}
        variant="danger"
      />
    </div>
  )
}
