import { afterEach, describe, expect, it, vi } from 'vitest'
import { buildModels } from './buildModels'
import { loadModels } from './loadModels'

const root = '../../../models'

describe('buildModels', () => {
  const warn = vi.spyOn(console, 'warn').mockImplementation(() => {})
  afterEach(() => warn.mockClear())

  it('builds a model per valid folder and ignores unknown keys', () => {
    const models = buildModels(
      { [`${root}/cube/project.json`]: { name: 'Cube', description: 'A cube.', extra: 1 } },
      { [`${root}/cube/cube.stl`]: '/assets/cube.stl' },
    )
    expect(models).toEqual([
      { slug: 'cube', name: 'Cube', description: 'A cube.', stlUrl: '/assets/cube.stl' },
    ])
    expect(warn).not.toHaveBeenCalled()
  })

  it('skips a folder without project.json', () => {
    expect(buildModels({}, { [`${root}/cube/cube.stl`]: '/cube.stl' })).toEqual([])
    expect(warn).toHaveBeenCalledWith(expect.stringContaining('missing project.json'))
  })

  it('skips a folder without an STL file', () => {
    const projects = { [`${root}/cube/project.json`]: { name: 'Cube', description: '' } }
    expect(buildModels(projects, {})).toEqual([])
    expect(warn).toHaveBeenCalledWith(expect.stringContaining('no STL file'))
  })

  it.each([
    ['null', null],
    ['a missing name', { description: 'x' }],
    ['an empty name', { name: '  ', description: 'x' }],
    ['a non-string description', { name: 'Cube', description: 3 }],
  ])('skips a project.json with %s', (_, project) => {
    const models = buildModels(
      { [`${root}/cube/project.json`]: project },
      { [`${root}/cube/cube.stl`]: '/cube.stl' },
    )
    expect(models).toEqual([])
    expect(warn).toHaveBeenCalledWith(
      expect.stringContaining('invalid project.json'),
      expect.any(String),
    )
  })

  it('uses the first STL alphabetically when a folder has several', () => {
    const models = buildModels(
      { [`${root}/cube/project.json`]: { name: 'Cube', description: '' } },
      { [`${root}/cube/b.stl`]: '/b.stl', [`${root}/cube/a.stl`]: '/a.stl' },
    )
    expect(models.map((m) => m.stlUrl)).toEqual(['/a.stl'])
    expect(warn).toHaveBeenCalledWith(expect.stringContaining('several STL files'))
  })

  it('sorts models by name', () => {
    const models = buildModels(
      {
        [`${root}/z/project.json`]: { name: 'apple', description: '' },
        [`${root}/a/project.json`]: { name: 'Zebra', description: '' },
        [`${root}/m/project.json`]: { name: 'Mango', description: '' },
      },
      { [`${root}/z/z.stl`]: '/z', [`${root}/a/a.stl`]: '/a', [`${root}/m/m.stl`]: '/m' },
    )
    expect(models.map((m) => m.name)).toEqual(['apple', 'Mango', 'Zebra'])
  })
})

describe('loadModels', () => {
  it('finds the sample models in the repository', () => {
    const models = loadModels()
    expect(models.map((m) => m.slug)).toEqual(['calibration-cube', 'pyramid'])
    for (const model of models) expect(model.stlUrl).toMatch(/\.stl/)
  })
})
