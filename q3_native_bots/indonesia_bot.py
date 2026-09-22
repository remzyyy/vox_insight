"""Indonesia bot (Q3): multifinance / consumer finance, Bahasa Indonesia.

Flow: installment reminder + collections support (pre-due and gentle follow-up).
Supports formal and colloquial Bahasa, finance English loanwords, and at least
one regional accent outside standard Jakarta speech (Javanese-accented Bahasa).
"""
from __future__ import annotations

from .localization import (
    BotConfig, FAQ, LocalizationExample, Objection, ScriptedTurn, TermEntry,
)

ID_BOT = BotConfig(
    market="indonesia",
    sector="multifinance_consumer_finance",
    languages=["id", "id-colloquial", "en-loanwords"],
    register_notes=(
        "Open formal/polite ('Bapak/Ibu', 'Selamat pagi'), then soften to colloquial "
        "if the customer does. Collections tone must stay respectful and face-saving — "
        "never shaming. Use 'Kak' for younger/informal customers."
    ),
    asr={
        "provider": "deepgram",
        "model": "nova-2",
        "primary_language": "id",
        "also_configure": ["en"],
        "notes": (
            "Bahasa Indonesia (id) primary + English fallback for loanwords (tenor, DP, "
            "cover). Test three profiles separately: standard Jakarta, colloquial "
            "Jakarta (gue/lo, nggak), and Javanese-accented Bahasa (Central/East Java)."
        ),
    },
    tts={
        "provider": "azure",
        "voice": "id-ID-GadisNeural",
        "alt_voice": "id-ID-ArdiNeural",
        "notes": (
            "Azure Indonesian neural voices are natural for standard Bahasa. Regional "
            "accents are an ASR concern (input) more than TTS; the bot always replies in "
            "clear standard Bahasa. Document that native Sundanese/Javanese TTS is not used."
        ),
    },
    terminology=[
        TermEntry("cicilan", "installment", "Core word for installment; use freely."),
        TermEntry("angsuran", "installment (more formal)", "Formal synonym of cicilan; use in formal register."),
        TermEntry("tenor", "loan term/duration", "English loanword, fully standard in ID finance."),
        TermEntry("denda", "late fee/penalty", "Say 'denda' for late fee; explain amount clearly."),
        TermEntry("DP", "down payment", "Pronounced 'de-pe'; standard loanword."),
        TermEntry("jatuh tempo", "due date", "Standard phrase for due date."),
        TermEntry("pembiayaan", "financing", "Formal term for financing/multifinance product."),
        TermEntry("pelunasan", "full settlement / payoff", "For early payoff discussions."),
    ],
    greeting=(
        "Selamat pagi, Bapak/Ibu. Saya Rina dari tim pembiayaan. Saya menghubungi "
        "terkait cicilan Bapak/Ibu yang akan segera jatuh tempo. Apakah ada waktu "
        "sebentar? Terima kasih."
    ),
    flow=[
        ScriptedTurn("open",
                     "Selamat pagi, Bapak/Ibu, saya Rina dari tim pembiayaan. Boleh minta "
                     "waktu sebentar terkait cicilan Bapak/Ibu?"),
        ScriptedTurn("installment_reminder",
                     "Ini hanya pengingat, Pak/Bu — cicilan bulan ini akan jatuh tempo "
                     "tanggal 25. Supaya tidak kena denda, mohon dibayar sebelum tanggal itu ya.",
                     notes="Pre-due reminder; mentions denda to motivate on-time payment."),
        ScriptedTurn("payment_difficulty_check",
                     "Kalau misalnya bulan ini agak berat, tidak apa-apa Pak/Bu — bisa kita "
                     "bicarakan opsi keringanan atau atur ulang jadwal. Boleh saya bantu?",
                     notes="Collections support: face-saving, offers restructuring."),
        ScriptedTurn("confirm",
                     "Baik, jadi Bapak/Ibu akan bayar sebelum tanggal 25 ya. Saya catat. "
                     "Terima kasih banyak."),
        ScriptedTurn("close",
                     "Terima kasih atas waktunya, Pak/Bu. Kalau ada kendala, silakan "
                     "hubungi kami kembali. Selamat beraktivitas."),
    ],
    faqs=[
        FAQ("Berapa denda kalau telat bayar?",
            "Denda keterlambatan dihitung per hari dari nilai cicilan, Pak/Bu. Supaya "
            "tidak terkena denda, sebaiknya dibayar sebelum jatuh tempo. Saya bisa bantu "
            "cek nominal pastinya."),
        FAQ("Bisa tidak tenornya diperpanjang?",
            "Bisa kita ajukan perpanjangan tenor, Pak/Bu, supaya cicilan bulanannya lebih "
            "ringan. Nanti tim kami bantu proses pengajuannya."),
        FAQ("Kalau saya mau lunasi lebih awal bagaimana?",
            "Untuk pelunasan lebih awal bisa, Pak/Bu. Ada perhitungan sisa pokok — saya "
            "bantu hubungkan ke tim agar dapat angka pastinya."),
    ],
    objections=[
        Objection("Saya belum ada uang bulan ini.",
                  "Saya mengerti, Pak/Bu, tidak apa-apa. Kita cari solusi bersama — bisa "
                  "atur ulang jadwal atau keringanan supaya tidak memberatkan. Yang penting "
                  "kita jaga catatan pembiayaan Bapak/Ibu tetap baik."),
        Objection("Dendanya kok mahal banget sih.",
                  "Saya paham, Pak/Bu. Denda muncul karena keterlambatan, jadi kalau dibayar "
                  "sebelum jatuh tempo tidak akan kena. Kalau sekarang berat, boleh kita "
                  "bicarakan opsi keringanannya."),
        Objection("Nggak sempat ke kantor buat bayar.",
                  "Tenang Pak/Bu, tidak perlu ke kantor. Pembayaran bisa lewat transfer atau "
                  "aplikasi. Saya bisa pandu langkah-langkahnya sekarang kalau berkenan."),
    ],
    localization_examples=[
        LocalizationExample(
            situation="Reminding a customer their installment is due soon",
            literal_translation="Pembayaran ansuran Anda harus dibayar segera untuk menghindari denda.",
            localized="Pak, cicilan bulan ini jatuh tempo tanggal 25 ya — biar nggak kena denda, "
                      "dibayar sebelum itu ya Pak.",
            why="Literal 'Anda' + stiff phrasing feels like a legal notice. Real collectors use "
                "'Pak/Bu', 'cicilan', 'jatuh tempo', 'kena denda' and a warmer rhythm."),
        LocalizationExample(
            situation="Offering help to a customer who can't pay this month",
            literal_translation="Jika Anda tidak dapat membayar, silakan hubungi kantor kami.",
            localized="Kalau bulan ini agak berat, tenang Pak/Bu, bisa kita atur keringanan — "
                      "nggak usah sungkan.",
            why="Face-saving matters in Indonesian collections. 'agak berat', 'tenang', 'nggak usah "
                "sungkan' preserve dignity; the literal version sounds cold and pushes the customer away."),
        LocalizationExample(
            situation="Javanese-accented customer speaks colloquially",
            literal_translation="(bot switches to formal English/Bahasa, ignoring the register)",
            localized="Nggih Pak, mboten menopo-menopo — bisa kita bantu atur cicilannya, "
                      "tenang mawon.",
            why="For a clearly Javanese-accented, older customer the bot mirrors light Javanese "
                "politeness ('nggih', 'mboten menopo', 'mawon') within Bahasa — not a literal "
                "translation and never an unexpected English switch."),
    ],
    fallback_line=(
        "Mohon maaf Pak/Bu, untuk yang itu saya belum bisa memastikan, jadi tidak ingin "
        "memberi informasi yang keliru. Akan saya teruskan ke tim kami supaya dapat "
        "jawaban yang tepat ya."
    ),
    escalation_line=(
        "Baik Pak/Bu, saya sambungkan ke petugas kami langsung ya. Mohon tunggu "
        "sebentar, tidak perlu khawatir."
    ),
    accent_notes=(
        "Regional accent handled: Javanese-accented Bahasa (Central/East Java). ASR tested "
        "separately for this profile; expect slightly higher word-error on rapid colloquial "
        "speech and Javanese particles ('nggih', 'mboten', 'mawon', 'ndak'). The bot replies "
        "in clear standard Bahasa but may echo light Javanese politeness markers to build rapport."
    ),
    code_switching_notes=(
        "Finance English loanwords (tenor, DP, cover, cash) stay in English within Bahasa "
        "sentences. Colloquial markers: 'nggak', 'kok', 'sih', 'banget', 'Kak'. Formal "
        "markers: 'tidak', 'Bapak/Ibu', 'silakan'. Bot picks register from the customer."
    ),
    known_gaps=[
        "Only Javanese accent modeled; Batak/Sundanese/Minang accents not separately tuned.",
        "No native Javanese/Sundanese TTS — replies use standard Indonesian voice.",
        "Denda amounts are illustrative; real figures must come from the loan system.",
        "Collections compliance (OJK conduct rules) requires legal/compliance review.",
    ],
)
