/**
 * Inline form error message component
 */
import { AlertCircle } from 'lucide-react'

interface FormErrorProps {
  message?: string | null
  className?: string
}

export function FormError({ message, className = '' }: FormErrorProps) {
  if (!message) return null

  return (
    <div className={`flex items-start gap-2 text-sm text-red-600 mt-1 ${className}`}>
      <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
      <span>{message}</span>
    </div>
  )
}
