
import streamlit as st
__version__ = "1.1.0"  # Update this version string with each release
import pandas as pd
from bands import BANDS, Band
from calculator import evaluate
import altair as alt
import pyperclip
from io import BytesIO

st.set_page_config(page_title="RF Spectrum Interference Calculator", page_icon="📡", layout="wide", initial_sidebar_state="expanded")
st.title("📡 RF Spectrum Interference Calculator")
st.markdown("**Professional-grade harmonic & intermodulation analysis tool**")
st.markdown("---")

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    guard = st.number_input(
        "Guard Band Margin (MHz)",
        min_value=0.0,
        max_value=50.0,
        value=0.0,
        step=0.1,
        help="Additional frequency margin around Rx bands for interference detection"
    )
    aclr_margin = st.number_input("ACLR margin (MHz)", 0.0, 20.0, 0.0, step=0.1)
    st.markdown("---")
    st.markdown("### Band Categories")
    all_bands = list(BANDS.values())
    categories = sorted(set(b.category for b in all_bands))
    default_cats = [cat for cat in categories if cat in ("Wi-Fi", "LTE")]
    selected_cats = st.multiselect("Filter by category:", categories, default=default_cats)

# Main interface
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📋 Available Bands")
    filtered_bands = {b.code: b for b in all_bands if b.category in selected_cats}
    available_options = [f"{b.code}: {b.label}" for b in filtered_bands.values()]
    available_bands = st.multiselect(
        "Select bands to analyze:",
        available_options,
        help="Choose bands for interference analysis. Use Ctrl+Click for multiple selections."
    )
    st.info(f"**{len(available_bands)} bands selected** from {len(filtered_bands)} available")

with col2:
    st.subheader("🎯 Selected Bands Summary")
    if available_bands:
        selected_band_ids = [b.split(":")[0] for b in available_bands]
        for i, band_id in enumerate(selected_band_ids[:10]):
            band = BANDS[band_id]
            st.write(f"**{i+1}.** {band.label}")
            st.write(f"   └─ Tx: {band.tx_low}-{band.tx_high} MHz | Rx: {band.rx_low}-{band.rx_high} MHz")
        if len(selected_band_ids) > 10:
            st.write(f"... and {len(selected_band_ids) - 10} more bands")
    else:
        st.info("Select bands from the left panel to begin analysis")

st.markdown("---")

# IMD toggles
st.subheader("IMD/Harmonic Products")
col_4, col_5, col_6 = st.columns(3)
with col_4:
    imd4 = st.checkbox("IMD4 (2f1+2f2)", value=False)
with col_5:
    imd5 = st.checkbox("IMD5 (3f1±2f2)", value=False)
with col_6:
    imd7 = st.checkbox("IMD7 (4f1±3f2)", value=False)


# Calculate button
from calculator import calculate_all_products
if st.button("🚀 Calculate Interference", type="primary", use_container_width=True):
    if not available_bands:
        st.error("Please select at least one band for analysis")
    else:

        selected_band_ids = [b.split(":")[0] for b in available_bands]
        selected_band_objs = [BANDS[c] for c in selected_band_ids]
        # Use new exhaustive calculation function
        results_list, overlap_alerts = calculate_all_products(selected_band_objs, guard, imd4=imd4, imd5=imd5, imd7=imd7, aclr_margin=aclr_margin)
        # Sort so risk items (⚠️) are at the top, then by frequency
        results_sorted = sorted(results_list, key=lambda x: (x.get("Risk", "✓") == "✓", x.get("Frequency_MHz", 0)))
        results = pd.DataFrame(results_sorted)

        # Results summary
        st.subheader("📊 Analysis Results")
        total_products = len(results)
        risk_products = (results["Risk"] == "⚠️").sum() if "Risk" in results.columns else 0
        safe_products = total_products - risk_products
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Products", f"{total_products:,}")
        with col2:
            st.metric("⚠️ Risk Products", f"{risk_products:,}", delta=f"{risk_products/total_products*100:.1f}%" if total_products > 0 else "0%")
        with col3:
            st.metric("✅ Safe Products", f"{safe_products:,}")
        with col4:
            st.metric("Guard Margin", f"{guard} MHz")

        # Overlap alerts
        if overlap_alerts:
            st.warning("\n".join(overlap_alerts))

        # Results table
        st.subheader("📋 Detailed Results")
        # Ensure all columns are present and in the same order as app.py
        expected_cols = [
            "Type", "IM3_Type", "Formula", "Frequency_MHz", "Aggressors", "Victims", "Risk", "Details"
        ]
        for col in expected_cols:
            if col not in results.columns:
                results[col] = ""
        # Add any missing columns to the DataFrame and preserve order
        results = results.reindex(columns=expected_cols)

        def highlight_risks(row):
            if row["Risk"] == "⚠️":
                return ["background-color: rgba(255, 75, 75, 0.1)"] * len(row)
            else:
                return ["background-color: rgba(0, 200, 81, 0.05)"] * len(row)
        if not results.empty:
            styled_df = results.style.apply(highlight_risks, axis=1)
            st.dataframe(styled_df, use_container_width=True, height=400)

            # Export options
            st.subheader("📥 Export Results")
            col1, col2 = st.columns(2)
            with col1:
                csv = results.to_csv(index=False)
                st.download_button(
                    label="📄 Download CSV",
                    data=csv,
                    file_name="interference_analysis.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            with col2:
                buffer = BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    results.to_excel(writer, sheet_name='Interference Analysis', index=False)
                    summary_data = {
                        'Metric': ['Total Products', 'Risk Products', 'Safe Products', 'Guard Margin (MHz)'],
                        'Value': [total_products, risk_products, safe_products, guard]
                    }
                    pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
                st.download_button(
                    label="📊 Download Excel",
                    data=buffer.getvalue(),
                    file_name="interference_analysis.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

        # Show error/success based on risk column
        if "Risk" in results.columns and (results["Risk"] == "⚠️").any():
            st.error("⚠ At least one product lands inside the Rx band.")
        else:
            st.success("✅ No in-band hits detected.")

        # Altair plot (interactive)
        st.markdown("### Frequency View (Interactive)")
        if not results.empty:
            color_col = "Risk" if "Risk" in results.columns else results.columns[-1]
            freq_col = "Freq_low" if "Freq_low" in results.columns else (results.columns[2] if results.shape[1] > 2 else results.columns[0])
            chart = alt.Chart(results).mark_circle(size=100).encode(
                x=alt.X(freq_col, title="Frequency (MHz)"),
                y=alt.Y("Type", title="Product Type"),
                color=alt.Color(color_col, scale=alt.Scale(domain=["⚠️", "✓"], range=["#c62828", "#388e3c"])),
                tooltip=list(results.columns)
            ).interactive()
            st.altair_chart(chart, use_container_width=True)

        # Copy to clipboard (markdown)
        if st.button("Copy Results as Markdown"):
            md = results.to_markdown(index=False)
            pyperclip.copy(md)
            st.info("Results copied to clipboard as Markdown!")

        # PDF report (placeholder)
        if st.button("Generate PDF Report"):
            st.warning("PDF report generation coming soon! (WeasyPrint/pdfkit integration)")

# Footer
st.markdown("---")
st.markdown(f"""
<div style='text-align: center; color: gray; font-size: 0.8em;'>
    RF Spectrum Interference Calculator v{__version__} | Professional RF Systems Analysis Tool<br>
    Supports 3GPP LTE Bands 1-71, Wi-Fi 2.4G/5G/6E, Bluetooth LE, ISM, HaLow, LoRaWAN, GNSS
</div>
""", unsafe_allow_html=True)
