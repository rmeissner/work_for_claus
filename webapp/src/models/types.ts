export interface ModelFile {
  /** Label from project.json, or the file name. */
  name: string
  /** File name in the model folder, used as the download name. */
  fileName: string
  url: string
}

export interface Model {
  /** Folder name under `models/`. */
  slug: string
  name: string
  /** Hand-maintained version from project.json, e.g. "1.0". */
  version: string
  description: string
  /** In project.json order; never empty. */
  files: ModelFile[]
}
