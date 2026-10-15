import { describe, expect, it } from 'vitest'

import { roleHomePath } from './role-home'

describe('roleHomePath', () => {
  it('maps every role to its own workspace', () => {
    expect(roleHomePath('user')).toBe('/forum')
    expect(roleHomePath('content_reviewer')).toBe('/moderation')
    expect(roleHomePath('appeal_reviewer')).toBe('/appeals')
  })
})

