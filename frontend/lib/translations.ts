/**
 * i18n translations for CN/EN.
 */

export const translations = {
  'en-US': {
    nav: {
      ingest: 'Ingest',
      playbook: 'Playbook',
      alerts: 'Alerts',
      scoreboard: 'Scoreboard',
    },
    ingest: {
      title: 'Ingest Transcript',
      subtitle: 'Paste your weekly lesson transcript to generate playbook cards',
      placeholder: 'Paste transcript here (supports CN/EN mixed)...',
      expertRef: 'Expert/Source Reference',
      submit: 'Extract Cards',
      processing: 'Processing...',
      draftCards: 'Draft Cards',
      noCards: 'No cards generated yet',
      entities: 'Entities Extracted',
      processingTime: 'Processing Time',
    },
    playbook: {
      title: 'This Week\'s Playbook',
      subtitle: 'Tradable cards with entry/exit triggers',
      noCards: 'No cards available',
      direction: 'Direction',
      horizon: 'Horizon',
      confidence: 'Confidence',
      instruments: 'Instruments',
      entryTrigger: 'Entry Trigger',
      invalidator: 'Invalidator',
      catalysts: 'Catalysts',
      risks: 'Risks',
      why: 'Why',
      similar: 'Similar Tickers',
      follow: 'Follow',
      enableAlerts: 'Enable Alerts',
      addToPaper: 'Add to Paper',
    },
    alerts: {
      title: 'Alerts',
      subtitle: 'Recent trigger events',
      noAlerts: 'No alerts',
      addPosition: 'Add Position',
      ignore: 'Ignore',
    },
    scoreboard: {
      title: 'Scoreboard',
      subtitle: 'Paper portfolio performance',
      totalPnL: 'Total P&L',
      winRate: 'Win Rate',
      maxDrawdown: 'Max Drawdown',
      twr: 'TWR',
      positions: 'Positions',
      open: 'Open',
      closed: 'Closed',
      noPositions: 'No positions yet',
    },
    common: {
      loading: 'Loading...',
      error: 'Error',
      success: 'Success',
      cancel: 'Cancel',
      save: 'Save',
      delete: 'Delete',
      edit: 'Edit',
      close: 'Close',
    },
  },
  'zh-CN': {
    nav: {
      ingest: '导入',
      playbook: '交易本',
      alerts: '提醒',
      scoreboard: '成绩单',
    },
    ingest: {
      title: '导入课程',
      subtitle: '粘贴每周课程文字稿，生成交易卡片',
      placeholder: '在此粘贴课程内容（支持中英文混合）...',
      expertRef: '专家/来源',
      submit: '提取卡片',
      processing: '处理中...',
      draftCards: '草稿卡片',
      noCards: '尚未生成卡片',
      entities: '提取实体',
      processingTime: '处理时间',
    },
    playbook: {
      title: '本周交易本',
      subtitle: '可交易卡片，含入场/止损触发条件',
      noCards: '暂无卡片',
      direction: '方向',
      horizon: '时间',
      confidence: '信心',
      instruments: '标的',
      entryTrigger: '入场触发',
      invalidator: '失效条件',
      catalysts: '催化剂',
      risks: '风险',
      why: '理由',
      similar: '相似标的',
      follow: '关注',
      enableAlerts: '开启提醒',
      addToPaper: '加入模拟',
    },
    alerts: {
      title: '提醒',
      subtitle: '最近触发事件',
      noAlerts: '暂无提醒',
      addPosition: '建仓',
      ignore: '忽略',
    },
    scoreboard: {
      title: '成绩单',
      subtitle: '模拟组合表现',
      totalPnL: '总盈亏',
      winRate: '胜率',
      maxDrawdown: '最大回撤',
      twr: '时间加权回报',
      positions: '持仓',
      open: '持有',
      closed: '已平仓',
      noPositions: '暂无持仓',
    },
    common: {
      loading: '加载中...',
      error: '错误',
      success: '成功',
      cancel: '取消',
      save: '保存',
      delete: '删除',
      edit: '编辑',
      close: '关闭',
    },
  },
};

export type Locale = 'en-US' | 'zh-CN';

export function t(locale: Locale, key: string): string {
  const keys = key.split('.');
  let value: any = translations[locale];

  for (const k of keys) {
    value = value?.[k];
  }

  return value || key;
}
