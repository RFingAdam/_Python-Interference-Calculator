# RF Spectrum Interference Calculator

A professional-grade tool for analyzing RF spectrum interference, harmonics, and intermodulation products across global wireless bands.

## Features
- Complete 3GPP LTE bands 1-71, Wi-Fi 2.4G/5G/6E, Bluetooth LE, ISM, HaLow, LoRaWAN, GNSS
- Harmonic and IMD (IM3, IM4, IM5, IM7) analysis
- Risk-level flagging and overlap warnings
- Interactive frequency plots (Altair)
- Export results to CSV/Excel
- Modern Streamlit UI with category filtering and multi-select
- Modular codebase: `bands.py`, `calculator.py`, `ui.py`

## Quick Start
1. **Install dependencies:**
   ```sh
   pip install streamlit pandas altair openpyxl pyperclip
   ```
2. **Run the app:**
   ```sh
   streamlit run ui.py
   ```
3. **Select band categories and bands, set margins, and click Calculate Interference.**
4. **Review results, export, or copy as needed.**

## Versioning
- See the `__version__` string at the top of `ui.py` for the current version.
- Update the version string in `ui.py` and add changes to [CHANGELOG.md](CHANGELOG.md) with each release.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for full release history.

## Authors
Adam Engelbrecht

## License
[MIT](LICENSE)
