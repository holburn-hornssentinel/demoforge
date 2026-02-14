/**
 * Video player component with download button and analytics tracking
 */
import { useRef, useEffect } from 'react'
import { Download, Play } from 'lucide-react'

interface VideoPlayerProps {
  projectId: string
  projectName: string
  className?: string
}

async function trackViewEvent(
  projectId: string,
  eventType: string,
  progress: number = 0,
  duration: number | null = null
) {
  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:7500'
  try {
    await fetch(`${apiUrl}/api/analytics/view`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ project_id: projectId, event_type: eventType, progress, duration }),
    })
  } catch (error) {
    console.error('Failed to track view event:', error)
  }
}

export function VideoPlayer({ projectId, projectName, className = '' }: VideoPlayerProps) {
  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:7500'
  const videoUrl = `${apiUrl}/api/projects/${projectId}/video`
  const videoRef = useRef<HTMLVideoElement>(null)

  useEffect(() => {
    const video = videoRef.current
    if (!video) return

    // Track play event
    const handlePlay = () => {
      trackViewEvent(projectId, 'play', 0, video.duration)
    }

    // Track pause event
    const handlePause = () => {
      const progress = video.currentTime / video.duration
      trackViewEvent(projectId, 'pause', progress, video.duration)
    }

    // Track completion (when video reaches 95%)
    const handleTimeUpdate = () => {
      const progress = video.currentTime / video.duration
      if (progress >= 0.95) {
        trackViewEvent(projectId, 'complete', 1.0, video.duration)
        // Remove listener after first completion
        video.removeEventListener('timeupdate', handleTimeUpdate)
      }
    }

    // Add event listeners
    video.addEventListener('play', handlePlay)
    video.addEventListener('pause', handlePause)
    video.addEventListener('timeupdate', handleTimeUpdate)

    return () => {
      video.removeEventListener('play', handlePlay)
      video.removeEventListener('pause', handlePause)
      video.removeEventListener('timeupdate', handleTimeUpdate)
    }
  }, [projectId])

  const handleDownload = () => {
    const link = document.createElement('a')
    link.href = videoUrl
    link.download = `${projectName.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_demo.mp4`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Video Player */}
      <div className="relative rounded-lg overflow-hidden bg-black aspect-video">
        <video
          ref={videoRef}
          controls
          className="w-full h-full"
          preload="metadata"
        >
          <source src={videoUrl} type="video/mp4" />
          Your browser does not support the video tag.
        </video>
      </div>

      {/* Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center text-sm text-gray-600">
          <Play className="w-4 h-4 mr-1.5" />
          <span>MP4 • HD Quality</span>
        </div>

        <button
          onClick={handleDownload}
          className="inline-flex items-center px-4 py-2 bg-primary-600 text-white rounded-md text-sm font-medium hover:bg-primary-700 transition-colors"
        >
          <Download className="w-4 h-4 mr-2" />
          Download Video
        </button>
      </div>

      {/* Video Info */}
      <div className="text-xs text-gray-500 border-t border-gray-200 pt-3">
        <p>
          This video was generated automatically by DemoForge. Share it anywhere or download for offline use.
        </p>
      </div>
    </div>
  )
}
