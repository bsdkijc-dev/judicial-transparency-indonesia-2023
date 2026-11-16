# Data Quality Assessment — FY 2023 Audited Financial Statements

* **Overall Completeness:** **8 of 9 PDF chunks** (1,667 of 1,867 pages) were downloaded and verified directly; `LKMA2023_AUDITED-1001-1200.pdf` (VA/BPG bank account list) returned a Drive permission error (`EXC-2023-008`).
* **Numeric Integrity:** All 18 CSV files use pure numeric formatting (no currency symbols or thousands separators) and UTF-8 encoding for direct ingestion into Google Sheets, Python, R, and SQL.
* **Key Exceptions Logged (`financial_reconciliation_exceptions_2023.csv`):**
  1. `EXC-2023-001`: CALBMN p. 37 *Belanja Modal Lainnya* TOTAL row copy-paste typo (**Rp 329.64B** vs. true sum **Rp 30.90B**).
  2. `EXC-2023-002`: **Rp 58,362,739,295.00** account-code vs. BMN-code mismatches across **376 rows**.
  3. `EXC-2023-003`: **Rp 40,989,920.00** account-code vs. inventory-code mismatches across **33 rows**.
  4. `EXC-2023-004`: **Rp 0.22** TP/TGR rounding difference between Neraca (**Rp 48,752,226.00**) and CaLK F.2 (**Rp 48,752,225.78**).
  5. `EXC-2023-005`: **Rp 22,772,000.00** fully paid TGR case (*PA Pekalongan / [REDACTED-INDIVIDUAL-02]*) awaiting formal BPK removal.
  6. `EXC-2023-006`: **-Rp 83.80B** cross-disclosure scope variance between CaLK F.3 RPL register (**Rp 6.194T**) and CaLK F.4.1 Bank balance (**Rp 6.278T**).
  7. `EXC-2023-007`: **Rp 24,859,000.00** FY 2023 closing vs. FY 2024 opening *Uang Titipan* bridge difference.
  8. `EXC-2023-008`: `LKMA2023_AUDITED-1001-1200.pdf` Drive permission restriction.
  9. `EXC-2023-009`: **Rp 60,000.00** March 2023 consolidated *Uang Titipan* movement variance.
  10. `EXC-2023-010`: **-Rp 1,940,800.00** April 2023 *Biaya Proses* opening adjustment vs. March 2023 closing.
