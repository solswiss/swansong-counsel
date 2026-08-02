# swansong-counsel
## 🚧 construction

### functionality
Your project should do something useful with AI. For example:

    Summarize text or documents
    Retrieve information or data from a source
    Plan and complete a step-by-step task
    Help debug, classify, or explain something

To make your project more advanced, it must include at least one of the following AI features: RAG, agentic workflow, fine-tuned or specialized model, reliability or testing system.

The feature should be fully integrated into the main application logic. It is not enough to have standalone script; the feature must meaningfully change how the system behaves or processes information. For example, if you add RAG, your AI should actively use the retrieved data to formulate its response rather than just printing the data alongside a standard answer.

#### targets
WORDPLAY: one-letter-off picture puzzles
- paintings
- boil the frog imperceptible hops
- make it a game, spot the difference?
- bridge your music taste using pictures (AI's job)

BLUEPRINTS: audiospacial designs
- AI blueprint rolls (RNG)
- user maps
- ??? goal

---

### design & architecture
Show how your project is organized by creating a short system diagram. Your diagram should include:

    The main components (like retriever, agent, evaluator, or tester).
    How data flows through the system (input → process → output).
    Where humans or testing are involved in checking AI results.

---

### documentation
You'll write a README file that clearly explains your project. It should include:

    Explicitly name your original project (from Modules 1-3) and provide a 2-3 sentence summary of its original goals and capabilities.
    Title and Summary: What your project does and why it matters.
    Architecture Overview: A short explanation of your system diagram.
    Setup Instructions: Step-by-step directions to run your code.
    Sample Interactions: Include at least 2-3 examples of inputs and the resulting AI outputs to demonstrate the system is functional.
    Design Decisions: Why you built it this way, and what trade-offs you made.
    Testing Summary: What worked, what didn't, and what you learned.
    Reflection: A brief note on what this project taught you about AI and problem-solving. Your graded responsible-AI reflection — how you collaborated with AI, one helpful and one flawed AI suggestion, and your system's limitations — goes in model_card.md (see Step 5), not here. Reflection content placed only in the README does not earn the reflection points.

Write this for a future employer who might look at your GitHub portfolio! Clarity and completeness matter more than perfection.

---

### AI
Your AI should prove that it works, not just seem like it does. Include at least one way to test or measure its reliability, such as:

    Automated tests (e.g., unit tests or simple checks for key functions).
    Confidence scoring (the AI rates how sure it is).
    Logging and error handling (your code records what failed and why).
    Human evaluation (you or a peer review the AI's output).

### to-do
- [ ] specialized model for music rec
- [ ] reliability system (feedback from users)
- [ ] diagram (architecture.mmd)
- [ ] logging &/ guardrails
- [ ] README setup documentation