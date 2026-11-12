import type { RiskLevel } from '../types/content'

export const riskLevelLabels: Record<RiskLevel, string> = {
  L0: 'L0 · 明确正常（允许发布）',
  L1: 'L1 · 轻微或边界风险（允许发布）',
  L2: 'L2 · 无法确定（需人工判断，不能作为终态）',
  L3: 'L3 · 明确违规（拒绝发布）',
  L4: 'L4 · 严重违法或高危（拒绝发布）',
}

export const riskLevelHints: Record<RiskLevel, string> = {
  L0: '内容明确正常。确认后可通过并发布；申诉复核时可通过申诉。',
  L1: '存在轻微或边界风险，但仍在允许发布范围内。确认后可通过并发布；申诉复核时可通过申诉。',
  L2: '当前无法稳定判断，需要人工结合原文与上下文进一步判断。请调整为 L0/L1 或 L3/L4，再作出最终决定。',
  L3: '内容明确违规。确认后应拒绝发布；申诉复核时应驳回申诉。',
  L4: '内容涉及严重违法或高危风险。确认后应拒绝发布；申诉复核时应驳回申诉。',
}
