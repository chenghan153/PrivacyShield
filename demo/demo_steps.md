# PrivacyShield demo steps

All names, contacts, credentials, and figures in `demo/` are fictional.

1. Run `scripts/run.sh`, then forward remote port `8501` in VS Code.
2. Open `http://localhost:8501` and upload `demo/synthetic_invoice.pdf`.
3. Select **Internal Team**. Notice that the API key is redacted while contact and project details are allowed; financial data is flagged for review.
4. Select **External Client**. Contact details, the project name, budget, and API key are redacted; the client name is presented for review.
5. Select **Public**. Every detected sensitive category is redacted.
6. Uncheck and re-check a finding to demonstrate human control.
7. Download the redacted PDF. Verify it has no searchable sensitive strings:

   ```bash
   pdftotext downloaded_redacted.pdf - 2>/dev/null || true
   ```

   If `pdftotext` is unavailable, use the verification command in the README.

8. State the limitation clearly: deterministic OCR/rules can miss novel or low-quality content, so review remains mandatory.
