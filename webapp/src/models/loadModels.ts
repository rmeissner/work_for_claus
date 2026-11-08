import { buildModels } from './buildModels'
import type { Model } from './types'

const projects = import.meta.glob<unknown>('../../../models/*/project.json', {
  eager: true,
  import: 'default',
})

const stls = import.meta.glob<string>('../../../models/*/*.stl', {
  eager: true,
  query: '?url',
  import: 'default',
})

/** Returns every valid model in the repository's `models/` folder, sorted by name. */
export function loadModels(): Model[] {
  return buildModels(projects, stls)
}
