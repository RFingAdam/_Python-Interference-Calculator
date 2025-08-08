from typing import List, Tuple, Dict
from bands import Band

def calculate_all_products(selected_bands: List[Band], guard: float = 0.0, imd4: bool = False, imd5: bool = True, imd7: bool = False, aclr_margin: float = 0.0) -> Tuple[List[Dict], List[str]]:
    """
    Exhaustive IMD/harmonic/overlap logic for all selected bands, matching app.py.
    Returns (results, overlap_alerts).
    """
    results = []
    overlap_alerts = []
    n = len(selected_bands)
    # Overlap checks (Tx/Tx, Rx/Rx, Tx in Rx, Rx in Tx)
    for i in range(n):
        b1 = selected_bands[i]
        for j in range(i+1, n):
            b2 = selected_bands[j]
            b1_tx_low = b1.tx_low - guard
            b1_tx_high = b1.tx_high + guard
            b2_tx_low = b2.tx_low - guard
            b2_tx_high = b2.tx_high + guard
            b1_rx_low = b1.rx_low - guard
            b1_rx_high = b1.rx_high + guard
            b2_rx_low = b2.rx_low - guard
            b2_rx_high = b2.rx_high + guard
            # Tx-Tx overlap
            if not (b1_tx_high < b2_tx_low or b2_tx_high < b1_tx_low):
                overlap_alerts.append(f"Tx band overlap: {b1.code} ({b1.tx_low}-{b1.tx_high} MHz) and {b2.code} ({b2.tx_low}-{b2.tx_high} MHz)")
            # Rx-Rx overlap
            if not (b1_rx_high < b2_rx_low or b2_rx_high < b1_rx_low):
                overlap_alerts.append(f"Rx band overlap: {b1.code} ({b1.rx_low}-{b1.rx_high} MHz) and {b2.code} ({b2.rx_low}-{b2.rx_high} MHz)")
            # Tx of one in Rx of other
            if not (b1_tx_high < b2_rx_low or b1_tx_low > b2_rx_high):
                overlap_alerts.append(f"Tx({b1.code}) overlaps Rx({b2.code})")
            if not (b2_tx_high < b1_rx_low or b2_tx_low > b1_rx_high):
                overlap_alerts.append(f"Tx({b2.code}) overlaps Rx({b1.code})")

    # Harmonics (2H, 3H)
    for b in selected_bands:
        for order in (2, 3):
            for edge in [b.tx_low, b.tx_high]:
                freq = edge * order
                for victim in selected_bands:
                    rx_low = victim.rx_low - guard
                    rx_high = victim.rx_high + guard
                    risk = rx_low <= freq <= rx_high
                    results.append(dict(
                        Type=f"{order}H",
                        Formula=f"{order}×Tx_{'low' if edge==b.tx_low else 'high'}({b.code})",
                        Freq_low=freq,
                        Freq_high=freq,
                        Aggressors=b.code,
                        Victims=victim.code if risk else '',
                        Risk="⚠️" if risk else "✓",
                        RiskLevel=risk_level(freq, freq, rx_low, rx_high),
                    ))

    # IM3/IM4/IM5/IM7 exhaustive edge cases (all band pairs, all edges)
    for i in range(n):
        b1 = selected_bands[i]
        for j in range(n):
            if i == j:
                continue
            b2 = selected_bands[j]
            A_edges = [b1.tx_low, b1.tx_high]
            B_edges = [b2.tx_low, b2.tx_high]
            # IM3: 2A ± B, 2B ± A
            for A in A_edges:
                for B in B_edges:
                    for sign in [-1, 1]:
                        freq1 = 2*A + sign*B
                        for victim in selected_bands:
                            rx_low = victim.rx_low - guard
                            rx_high = victim.rx_high + guard
                            risk = rx_low <= freq1 <= rx_high
                            results.append(dict(
                                Type="IM3",
                                Formula=f"2×{b1.code}_{'low' if A==b1.tx_low else 'high'} {'+' if sign>0 else '-'} {b2.code}_{'low' if B==b2.tx_low else 'high'}",
                                Freq_low=freq1,
                                Freq_high=freq1,
                                Aggressors=f"{b1.code}, {b2.code}",
                                Victims=victim.code if risk else '',
                                Risk="⚠️" if risk else "✓",
                                RiskLevel=risk_level(freq1, freq1, rx_low, rx_high),
                            ))
            # IM4 (2f1+2f2)
            if imd4:
                for A in A_edges:
                    for B in B_edges:
                        freq4 = 2*A + 2*B
                        for victim in selected_bands:
                            rx_low = victim.rx_low - guard
                            rx_high = victim.rx_high + guard
                            risk = rx_low <= freq4 <= rx_high
                            results.append(dict(
                                Type="IM4",
                                Formula=f"2×{b1.code}_{'low' if A==b1.tx_low else 'high'} + 2×{b2.code}_{'low' if B==b2.tx_low else 'high'}",
                                Freq_low=freq4,
                                Freq_high=freq4,
                                Aggressors=f"{b1.code}, {b2.code}",
                                Victims=victim.code if risk else '',
                                Risk="⚠️" if risk else "✓",
                                RiskLevel=risk_level(freq4, freq4, rx_low, rx_high),
                            ))
            # IM5 (3f1±2f2)
            if imd5:
                for A in A_edges:
                    for B in B_edges:
                        for sign in [-1, 1]:
                            freq5 = 3*A + sign*2*B
                            for victim in selected_bands:
                                rx_low = victim.rx_low - guard
                                rx_high = victim.rx_high + guard
                                risk = rx_low <= freq5 <= rx_high
                                results.append(dict(
                                    Type="IM5",
                                    Formula=f"3×{b1.code}_{'low' if A==b1.tx_low else 'high'} {'+' if sign>0 else '-'} 2×{b2.code}_{'low' if B==b2.tx_low else 'high'}",
                                    Freq_low=freq5,
                                    Freq_high=freq5,
                                    Aggressors=f"{b1.code}, {b2.code}",
                                    Victims=victim.code if risk else '',
                                    Risk="⚠️" if risk else "✓",
                                    RiskLevel=risk_level(freq5, freq5, rx_low, rx_high),
                                ))
            # IM7 (4f1±3f2)
            if imd7:
                for A in A_edges:
                    for B in B_edges:
                        for sign in [-1, 1]:
                            freq7 = 4*A + sign*3*B
                            for victim in selected_bands:
                                rx_low = victim.rx_low - guard
                                rx_high = victim.rx_high + guard
                                risk = rx_low <= freq7 <= rx_high
                                results.append(dict(
                                    Type="IM7",
                                    Formula=f"4×{b1.code}_{'low' if A==b1.tx_low else 'high'} {'+' if sign>0 else '-'} 3×{b2.code}_{'low' if B==b2.tx_low else 'high'}",
                                    Freq_low=freq7,
                                    Freq_high=freq7,
                                    Aggressors=f"{b1.code}, {b2.code}",
                                    Victims=victim.code if risk else '',
                                    Risk="⚠️" if risk else "✓",
                                    RiskLevel=risk_level(freq7, freq7, rx_low, rx_high),
                                ))
    # ACLR check (optional, for all pairs)
    if aclr_margin > 0:
        for i in range(n):
            b1 = selected_bands[i]
            for j in range(n):
                if i == j:
                    continue
                b2 = selected_bands[j]
                aclr_risk = aclr_check(b1.tx_high, b2.rx_low, aclr_margin)
                results.append(dict(
                    Type="ACLR",
                    Formula=f"{b1.code}_tx_high vs {b2.code}_rx_low",
                    Freq_low=b1.tx_high,
                    Freq_high=b2.rx_low,
                    Aggressors=b1.code,
                    Victims=b2.code if aclr_risk else '',
                    Risk="⚠️" if aclr_risk else "✓",
                    RiskLevel="High" if aclr_risk else "Low",
                ))
    return results, overlap_alerts
