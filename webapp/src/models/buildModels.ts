import { z } from 'zod'
import type { Model, ModelFile } from './types'

/** Returns the model folder name for a glob key like `../../../models/<slug>/file`. */
function slugOf(path: string): string | undefined {
  return path.match(/(?:^|\/)models\/([^/]+)\/[^/]+$/)?.[1]
}

/** Schema for `project.json`. Unknown keys are allowed and dropped. */
const projectSchema = z.object({
  name: z.string().refine((name) => name.trim() !== '', 'name must not be empty'),
  version: z.string().refine((version) => version.trim() !== '', 'version must not be empty'),
  description: z.string(),
  files: z
    .array(
      z.object({
        file: z
          .string()
          .refine((file) => !file.includes('/'), 'file must be a plain file name')
          .refine((file) => /\.stl$/i.test(file), 'file must end in .stl'),
        name: z.string().optional(),
      }),
    )
    .min(1)
    .refine(
      (files) => new Set(files.map((entry) => entry.file)).size === files.length,
      'files must not contain duplicates',
    ),
})

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
    const parsed = projectSchema.safeParse(project)
    if (!parsed.success) {
      console.warn(`models/${slug}: invalid project.json, skipping`, z.prettifyError(parsed.error))
      continue
    }
    const stlPaths = stlPathsBySlug.get(slug) ?? []
    const urlByFileName = new Map(stlPaths.map((path) => [path.split('/').pop()!, stls[path]]))
    const files: ModelFile[] = []
    for (const { file, name } of parsed.data.files) {
      const url = urlByFileName.get(file)
      if (url === undefined) {
        console.warn(`models/${slug}: listed file ${file} not found, ignoring it`)
        continue
      }
      files.push({ name: name ?? file, fileName: file, url })
    }
    for (const fileName of urlByFileName.keys()) {
      if (!parsed.data.files.some((entry) => entry.file === fileName)) {
        console.warn(`models/${slug}: ${fileName} is not listed in project.json, ignoring it`)
      }
    }
    if (files.length === 0) {
      console.warn(`models/${slug}: no STL file, skipping`)
      continue
    }
    models.push({
      slug,
      name: parsed.data.name,
      version: parsed.data.version,
      description: parsed.data.description,
      files,
    })
  }

  return models.sort((a, b) => a.name.localeCompare(b.name))
}
