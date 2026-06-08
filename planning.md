# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

I chose the domain of best restaurants to eat on and around campus at Georgia Tech. I believe this information is hard to find organically because of the variety of sources and opinions out there that require a lot of reading through sources to aggregate the most popular opinions. The information foud here also isn't often published by colleges as the food scene around campus isn't generally a large deciding factor when choosing a college, meaning the college doesn't have incentive to provide insight on this.

---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

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

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:**

**Overlap:**

**Reasoning:**

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**

**Top-k:**

**Production tradeoff reflection:**

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1.

2.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**

**Milestone 4 — Embedding and retrieval:**

**Milestone 5 — Generation and interface:**
