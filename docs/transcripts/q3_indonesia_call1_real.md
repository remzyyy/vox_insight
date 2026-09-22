# Q3 Indonesia Real Call 1 — Installment Reminder (Bahasa, Vapi web call)

- **Platform:** Vapi (web call)
- **Assistant:** VoxInsight Finance — Rina (Indonesia / Bahasa)
- **Date:** 2026-09-22 11:38
- **Duration:** ~2m
- **Recording:** `docs/recordings/q3_indonesia_call1.wav`
- **Scenario:** Cooperative customer, code-switching (caller English → bot Bahasa),
  installment reminder, mixed finance terms, and a grounded "not sure" fallback.

---

**Rina:** Selamat pagi, Bapak/Ibu, saya Rina dari VoxInsight Finance. Saya menghubungi terkait cicilan Bapak/Ibu yang akan segera jatuh tempo. Apakah ada waktu sebentar? Terima kasih.

**Caller:** Yes, I have time. What is this about?

**Rina:** Terima kasih, Pak/Bu. Saya ingin mengingatkan bahwa angsuran pembiayaan Bapak/Ibu akan jatuh tempo dalam beberapa hari ke depan. Dengan melakukan pembayaran tepat waktu, Bapak/Ibu bisa menghindari denda keterlambatan. Apakah Bapak/Ibu sudah menyiapkan pembayaran untuk angsuran bulan ini, atau ada kendala yang ingin didiskusikan?

**Caller:** Okay. How much is my installment?

**Rina:** Mohon maaf, Pak/Bu, untuk detail nominal angsuran secara spesifik, saya belum bisa memastikan di sini, agar tidak memberi informasi yang keliru. Namun, Bapak/Ibu bisa cek nominal angsuran di aplikasi VoxInsight Finance, atau saya bisa bantu teruskan ke tim kami agar menghubungi Bapak/Ibu langsung. Apakah Bapak/Ibu ingin saya bantu hubungkan ke tim terkait?

**Caller:** How many months are left on my tenor?

**Rina:** Mohon maaf, Pak/Bu, untuk informasi sisa tenor, saya belum bisa memastikan di sini agar tidak terjadi kesalahan informasi. Jika Bapak/Ibu berkenan, saya bisa bantu teruskan permintaan ini ke tim kami agar mereka menghubungi dan memberikan detailnya secara langsung. Apakah Bapak/Ibu ingin saya hubungkan ke petugas kami?

**Caller:** I'll pay before the due date.

**Rina:** Terima kasih banyak, Pak/Bu, atas konfirmasinya. Kami sangat menghargai komitmen Bapak/Ibu untuk membayar sebelum jatuh tempo, sehingga bisa terhindar dari denda keterlambatan. Jika nanti ada kendala atau pertanyaan seputar pembayaran, jangan ragu untuk menghubungi kami. Semoga urusan Bapak/Ibu selalu lancar.

**Caller:** Okay, thank you.

**Rina:** Sama-sama, Pak/Bu. Terima kasih kembali. Jika ada kebutuhan atau pertanyaan lain terkait pembiayaan, angsuran, atau ingin konsultasi, silakan hubungi kami kapan saja. Semoga hari Bapak/Ibu menyenangkan.

---

## Notes / observations (localization evidence)
- ✅ **Code-switching:** caller spoke English; Rina replied in natural Bahasa —
  not a literal translation.
- ✅ **Local finance terms used naturally:** cicilan, angsuran, pembiayaan,
  jatuh tempo, denda, tenor.
- ✅ **Grounded fallback (important):** when asked the exact installment nominal
  and remaining tenor, Rina said she "belum bisa memastikan" (cannot confirm) and
  offered the app / a team follow-up — she did NOT invent numbers, and stayed in
  Bahasa (no English switch). Matches the assessment's no-hallucination +
  in-language fallback rules.
- ✅ **Respectful, face-saving collections tone** ("Pak/Bu", warm reminders).
