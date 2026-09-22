# Q1 Real Test Call 1 — Cooperative Customer (Vapi web call)

- **Platform:** Vapi (web call)
- **Assistant:** VoxInsight Lending Receptionist
- **Date:** 2026-09-21 20:16
- **Duration:** ~3m 58s
- **Recording:** `docs/recordings/q1_call1_cooperative.wav`
- **Scenario:** Cooperative customer providing business details for a loan.

---

**Aria (VoxInsight):** Thank you for calling VoxInsight Business Lending. How may I help you today?

**Caller:** Hey, I want a business loan for my bakery.

**Aria:** Thank you for reaching out to VoxInsight Business Lending. To assist you better, may I please have your full name and the name of your bakery? Could you provide a callback number and an email if you wish? Are you interested in financing to help acquire the business? If so, may I ask the type of financing, the approximate funding amount, and the intended use of the funds? Lastly, do you have a preferred time for a callback?

**Caller:** My name is Rameez, and my bakery is Sweet Treats.

**Aria:** Thank you.

**Caller:** Phone number is 74-884-2647. Now tell me — I want a business loan for my bakery.

**Aria:** Thank you, Rameez. Just to confirm, your bakery is called Sweet Treats and your phone number is 74-884-2647. For the business loan, could you share the type of financing, the approximate funding amount, and how you intend to use the funds? Also, do you have a preferred time for a callback?

**Caller:** My annual revenue is about 40 lakh rupees, and my business is 3 years old.

**Aria:** Thank you for sharing that, Rameez. To summarize: your name is Rameez, your bakery is Sweet Treats, phone 74-884-2647, business operating for 3 years, annual revenue about ₹40 lakh. You're interested in a business loan. Could you let me know the approximate funding amount and the intended use of the funds? Do you have a preferred callback time?

**Caller:** Also I want to share my credit score.

**Aria:** Thank you, Rameez. If you'd like, you can share your credit score and I'll include it in the message.

**Caller:** Yes, please set up my application.

**Aria:** I'm here to take your message and details for the team, but I'm unable to set up applications directly. [confirms details] Once I have these details, I'll make sure the appropriate team member follows up with you.

**Caller:** Funding amount is like 40 lakh.

**Aria:** Thank you, Rameez. To confirm, you are seeking a funding amount of approximately ₹40 lakh for your bakery, Sweet Treats. Could you share the intended use of these funds? Do you have a preferred callback time? Once I have these details, I'll summarize everything and ensure the appropriate team member follows up.

---

## Notes / observations
- ✅ Agent greeted, collected name, business, phone, revenue, vintage — the
  qualification flow worked over real voice.
- ✅ Correctly stated it cannot set up applications directly and takes a message
  for the team (safe handoff behavior).
- ⚠️ **Currency bug:** ASR/LLM read "40 lakh" as "$40,000,000". For the final
  submission the prompt should pin currency to INR and interpret "lakh"
  (₹40 lakh = ₹4,000,000). Fix in the assistant system prompt.
- ⚠️ This Vapi-built receptionist is the *generic* auto-generated one; it is not
  yet connected to the Q2 knowledge base. To satisfy the assessment fully,
  connect the `query_knowledge_base` tool to the deployed webhook (see
  `docs/vapi_setup.md`) so factual answers are grounded + cited.
