# Verification & Reconciliation Protocol — FY 2023

1. **Zero-Fabrication Rule:** Every figure in the 18 CSV datasets is extracted directly from [LKMA2023_AUDITED](https://drive.google.com/drive/folders/1OEorvUPXgSwqheqGk35B8EmD1u43vL7R) or computed explicitly from verified source columns. No missing comparative fields are estimated.
2. **Embedded Image Table & Shifted-Font Extraction:** CaLK Section F.4.1 (*Biaya Proses* and *Uang Titipan Pihak Ketiga*, pp. 159–164) and the main statement faces (Ringkasan, LRA, Neraca, LO) were rendered to PNG and visually verified line-by-line; shifted-font CaLK pages were decoded and cross-checked against rendered pages.
3. **Cross-Statement Checks Performed:**
   * **Neraca Identity:** `Assets (31,961,178,373,027) - Liabilities (195,204,452,338) = Equity (31,765,973,920,689)` — exact match.
   * **LPE Roll-Forward:** `Opening Equity (30,525,686,275,992) + Deficit-LO (-10,481,650,834,787) + Equity Corrections (66,338,556,929) + Inter-Entity (11,655,599,922,555) = Closing Equity (31,765,973,920,689)` — exact match.
   * **Grants Sum:** All **538 rows** of `grants_master_register_2023.csv` sum to **Rp 173,767,804,097.00**, matching CaLK F.4.2.1 exactly.
   * **TGR Receivable:** `Neraca` & `CaLK C.3.1` gross TP/TGR (**Rp 48,752,226.00**) minus 100% provision (**Rp 48,752,226.00**) = **Rp 0.00** net (`Rp 0.22` rounding diff vs. `CaLK F.2` **Rp 48,752,225.78**).
   * **KDP Roll-Forward:** `Tabel 52` closing balance (**Rp 915,655,052,073.00**) matches Neraca KDP line exactly.
