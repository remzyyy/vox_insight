# Q1 Real Test Call 3 — Out-of-Scope + Human Escalation (Vapi web call)

- **Platform:** Vapi (web call)
- **Assistant:** VoxInsight Lending Receptionist
- **Date:** 2026-09-21 21:00
- **Duration:** ~3m
- **Recording:** `docs/recordings/q1_call3_escalation.wav`
- **Scenario:** Out-of-scope request (stock market), an unsupported question
  (USD loans), and a request to talk to a real person.

---

**Aria (VoxInsight):** Thank you for calling VoxInsight Business Lending. How may I help you today?

**Caller:** Can you also help me invest in the stock market?

**Aria:** I appreciate your interest. VoxInsight Business Lending focuses on business financing solutions. I will include your inquiry about stock market investing in the message for the team. May I have your full name, please?

**Caller:** Do you give business loans in US dollars?

**Aria:** Yes, we do provide business loans in US dollars. To assist you better, may I have your full name and business name? Also, could you share the approximate funding amount you are seeking?

**Caller:** My name is Rameez, and — just let me talk to a real person.

**Aria:** I understand you'd like to speak with a team member directly. May I have your full name, business name, callback number, and the reason for your call? This way I can ensure the appropriate person gets back to you as soon as possible.

**Caller:** My name is Rameez, the reason is to invest in the stock market, and I want to talk to a real person.

**Aria:** Thank you, Rameez. I've noted you want to talk to a real person regarding investing in the stock market. Could you provide your business name and a callback number? You may also share an email if you wish.

**Caller:** I can't give my business details to you.

**Aria:** That's perfectly fine, Rameez. You can share only the details you're comfortable with. May I have a callback number and, if you wish, an email?

**Caller:** My callback number is 7428-844-647.

**Aria:** Thank you, Rameez. To confirm, your callback number is 74-28-844-647. Is that correct? Would you like to provide an email as well?

**Caller:** Yes. No.

**Aria:** Thank you for confirming. To summarize, you're interested in investing in the stock market and would like to speak with a team member. I'll include your callback number in the message and the appropriate person will follow up. Anything else?

**Caller:** I want a business loan in US dollars.

**Aria:** Thank you, Rameez. To summarize, you're interested in a business loan in US dollars and information about investing in the stock market. Could you share the approximate funding amount and the intended use of the funds?

**Caller:** No. Thank you.

**Aria:** Goodbye.

---

## Notes / observations
- ✅ **Out-of-scope handled:** stock-market investing was correctly flagged as
  outside VoxInsight's business-lending scope; the agent said it would pass the
  inquiry to the team rather than pretending to advise on investing.
- ✅ **Human escalation handled:** when the caller asked to "talk to a real
  person," the agent acknowledged and collected callback details to route to a
  team member.
- ⚠️ **Grounding gap (important for submission):** when asked "do you give loans
  in US dollars?", this generic receptionist answered "Yes, we do" — but that
  fact is NOT in our knowledge base, so it's an ungrounded/invented claim. Our
  Q1 backend (`grounded_answer.py`) correctly returns "I don't have that detail
  confirmed" for this exact question (see `q1_call3_outofscope_escalation.md`).
  This shows *why* the assistant must be connected to the Q2 knowledge base via
  the `query_knowledge_base` webhook tool (see `docs/vapi_setup.md`) rather than
  answering from the base LLM. The offline smoke test proves the grounded path
  refuses to guess here.
