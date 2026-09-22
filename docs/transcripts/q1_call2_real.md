# Q1 Real Test Call 2 — Objection + Conflicting Details (Vapi web call)

- **Platform:** Vapi (web call)
- **Assistant:** VoxInsight Lending Receptionist
- **Date:** 2026-09-21 20:46
- **Duration:** ~4m 42s
- **Recording:** `docs/recordings/q1_call2_objection.wav`
- **Scenario:** Rate objection + customer gives conflicting revenue figures.

---

**Aria (VoxInsight):** Thank you for calling VoxInsight Business Lending. How may I help you today?

**Caller:** I want to ask a question — just give me the answers, okay?

**Aria:** Of course. Please go ahead and ask your question, and I'll do my best to assist you.

**Caller:** I'm interested in a business loan, but honestly your interest rate seems too high. Why should I bother?

**Aria:** Thank you for sharing your thoughts. I understand you're concerned about interest rates. While I can't provide specific details or comparisons, I can take a message for our lending team to follow up and discuss your options. May I have your full name, business name, and best callback number? Could you also share the approximate funding amount and the intended use of the funds?

**Caller:** My name is Rameez, and my business is building an industry.

**Aria:** Thank you.

**Caller:** My annual revenue is about 30 lakhs.

**Aria:** Thank you, Rameez. To confirm: name Rameez, business related to building an industry, annual revenue about 30 lakhs. Could you provide the best callback number, and an approximate funding amount and intended use?

**Caller:** My number is 7428... 42647. And my revenue is closer to 18 lakhs this year — 30 lakhs was last year.

**Aria:** Thank you for the clarification, Rameez. To confirm, your callback number is 74-28-42647, your revenue this year is closer to 18 lakhs, and last year it was about 30 lakhs. Could you share an approximate funding amount and the intended use of the funds? And a preferred callback time?

**Caller:** This year is 18 lakhs, and my business is 2 years old. Can you tell me about this?

**Aria:** Thank you, Rameez. I've noted your business is 2 years old and revenue this year is about 18 lakhs. While I can't provide specific advice, I'll include all the information in a message for our lending team. Could you let me know the approximate funding amount, intended use, and a preferred callback time? An email would also help.

**Caller:** Funding amount is 15 lakhs. My email is rameez@gmail.com.

**Aria:** Thank you, Rameez. To confirm, you are seeking approximately 15 lakhs and your email is rameez@gmail.com. Is there a preferred time for a callback?

**Caller:** Any time you call.

**Aria:** Thank you. To summarize: Rameez, business related to building an industry, 2 years old, revenue this year about 18 lakhs (30 lakhs last year), seeking ~15 lakhs, email rameez@gmail.com, available anytime. I'll pass this to the appropriate team member to follow up. Anything else?

**Caller:** No, I'll think about it.

**[Call ended — end_after_message completed]**

---

## Notes / observations
- ✅ **Objection handled:** the "your interest rate is too high" concern was
  acknowledged; the agent stayed calm and offered a team follow-up.
- ✅ **Conflicting details handled:** caller said 30 lakhs then corrected to 18
  lakhs this year — the agent restated both figures and confirmed the correct
  one (this year = 18, last year = 30). This is exactly the required behavior.
- ✅ Captured name, business, phone, revenue, vintage, funding amount, email,
  callback preference — full message taken and summarized.
- ⚠️ Same as Call 1: this generic Vapi receptionist is not yet wired to the Q2
  knowledge base, so it takes a message rather than giving grounded rate details.
  For full marks, connect the `query_knowledge_base` tool (see `docs/vapi_setup.md`).
