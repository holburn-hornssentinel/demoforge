/**
 * TypeScript types mirroring Python Pydantic models
 */

export type AudienceType = 'investor' | 'customer' | 'developer' | 'technical'

export type PipelineStage =
  | 'analyze'
  | 'script'
  | 'capture'
  | 'voice'
  | 'assemble'
  | 'complete'
  | 'failed'

export type SceneType = 'screenshot' | 'title_card' | 'code_snippet' | 'diagram'

export interface ProductFeature {
  name: string
  description: string
  importance: number
  demo_worthy: boolean
}

export interface AnalysisResult {
  product_name: string
  tagline: string
  category: string
  target_users: string[]
  key_features: ProductFeature[]
  tech_stack: string[]
  use_cases: string[]
  competitive_advantage: string
  github_url?: string
  website_url?: string
  demo_urls: string[]
  analyzed_at: string
}

export interface Scene {
  id: string
  scene_type: SceneType
  narration: string
  duration_seconds: number
  url?: string
  visual_content: string
  actions: unknown[]
  metadata: Record<string, unknown>
}

export interface DemoScript {
  title: string
  audience: AudienceType
  total_duration: number
  scenes: Scene[]
  intro: string
  outro: string
  call_to_action: string
  generated_at: string
}

export interface PipelineProgress {
  stage: PipelineStage
  progress: number
  message: string
  current_scene: number
  total_scenes: number
  error?: string
  started_at: string
  updated_at: string
}

export interface Project {
  id: string
  name: string
  created_at: string
  updated_at: string
  repo_url?: string
  website_url?: string
  audience: AudienceType
  target_length: number
  current_stage: PipelineStage
  output_path?: string
}

export interface ProjectState extends Project {
  analysis?: AnalysisResult
  script?: DemoScript
  progress?: PipelineProgress
  cache_hash: string
}

export interface CreateProjectRequest {
  name: string
  repo_url?: string
  website_url?: string
  audience: AudienceType
  target_length: number
}

export interface ExecutePipelineRequest {
  project_id: string
}