from typing import List, Tuple, Dict
from bands import Band

def hits_rx(freq_low: float, freq_high: float, rx_low: float, rx_high: float) -> bool:
    return (
        rx_low <= freq_low <= rx_high
        or rx_low <= freq_high <= rx_high
        or (freq_low <= rx_low and freq_high >= rx_high)
    )

def aclr_check(tx_high: float, rx_low: float, margin: float) -> bool:
    # Adjacent channel leakage: Tx high within margin of Rx low
    return abs(tx_high - rx_low) <= margin

def evaluate(
    tx_band: Band,
    rx_band: Band,
    guard: float,
    imd4: bool = False,
    imd5: bool = True,
    imd7: bool = False,
    aclr_margin: float = 0.0
) -> List[Dict]:
    rx_low, rx_high = rx_band.rx_low - guard, rx_band.rx_high + guard
    rows = []

    # 2H / 3H
    for order in (2, 3):
        low, high = tx_band.tx_low * order, tx_band.tx_high * order
        rows.append(
            dict(
                Type=f"{order}H",
                Formula=f"{order}×Tx({tx_band.code})",
                Freq_low=low,
                Freq_high=high,
                Risk=hits_rx(low, high, rx_low, rx_high),
                RiskLevel=risk_level(low, high, rx_low, rx_high),
            )
        )

    # IM3: 2f1 ± f2 (use both band edges)
    edges = [
        (tx_band.tx_low, tx_band.tx_high),
        (rx_band.tx_low, rx_band.tx_high),
    ]
    combos = [
        (2 * edges[0][0] - edges[1][1], "2·X_low − Y_high"),
        (2 * edges[0][1] - edges[1][0], "2·X_high − Y_low"),
        (2 * edges[1][0] - edges[0][1], "2·Y_low − X_high"),
        (2 * edges[1][1] - edges[0][0], "2·Y_high − X_low"),
    ]
    for freq, label in combos:
        rows.append(
            dict(
                Type="IM3",
                Formula=label,
                Freq_low=freq,
                Freq_high=freq,  # discrete
                Risk=rx_low <= freq <= rx_high,
                RiskLevel=risk_level(freq, freq, rx_low, rx_high),
            )
        )

    # IM4 (2f1+2f2)
    if imd4:
        combos4 = [
            (2 * edges[0][0] + 2 * edges[1][1], "2·X_low + 2·Y_high"),
            (2 * edges[0][1] + 2 * edges[1][0], "2·X_high + 2·Y_low"),
            (2 * edges[1][0] + 2 * edges[0][1], "2·Y_low + 2·X_high"),
            (2 * edges[1][1] + 2 * edges[0][0], "2·Y_high + 2·X_low"),
        ]
        for freq, label in combos4:
            rows.append(
                dict(
                    Type="IM4",
                    Formula=label,
                    Freq_low=freq,
                    Freq_high=freq,
                    Risk=rx_low <= freq <= rx_high,
                    RiskLevel=risk_level(freq, freq, rx_low, rx_high),
                )
            )
    # IM5 (3f1±2f2)
    if imd5:
        combos5 = [
            (3 * edges[0][0] - 2 * edges[1][1], "3·X_low − 2·Y_high"),
            (3 * edges[0][1] - 2 * edges[1][0], "3·X_high − 2·Y_low"),
            (3 * edges[1][0] - 2 * edges[0][1], "3·Y_low − 2·X_high"),
            (3 * edges[1][1] - 2 * edges[0][0], "3·Y_high − 2·X_low"),
        ]
        for freq, label in combos5:
            rows.append(
                dict(
                    Type="IM5",
                    Formula=label,
                    Freq_low=freq,
                    Freq_high=freq,
                    Risk=rx_low <= freq <= rx_high,
                    RiskLevel=risk_level(freq, freq, rx_low, rx_high),
                )
            )
    # IM7 (4f1±3f2)
    if imd7:
        combos7 = [
            (4 * edges[0][0] - 3 * edges[1][1], "4·X_low − 3·Y_high"),
            (4 * edges[0][1] - 3 * edges[1][0], "4·X_high − 3·Y_low"),
            (4 * edges[1][0] - 3 * edges[0][1], "4·Y_low − 3·X_high"),
            (4 * edges[1][1] - 3 * edges[0][0], "4·Y_high − 3·X_low"),
        ]
        for freq, label in combos7:
            rows.append(
                dict(
                    Type="IM7",
                    Formula=label,
                    Freq_low=freq,
                    Freq_high=freq,
                    Risk=rx_low <= freq <= rx_high,
                    RiskLevel=risk_level(freq, freq, rx_low, rx_high),
                )
            )
    # ACLR check
    if aclr_margin > 0:
        aclr_risk = aclr_check(tx_band.tx_high, rx_band.rx_low, aclr_margin)
        rows.append(
            dict(
                Type="ACLR",
                Formula="Tx_high vs Rx_low",
                Freq_low=tx_band.tx_high,
                Freq_high=rx_band.rx_low,
                Risk=aclr_risk,
                RiskLevel="High" if aclr_risk else "Low",
            )
        )
    return rows

def risk_level(freq_low, freq_high, rx_low, rx_high):
    # Simple risk: High if in-band, Med if within 5 MHz, else Low
    if rx_low <= freq_low <= rx_high or rx_low <= freq_high <= rx_high:
        return "High"
    elif abs(freq_low - rx_low) < 5 or abs(freq_high - rx_high) < 5:
        return "Med"
    else:
        return "Low"
