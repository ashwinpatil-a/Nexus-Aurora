class SwarmRouter:
    def route(self, text: str, has_file: bool):
        t = text.lower()
        if has_file: return "Analyst", "Data Science"
        if any(x in t for x in ['def ', 'import ', 'sql', 'vulnerability', 'hack']): return "Sentinel", "Cybersecurity"
        if any(x in t for x in ['roi', 'market', 'strategy', 'profit', 'growth']): return "Strategist", "Finance"
        return "Liaison", "General Analysis"