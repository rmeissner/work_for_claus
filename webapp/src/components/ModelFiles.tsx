import { useId, useState } from 'react'
import type { ModelFile } from '../models/types'

export const VISIBLE_FILES = 3

/** Download links for a model's files; the first few, the rest on demand. */
export function ModelFiles({ files }: { files: ModelFile[] }) {
  const [expanded, setExpanded] = useState(false)
  const listId = useId()
  const hidden = files.length - VISIBLE_FILES
  const shown = expanded ? files : files.slice(0, VISIBLE_FILES)

  return (
    <section aria-labelledby={`${listId}-heading`} className="mt-4">
      <h3 id={`${listId}-heading`} className="m-0 mb-2 font-semibold">
        Files
      </h3>
      <ul id={listId} className="m-0 list-none p-0">
        {shown.map((file) => (
          <li key={file.fileName}>
            <a
              href={file.url}
              download={file.fileName}
              className="flex items-baseline gap-3 rounded-item px-1 py-1 text-accent hover:bg-hover"
            >
              <span>{file.name}</span>
              <span className="text-muted">{file.fileName}</span>
            </a>
          </li>
        ))}
      </ul>
      {hidden > 0 && (
        <button
          type="button"
          aria-expanded={expanded}
          aria-controls={listId}
          className="mt-1 cursor-pointer rounded-item border border-border bg-transparent px-3 py-1 text-inherit hover:bg-hover"
          onClick={() => setExpanded((value) => !value)}
        >
          {expanded ? 'Show less' : `Show ${hidden} more`}
        </button>
      )}
    </section>
  )
}
