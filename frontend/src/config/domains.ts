export type DomainType =
  | 'medical'
  | 'finance'
  | 'cyber'
  | 'agriculture'
  | 'marketing'
  | 'logistics'
  | 'education'
  | 'retail'
  | 'manufacturing'
  | 'energy'
  | 'general';

export interface DomainConfig {
  name: string;
  color: string;
  gradientFrom: string;
  gradientTo: string;
  icon: string;
  chartType: string[];
  kpis: string[];
}

export const DOMAIN_CONFIGS: Record<DomainType, DomainConfig> = {
  medical: {
    name: 'Medical',
    color: '#3B82F6',
    gradientFrom: '#3B82F6',
    gradientTo: '#1D4ED8',
    icon: 'Activity',
    chartType: ['line', 'bar', 'scatter'],
    kpis: ['Heart Rate', 'Blood Pressure', 'Temperature', 'SpO2']
  },
  finance: {
    name: 'Finance',
    color: '#10B981',
    gradientFrom: '#10B981',
    gradientTo: '#059669',
    icon: 'TrendingUp',
    chartType: ['candlestick', 'line', 'area'],
    kpis: ['Revenue', 'Profit', 'Cash Flow', 'ROI']
  },
  cyber: {
    name: 'Cybersecurity',
    color: '#8B5CF6',
    gradientFrom: '#8B5CF6',
    gradientTo: '#6D28D9',
    icon: 'Shield',
    chartType: ['heatmap', 'network', 'timeline'],
    kpis: ['Threats Detected', 'Response Time', 'Incidents', 'Vulnerabilities']
  },
  agriculture: {
    name: 'Agriculture',
    color: '#22C55E',
    gradientFrom: '#22C55E',
    gradientTo: '#16A34A',
    icon: 'Sprout',
    chartType: ['bar', 'line', 'area'],
    kpis: ['Yield', 'Soil Moisture', 'Rainfall', 'Temperature']
  },
  marketing: {
    name: 'Marketing',
    color: '#F59E0B',
    gradientFrom: '#F59E0B',
    gradientTo: '#D97706',
    icon: 'Target',
    chartType: ['funnel', 'pie', 'bar'],
    kpis: ['Conversion Rate', 'CTR', 'Engagement', 'ROI']
  },
  logistics: {
    name: 'Logistics',
    color: '#EC4899',
    gradientFrom: '#EC4899',
    gradientTo: '#DB2777',
    icon: 'Truck',
    chartType: ['map', 'timeline', 'bar'],
    kpis: ['Delivery Time', 'Fleet Utilization', 'Cost per Mile', 'On-Time %']
  },
  education: {
    name: 'Education',
    color: '#6366F1',
    gradientFrom: '#6366F1',
    gradientTo: '#4F46E5',
    icon: 'GraduationCap',
    chartType: ['bar', 'radar', 'pie'],
    kpis: ['Pass Rate', 'Attendance', 'Performance', 'Engagement']
  },
  retail: {
    name: 'Retail',
    color: '#EF4444',
    gradientFrom: '#EF4444',
    gradientTo: '#DC2626',
    icon: 'ShoppingCart',
    chartType: ['bar', 'line', 'pie'],
    kpis: ['Sales', 'Inventory Turnover', 'Customer Retention', 'Basket Size']
  },
  manufacturing: {
    name: 'Manufacturing',
    color: '#64748B',
    gradientFrom: '#64748B',
    gradientTo: '#475569',
    icon: 'Factory',
    chartType: ['line', 'gauge', 'bar'],
    kpis: ['OEE', 'Downtime', 'Defect Rate', 'Throughput']
  },
  energy: {
    name: 'Energy',
    color: '#FBBF24',
    gradientFrom: '#FBBF24',
    gradientTo: '#F59E0B',
    icon: 'Zap',
    chartType: ['line', 'area', 'gauge'],
    kpis: ['Consumption', 'Generation', 'Efficiency', 'Peak Demand']
  },
  // ... inside DOMAIN_CONFIGS object ...
  general: {
    name: 'General Analysis',
    color: '#94A3B8', // Slate-400
    gradientFrom: '#94A3B8',
    gradientTo: '#475569',
    icon: 'FileText',
    chartType: ['bar'],
    kpis: ['Data Quality', 'Rows', 'Columns', 'Completeness']
  }
// ...
}
