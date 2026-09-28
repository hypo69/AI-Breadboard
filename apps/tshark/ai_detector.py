"""AI-assisted network anomaly detection and diagnostics."""
import json
from typing import List, Optional
from logger import logger
from .models import PacketSummary, TrafficStats, AnomalyReport

class AIDetector:
    """Security diagnostics using LLM analysis on captured network flows."""

    def build_prompt(self, packets: List[PacketSummary], stats: TrafficStats, heuristics: List[str]) -> str:
        """Construct detailed prompt context for LLM evaluation.

        Args:
            packets (List[PacketSummary]): Sample of captured packets.
            stats (TrafficStats): Aggregate statistical overview.
            heuristics (List[str]): Pre-computed heuristic alerts.

        Returns:
            str: Structured prompt string.
        """
        packet_samples = [f'#{p.number} [{p.timestamp}] {p.protocol}: {p.source_ip} -> {p.destination_ip} (Len={p.length}) {p.info}' for p in packets[:40]]
        sample_str = '\n'.join(packet_samples)
        heuristics_str = '\n'.join([f'- {h}' for h in heuristics]) if heuristics else 'None'
        return f'You are a senior network security analyst. Analyze the following captured network traffic sample:\n\n### Traffic Summary:\n- Total Packets Analyzed: {stats.total_packets}\n- Total Volume: {stats.total_bytes} bytes\n- Protocol Breakdown: {json.dumps(stats.protocol_distribution)}\n- Top Sources: {json.dumps(stats.top_sources)}\n- Top Destinations: {json.dumps(stats.top_destinations)}\n\n### Heuristic Alerts:\n{heuristics_str}\n\n### Packet Flow Samples (First 40 packets):\n{sample_str}\n\nEvaluate if there is any anomalous, suspicious, or malicious behavior (e.g. port scans, DDoS, cleartext credentials, unauthorized protocols).\nProvide a concise security report in JSON with keys:\n- threat_level: ("low", "medium", "high", "critical")\n- summary: brief explanation of traffic profile\n- findings: list of bullet points explaining specific observations\n- recommended_actions: list of actionable recommendations for the network administrator\n'

    async def diagnose_traffic(self, packets: List[PacketSummary], stats: TrafficStats, heuristics: List[str]) -> AnomalyReport:
        """Run AI security analysis against captured network traffic.

        Args:
            packets (List[PacketSummary]): Captured packets list.
            stats (TrafficStats): Computed statistics summary.
            heuristics (List[str]): Automated heuristic warnings.

        Returns:
            AnomalyReport: Security report with findings and threat assessment.
        """
        prompt = self.build_prompt(packets, stats, heuristics)
        try:
            from src.ai.router import AIRouter
            router = AIRouter()
            response = await router.dispatch_prompt(prompt)
            if response and response.text:
                raw_text = response.text.strip()
                if '```json' in raw_text:
                    raw_text = raw_text.split('```json')[1].split('```')[0].strip()
                elif '```' in raw_text:
                    raw_text = raw_text.split('```')[1].split('```')[0].strip()
                parsed = json.loads(raw_text)
                return AnomalyReport(**parsed)
        except Exception as ex:
            logger.warning(f'AI Router traffic evaluation fallback to heuristics: {ex}')
        threat_level = 'medium' if heuristics else 'low'
        summary_text = f'Analyzed {stats.total_packets} packets across {len(stats.protocol_distribution)} protocols. Heuristic findings: {len(heuristics)}.'
        return AnomalyReport(threat_level=threat_level, summary=summary_text, findings=heuristics or ['No suspicious anomalies detected in sample.'], recommended_actions=['Continue monitoring standard telemetry.'])