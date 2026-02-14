/**
 * Pipeline progress visualization component
 * Shows real-time progress through SSE for the 5-stage pipeline
 */
import { CheckCircle2, Circle, Loader2, XCircle } from 'lucide-react'

export type PipelineStage = 'analyze' | 'script' | 'capture' | 'voice' | 'assemble' | 'complete' | 'failed'

export interface PipelineProgressData {
  stage: PipelineStage
  progress: number // 0-1
  message: string
  error?: string
  current_scene?: number
  total_scenes?: number
}

interface PipelineProgressProps {
  data: PipelineProgressData | null
  className?: string
}

const STAGES = [
  { id: 'analyze', label: 'Analyze', icon: '🔍' },
  { id: 'script', label: 'Script', icon: '📝' },
  { id: 'capture', label: 'Capture', icon: '📸' },
  { id: 'voice', label: 'Voice', icon: '🎙️' },
  { id: 'assemble', label: 'Assemble', icon: '🎬' },
] as const

export function PipelineProgress({ data, className = '' }: PipelineProgressProps) {
  if (!data) {
    return null
  }

  const currentStageIndex = STAGES.findIndex((s) => s.id === data.stage)
  const isFailed = data.stage === 'failed'
  const isComplete = data.stage === 'complete'

  const getStageStatus = (index: number) => {
    if (isFailed && index === currentStageIndex) return 'error'
    if (isComplete) return 'complete'
    if (index < currentStageIndex) return 'complete'
    if (index === currentStageIndex) return 'active'
    return 'pending'
  }

  const getStageIcon = (index: number) => {
    const status = getStageStatus(index)

    if (status === 'error') {
      return <XCircle className="w-6 h-6 text-red-500" />
    }
    if (status === 'complete') {
      return <CheckCircle2 className="w-6 h-6 text-green-500" />
    }
    if (status === 'active') {
      return <Loader2 className="w-6 h-6 text-blue-500 animate-spin" />
    }
    return <Circle className="w-6 h-6 text-gray-300" />
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Stage Stepper */}
      <div className="flex items-center justify-between">
        {STAGES.map((stage, index) => {
          const status = getStageStatus(index)
          const isLast = index === STAGES.length - 1

          return (
            <div key={stage.id} className="flex items-center flex-1">
              {/* Stage Circle */}
              <div className="flex flex-col items-center">
                <div
                  className={`
                    flex items-center justify-center w-12 h-12 rounded-full border-2
                    ${status === 'complete' ? 'border-green-500 bg-green-50' : ''}
                    ${status === 'active' ? 'border-blue-500 bg-blue-50' : ''}
                    ${status === 'error' ? 'border-red-500 bg-red-50' : ''}
                    ${status === 'pending' ? 'border-gray-300 bg-gray-50' : ''}
                  `}
                >
                  {getStageIcon(index)}
                </div>
                <span
                  className={`
                    mt-2 text-sm font-medium
                    ${status === 'complete' ? 'text-green-700' : ''}
                    ${status === 'active' ? 'text-blue-700' : ''}
                    ${status === 'error' ? 'text-red-700' : ''}
                    ${status === 'pending' ? 'text-gray-500' : ''}
                  `}
                >
                  {stage.label}
                </span>
              </div>

              {/* Connector Line */}
              {!isLast && (
                <div
                  className={`
                    flex-1 h-0.5 mx-2
                    ${status === 'complete' ? 'bg-green-500' : 'bg-gray-300'}
                  `}
                />
              )}
            </div>
          )
        })}
      </div>

      {/* Progress Bar */}
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="font-medium text-gray-700">{data.message}</span>
          <span className="text-gray-500">{Math.round(data.progress * 100)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
          <div
            className={`
              h-full rounded-full transition-all duration-300 ease-out
              ${isFailed ? 'bg-red-500' : 'bg-blue-500'}
            `}
            style={{ width: `${data.progress * 100}%` }}
          />
        </div>
      </div>

      {/* Scene Counter */}
      {data.current_scene && data.total_scenes && (
        <div className="text-sm text-gray-600 text-center">
          Processing scene {data.current_scene} of {data.total_scenes}
        </div>
      )}

      {/* Error Message */}
      {isFailed && data.error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-start">
            <XCircle className="w-5 h-5 text-red-500 mt-0.5 mr-2 flex-shrink-0" />
            <div>
              <h4 className="font-medium text-red-900">Pipeline Failed</h4>
              <p className="mt-1 text-sm text-red-700">{data.error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Success Message */}
      {isComplete && (
        <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-start">
            <CheckCircle2 className="w-5 h-5 text-green-500 mt-0.5 mr-2 flex-shrink-0" />
            <div>
              <h4 className="font-medium text-green-900">Demo Video Complete!</h4>
              <p className="mt-1 text-sm text-green-700">
                Your demo video has been generated successfully
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
