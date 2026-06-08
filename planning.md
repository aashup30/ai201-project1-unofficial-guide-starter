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

**Chunk size:**
400 characters

**Overlap:**
50 characters

**Reasoning:**
A 400 character chunk size was chosen because analysis of the 10 sources revealed that they all had a similar format of individual entries (ie bulleted paragraphs for restaurants or yelp reviews) so a fixed size chunk would be best. The average size of the entries in the blogs is a bit over 400 characters so I chose 400 with an overlap of 50 to capture the longest entries and threads under comments on reddit so that context isn't lost. I believe this strategy will work best across all sources but may fail to accurately capture the results on reddit threads with short comments which could be a limitation. I got around that limitation by asking Claude to also split by paragraphs when possible and then implement the chunk size when entries are too big.

---

## Retrieval Approach


**Embedding model:**
I am choosing the all-MiniLM-L6-v2 via sentence-transformers reccomended by CodePath for simplicty as it runs locally and simpler connection and implementation allows me to focus on improving other parts of my guide. 

**Top-k:**
I chose a top-k of 5 initially because it is broad enough to handle slightly more complex queries while limiting irrelevant information to the queries being asked. Additionally, a top K that is too high may increase the response time and since the questions asked are supposed to be for students, we want to focus on quick and mostly accurate responses. 

**Production tradeoff reflection:**
If cost was no object I'd choose a model that could provide multilingual support, increase accuracy and decrease latency due to our target audience of students. Generally students are looking for quick answers to their questions which is the primary driver of wanting to decrease latency. Many students are international and looking for food options (such as options from their home country), making multilingual support and accuracy the next priorities. I would prioritize latency and multilingual support as the top two factors, as accuracy is important but less critical to our target audience than those two.

---

## Evaluation Plan


| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | What is the closest restaurant to the library? | Citation of the Odyssey article with blue donkey coffee  |
| 2 | What is the most budget-friendly option for food near campus?| Citation of the first source and publix subs, blue donkey, or halal guys  |
| 3 | What are the best pizza places around campus? | Antico's, Attwoods |
| 4 | What restaurants are open late near campus?  | Waffle house, Taco bell, Lucky Buddha |
| 5 | I want a sweet treat near campus, where could I go?  | Jeni's Ice cream, Sweet Hut|

---

## Anticipated Challenges


1. The chunk size may be too large for the reddit posts and therefore provide inconsistent information when compared to other sources. It may make false equivalencies between reddit comments in an attempt to match the chunk size. 

2. Since some of the forum sources list some restaurants multiple times in comments (like TripAdvisor or Reddit), the results may prioritize those restaurants too much and not evenly attribute other sources of data, giving biased answers.
---

## Architecture


Document Ingestion (online sources)
        ↓
Chunking (200 chars, 50-char overlap)
        ↓
Embedding (sentence-transformers / all-MiniLM-L6-v2)
        ↓
Vector Store (ChromaDB)
        ↓
Retrieval (similarity search, top-k=5)
        ↓
Generation (browser-based interface)
---

## AI Tool Plan


**Milestone 3 — Ingestion and chunking:**
I will give Claude my source list from planning.md, the requirements for cleaning up the data, and the chunking requirements of fixed-size chunks of 200 characters with 50-character overlap. I will ask it to create a python script that cleans up the text, chunks it using chunk_text() and my requirements and look at several of the chunk outputs to verify that the size is correct and looks consistent with my expectations.

**Milestone 4 — Embedding and retrieval:**
I will give Claude my embedding model of choice, my chunking requirements from planning,md and my retrieval requirements. I will ask it to create a py file that embeds each chunk, stores the subsequent embeddings using my preferred vector store (chromaDB) and does the search. I'll then test using my evaluation questions to see if the sources are correct and the chunks that are chosen are relevant to the questions.

**Milestone 5 — Generation and interface:**
I'll give Claude the guidelines for a basic UI that students can use to search for their questions. I will ask it for code for a browser based UI that can display an answer to the question asked using the top retrieved chunks and cite sources. I will test using my evaluation questions and try to throw edge case questions at the engine to ensure that the answers are accurate. I will also test the UI for basic usability, ensuring it is user-friendly.