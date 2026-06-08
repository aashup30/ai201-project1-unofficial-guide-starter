# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

The domain chosen for this unofficial guide project is best places to eat around campus and surrounding areas. It was chosen because restaurant websites and official review sites don't accurately reflect the desires and priorities of students and are often influenced by ads or outside reviews. 

---

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 |r/gatech thread (what are all the best food places on campus) | Online forum | https://www.reddit.com/r/gatech/comments/sitg69/what_are_all_the_best_food_places_on_campus/ |
| 2 | Atlanta Eats article | Blog | https://www.atlantaeats.com/blog/restaurants-near-georgia-tech-atlanta/ |
| 3 | Yelp Ratings | Online Forum | https://www.yelp.com/search?find_desc=Campus+Food&find_loc=Georgia+Tech%2C+Atlanta%2C+GA |
| 4 | Best Places To Eat Around Georgia Tech - Article | Blog | https://www.theodysseyonline.com/best-places-to-eat-around-georgia-tech |
| 5 | Where to eat near Georgia Tech | Blog| https://www.theinfatuation.com/atlanta/guides/where-to-eat-near-georgia-tech |
| 6 | Good Restaurants near Georgia Tech | Online Forun |https://www.tripadvisor.com/ShowTopic-g60898-i104-k14737543-Good_restaurants_near_Georgia_Tech-Atlanta_Georgia.html |
| 7 | Best places to eat at Tech r/gatech | Online Forum | https://www.reddit.com/r/gatech/comments/n9zo4l/what_are_the_best_places_near_campus_to_eatdrink/ |
| 8 | Top restaurants near Georgia Tech | Blog | https://rambleratlanta.com/resources/top-restaurants-near-campus/ |
| 9 | r/gatech Must eat restaurants| Online Forum| https://www.reddit.com/r/gatech/comments/9ajrqb/must_eat_restaurants/ |
| 10 | Best restaurants in midtown Atlanta | Blog | https://atlanta.eater.com/maps/best-restaurants-bars-midtown-atlanta |

---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size:**

**Overlap:**

**Why these choices fit your documents:**

**Final chunk count:**

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:**

**Production tradeoff reflection:**

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:**

**How source attribution is surfaced in the response:**

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:**

**What the system returned:**

**Root cause (tied to a specific pipeline stage):**

**What you would change to fix it:**

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:**

**One way your implementation diverged from the spec, and why:**

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1**

- *What I gave the AI:*
- *What it produced:*
- *What I changed or overrode:*

**Instance 2**

- *What I gave the AI:*
- *What it produced:*
- *What I changed or overrode:*
