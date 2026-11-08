import type { Model } from './types'

/** Returns the model folder name for a glob key like `../../../models/<slug>/file`. */
function slugOf(path: string): string | undefined {
  return path.match(/(?:^|\/)models\/([^/]+)\/[^/]+$/)?.[1]
}

function isProject(value: unknown): value is { name: string; description: string } {
  if (typeof value !== 'object' || value === null) return false
  const { name, description } = value as Record<string, unknown>
  return typeof name === 'string' && name.trim() !== '' && typeof description === 'string'
}

/**
 * Groups `import.meta.glob` results by model folder and validates them.
 * Invalid folders are skipped with a warning; the result is sorted by name.
 */
export function buildModels(
  projects: Record<string, unknown>,
  stls: Record<string, string>,
): Model[] {
  const projectBySlug = new Map<string, unknown>()
  for (const [path, project] of Object.entries(projects)) {
    const slug = slugOf(path)
    if (slug) projectBySlug.set(slug, project)
  }

  const stlPathsBySlug = new Map<string, string[]>()
  for (const path of Object.keys(stls)) {
    const slug = slugOf(path)
    if (slug) stlPathsBySlug.set(slug, [...(stlPathsBySlug.get(slug) ?? []), path])
  }

  const slugs = new Set([...projectBySlug.keys(), ...stlPathsBySlug.keys()])
  const models: Model[] = []
  for (const slug of slugs) {
    const project = projectBySlug.get(slug)
    if (project === undefined) {
      console.warn(`models/${slug}: missing project.json, skipping`)
      continue
    }
    if (!isProject(project)) {
      console.warn(`models/${slug}: invalid project.json, skipping`)
      continue
    }
    const stlPaths = (stlPathsBySlug.get(slug) ?? []).sort()
    if (stlPaths.length === 0) {
      console.warn(`models/${slug}: no STL file, skipping`)
      continue
    }
    if (stlPaths.length > 1) {
      console.warn(`models/${slug}: several STL files, using ${stlPaths[0]}`)
    }
    models.push({
      slug,
      name: project.name,
      description: project.description,
      stlUrl: stls[stlPaths[0]],
    })
  }

  return models.sort((a, b) => a.name.localeCompare(b.name))
}
