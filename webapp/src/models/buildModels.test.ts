import { afterEach, describe, expect, it, vi } from 'vitest'
import { buildModels } from './buildModels'
import { loadModels } from './loadModels'

const root = '../../../models'

describe('buildModels', () => {
  const warn = vi.spyOn(console, 'warn').mockImplementation(() => {})
  afterEach(() => warn.mockClear())

  const project = (files: unknown, extra = {}) => ({
    [`${root}/cube/project.json`]: { name: 'Cube', version: '1.0', description: 'A cube.', files, ...extra },
  })

  it('builds a model per valid folder and ignores unknown keys', () => {
    const models = buildModels(project([{ file: 'cube.stl' }], { extra: 1 }), {
      [`${root}/cube/cube.stl`]: '/assets/cube.stl',
    })
    expect(models).toEqual([
      {
        slug: 'cube',
        name: 'Cube',
        version: '1.0',
        description: 'A cube.',
        files: [{ name: 'cube.stl', fileName: 'cube.stl', url: '/assets/cube.stl' }],
      },
    ])
    expect(warn).not.toHaveBeenCalled()
  })

  it('keeps the project.json order and uses name or falls back to the file name', () => {
    const models = buildModels(project([{ file: 'b.stl', name: 'Part B' }, { file: 'a.stl' }]), {
      [`${root}/cube/a.stl`]: '/a.stl',
      [`${root}/cube/b.stl`]: '/b.stl',
    })
    expect(models[0].files).toEqual([
      { name: 'Part B', fileName: 'b.stl', url: '/b.stl' },
      { name: 'a.stl', fileName: 'a.stl', url: '/a.stl' },
    ])
  })

  it('skips a folder without project.json', () => {
    expect(buildModels({}, { [`${root}/cube/cube.stl`]: '/cube.stl' })).toEqual([])
    expect(warn).toHaveBeenCalledWith(expect.stringContaining('missing project.json'))
  })

  it('skips a model when none of its listed files exists', () => {
    expect(buildModels(project([{ file: 'cube.stl' }]), {})).toEqual([])
    expect(warn).toHaveBeenCalledWith(expect.stringContaining('cube.stl not found'))
    expect(warn).toHaveBeenCalledWith(expect.stringContaining('no STL file'))
  })

  it('drops a listed file that does not exist', () => {
    const models = buildModels(project([{ file: 'a.stl' }, { file: 'gone.stl' }]), {
      [`${root}/cube/a.stl`]: '/a.stl',
    })
    expect(models[0].files.map((f) => f.fileName)).toEqual(['a.stl'])
    expect(warn).toHaveBeenCalledWith(expect.stringContaining('gone.stl not found'))
  })

  it('warns about an unlisted STL and ignores it', () => {
    const models = buildModels(project([{ file: 'a.stl' }]), {
      [`${root}/cube/a.stl`]: '/a.stl',
      [`${root}/cube/b.stl`]: '/b.stl',
    })
    expect(models[0].files.map((f) => f.fileName)).toEqual(['a.stl'])
    expect(warn).toHaveBeenCalledWith(expect.stringContaining('b.stl is not listed'))
  })

  it.each([
    ['null', null],
    ['a missing name', { version: '1.0', description: 'x', files: [{ file: 'cube.stl' }] }],
    ['a missing version', { name: 'Cube', description: 'x', files: [{ file: 'cube.stl' }] }],
    ['an empty version', { name: 'Cube', version: ' ', description: 'x', files: [{ file: 'cube.stl' }] }],
    ['an empty name', { name: '  ', version: '1.0', description: 'x', files: [{ file: 'cube.stl' }] }],
    ['a non-string description', { name: 'Cube', version: '1.0', description: 3, files: [{ file: 'cube.stl' }] }],
    ['missing files', { name: 'Cube', version: '1.0', description: 'x' }],
    ['empty files', { name: 'Cube', version: '1.0', description: 'x', files: [] }],
    ['files that is not an array', { name: 'Cube', version: '1.0', description: 'x', files: 'cube.stl' }],
    ['an entry without a file', { name: 'Cube', version: '1.0', description: 'x', files: [{ name: 'Cube' }] }],
    ['a non-.stl entry', { name: 'Cube', version: '1.0', description: 'x', files: [{ file: 'cube.3mf' }] }],
    ['a path with a slash', { name: 'Cube', version: '1.0', description: 'x', files: [{ file: 'sub/cube.stl' }] }],
    [
      'a duplicate entry',
      { name: 'Cube', version: '1.0', description: 'x', files: [{ file: 'cube.stl' }, { file: 'cube.stl' }] },
    ],
  ])('skips a project.json with %s', (_, invalid) => {
    const models = buildModels(
      { [`${root}/cube/project.json`]: invalid },
      { [`${root}/cube/cube.stl`]: '/cube.stl' },
    )
    expect(models).toEqual([])
    expect(warn).toHaveBeenCalledWith(
      expect.stringContaining('invalid project.json'),
      expect.any(String),
    )
  })

  it('sorts models by name', () => {
    const models = buildModels(
      {
        [`${root}/z/project.json`]: { name: 'apple', version: '1.0', description: '', files: [{ file: 'z.stl' }] },
        [`${root}/a/project.json`]: { name: 'Zebra', version: '1.0', description: '', files: [{ file: 'a.stl' }] },
        [`${root}/m/project.json`]: { name: 'Mango', version: '1.0', description: '', files: [{ file: 'm.stl' }] },
      },
      { [`${root}/z/z.stl`]: '/z', [`${root}/a/a.stl`]: '/a', [`${root}/m/m.stl`]: '/m' },
    )
    expect(models.map((m) => m.name)).toEqual(['apple', 'Mango', 'Zebra'])
  })
})

describe('loadModels', () => {
  it('finds the sample models in the repository', () => {
    const models = loadModels()
    expect(models.map((m) => m.slug)).toEqual(['star-24', 'calibration-cube', 'glider', 'pyramid', 'star-destroyer', 'star-ornament'])
    for (const model of models) {
      expect(model.files.length).toBeGreaterThan(0)
      for (const file of model.files) expect(file.url).toMatch(/\.stl/)
    }
  })
})
