# Task Formats & Prompt Templates

This document presents (1) the templates used for **alignment tasks** that bridge textual item information and their corresponding **Semantic IDs (SIDs)**, and (2) the **prompts used for corpus enrichment**.

---

## Table of Contents

- [Overview](#overview)
- [Part 1 · Alignment Task Formats](#part-1--alignment-task-formats)
  - [Group A · SID ↔ Title Translation (Cases 1–2)](#group-a--sid--title-translation-cases-12)
  - [Group B · Generative Next-Item Prediction (Cases 3–6)](#group-b--generative-next-item-prediction-cases-36)
  - [Group C · Alignment via Item-centric Semantic Enrichment (Case 7)](#group-c--alignment-via-item-centric-semantic-enrichment-case-7)
  - [Group D · Sequential Recommendation via User-centric Reasoning Augmentation (Case 8)](#group-d--sequential-recommendation-via-user-centric-reasoning-augmentation-case-8)
- [Part 2 · Prompts for Corpus Enrichment](#part-2--prompts-for-corpus-enrichment)
  - [Item-centric Semantic Enrichment (Two-Stage)](#item-centric-semantic-enrichment-two-stage)
  - [User-centric Reasoning Enrichment (Two-Stage)](#user-centric-reasoning-enrichment-two-stage)

---

## Overview

The 8 alignment tasks are organized into 4 functional groups. Each task either translates between Semantic IDs and titles, or weaves SIDs into richer item / user contexts to teach the model the SID ↔ semantic correspondence.

| # | Group | Task | Input → Output |
|:---:|:------|:------|:----------------|
| **1** | A · SID ↔ Title Translation | SID translation | Title → SID |
| **2** | A · SID ↔ Title Translation | SID translation | SID → Title |
| **3** | B · Generative Next-Item Prediction | Item prediction | SID history → Title |
| **4** | B · Generative Next-Item Prediction | Item prediction | Title history → Title |
| **5** | B · Generative Next-Item Prediction | Item prediction | SID history → SID |
| **6** | B · Generative Next-Item Prediction | Item prediction | Title history → SID |
| **7** | C · Item-centric Semantic Enrichment | SID translation | Item-context narrative interleaved with SIDs |
| **8** | D · User-centric Reasoning Augmentation | Item prediction | User narrative interleaved with SIDs |

**Group descriptions:**

- **Group A · Cases 1–2** — Bi-directional mapping between textual item titles and their corresponding SIDs.
- **Group B · Cases 3–6** — The model predicts future interactions by alternating input and output between item titles and SIDs, capturing sequential behavioral patterns while reinforcing the SID ↔ title correspondence.
- **Group C · Case 7** — The model learns to associate SIDs with detailed, augmented item contexts by integrating semantic identifiers into LLM-generated comprehensive descriptions.
- **Group D · Case 8** — The model is trained on hybrid narratives of interaction history that interleave natural language with Semantic IDs. The goal is to let the model understand user behavior or recommendation logic as a coherent story.

---

## Part 1 · Alignment Task Formats

### Group A · SID ↔ Title Translation (Cases 1–2)

> Bi-directional mapping between textual item titles and their corresponding SIDs.

---

#### Case 1 · Title → SID

> **System** ▸ Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request. Answer the question about item identification.
>
> **User** ▸ Which item has the title: _"Final Fantasy VIII"_?
>
> **Assistant** ▸ `<a_195><b_133><c_138>`

---

#### Case 2 · SID → Title

> **System** ▸ Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request. Answer the question about item identification.
>
> **User** ▸ What is the title of item `<a_175><b_83><c_8>`?
>
> **Assistant** ▸ _"The Legend of Zelda: Spirit Tracks"_

---

### Group B · Generative Next-Item Prediction (Cases 3–6)

> Predict future interactions by alternating input/output between titles and SIDs.

The 2 × 2 design matrix for this group:

|                       | **Predict Title** | **Predict SID** |
|:----------------------|:------------------|:----------------|
| **From SID history**   | Case 3            | Case 5          |
| **From Title history** | Case 4            | Case 6          |

---

#### Case 3 · SID history → Title prediction

> **System** ▸ Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request. Can you recommend the next item for the user based on their interaction history?
>
> **User** ▸ The user has sequentially interacted with items `<a_45><b_88><c_206>`, `<a_205><b_247><c_168>`, `<a_45><b_190><c_242>`. Can you recommend the next item for him? Tell me the title of the item?
>
> **Assistant** ▸ _"PlayStation 4 500GB Console [Old Model][Discontinued]"_

---

#### Case 4 · Title history → Title prediction

> **System** ▸ Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request. Given a list of games the user recently enjoy, please write a new game that the user may bought.
>
> **User** ▸ The user has played the following games before: _"FIFA Soccer 12 - Playstation 3"_, _"PS3 Gran Turismo 5 XL Edition"_, _"MLB 13 The Show - Playstation 3"_?
>
> **Assistant** ▸ _"The Legend of Zelda: Spirit Tracks"_

---

#### Case 5 · SID history → SID prediction

> **System** ▸ Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request. Can you predict the next possible item that the user may expect?
>
> **User** ▸ The user has interacted with items `<a_45><b_88><c_206>`, `<a_205><b_247><c_168>`, `<a_45><b_190><c_242>` in chronological order. Can you predict the next possible item that the user may expect?
>
> **Assistant** ▸ `<a_231><b_28><c_63>`

---

#### Case 6 · Title history → SID prediction

> **System** ▸ Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request. Based on the user's historical interaction with item titles, predict the semantic ID of the next item they may expect.
>
> **User** ▸ The user has interacted with the following games items in chronological order: _"FIFA Soccer 12 - Playstation 3"_, _"PS3 Gran Turismo 5 XL Edition"_, _"MLB 13 The Show - Playstation 3"_. Can you predict the next item the user may expect?
>
> **Assistant** ▸ `<a_231><b_28><c_63>`

---

### Group C · Alignment via Item-centric Semantic Enrichment (Case 7)

> Train the model to associate SIDs with detailed item contexts by interleaving SIDs into LLM-generated comprehensive descriptions.

---

#### Case 7 · Interleaving SIDs with Augmented Item Contexts

> Introducing `<a_175><b_24><c_4>`, an exhilarating platforming game developed by Nintendo that revolutionizes the beloved Super Mario franchise through its introduction of simultaneous multiplayer action. For the first time ever, players can join forces or compete against one another as they traverse iconic side-scrolling environments brimming with nostalgic charm and fresh challenges. The game supports 2 to 4 players, making it an ideal choice for family game nights where everyone can engage in either cooperative or competitive gameplay. Additionally, casual gaming sessions among friends seeking an interactive and entertaining experience are perfect for immersing in the whimsical world of Mario. The single-player experience also caters to long-time fans craving the classic Mario gameplay they know and love, enhanced with updated graphics and features that breathe new life into the franchise. With characters such as Mario, Luigi, and two Toads, alongside exciting new power-ups like the propeller suit and Penguin Mario, `<a_175><b_24><c_4>` combines nostalgia with innovative gameplay mechanics, making it a standout title in the Mario series. The intuitive controls of the Wii Remote allow players to navigate with ease, offering both classic and modern input options that appeal to diverse gaming preferences. Players can lift each other to safety or strategically toss opponents into danger, fostering a playful yet competitive environment that is sure to delight. As players race to complete levels, they are ranked at the end based on their scores, coins collected, and enemies defeated, adding an extra layer of friendly rivalry. `<a_175><b_24><c_4>` truly encapsulates the essence of family entertainment, delivering a multiplayer platformer experience that resonates with children, families, and fans alike while ensuring a fun-filled adventure steeped in the rich legacy of the Super Mario franchise.

---

### Group D · Sequential Recommendation via User-centric Reasoning Augmentation (Case 8)

> Train the model on hybrid narratives of interaction history that interleave natural language with Semantic IDs — so user behavior reads as a coherent story.

---

#### Case 8 · Narrative-based Sequential Recommendation with Semantic IDs

> The user has engaged with `<a_250><b_39><c_2>`, `<a_21><b_19><c_204>`, `<a_92><b_90><c_145>`, and `<a_21><b_19><c_204>`, showcasing a distinctive pattern in their gaming preferences. This journey began with an intriguing foray into the world of immersive RPGs, starting with `<a_250><b_39><c_2>`, a title that reflects their appreciation for vibrant storytelling and character development. Following this initial adventure, the user showed a keen interest in enhancing their gaming experience through `<a_21><b_19><c_204>`, engaging with this technical accessory not once but twice. This indicates not only a desire for improved online gaming capabilities but also a preference for stable performance during their gaming sessions.
>
> The user's return to `<a_21><b_19><c_204>` signifies their commitment to solidifying their gaming setup, thoughtfully balancing technical enhancements with the enjoyment of gameplay. After establishing their gaming environment, they transitioned back to an equally engaging RPG with `<a_92><b_90><c_145>`, highlighting their intrinsic draw towards rich narrative experiences that allow for deep player engagement. This seamless shift reveals a thoughtful consideration of both gameplay mechanics and the overall story arc, suggesting that the user values a harmonious blend of technical quality and immersive storytelling.
>
> Given this dynamic interaction history, it seems evident that the user will continue to seek out richly woven narrative experiences that challenge the mind and engage the heart. Therefore, it's only natural that they would be inclined toward `<a_92><b_90><c_145>` as their predicted next choice, as it perfectly aligns with their penchant for captivating storytelling and interactive gameplay.

---

## Part 2 · Prompts for Corpus Enrichment

This section provides the complete instructions for the prompts used in **Item-centric Semantic Enrichment** and **User-centric Reasoning Enrichment**. Both follow a **two-stage framework**.

### At a Glance

| Module | Stage 1 | Stage 2 |
|:-------|:--------|:--------|
| **Item-centric Semantic Enrichment** | Comprehensive Analysis — reason through raw metadata to generate structured insights (audiences, use cases, latent keywords) | Integration — fuse all metadata into a single paragraph, seamlessly interleaving SIDs into the text |
| **User-centric Reasoning Enrichment** | Reasoning Generation — adopt an analyst's persona to infer latent preferences and behavioral shifts | Narrative Integration — merge raw interaction sequence with reasoning into one paragraph, using SIDs to represent items |

---

### Item-centric Semantic Enrichment (Two-Stage)

> **Stage 1** asks the model to reason through raw metadata to generate structured insights — target audiences, use cases, and latent keywords — transforming sparse data into deep contextual knowledge.
> **Stage 2** enforces fusing all metadata into a single paragraph by seamlessly interleaving SIDs into the text.

---

#### Stage 1 · Comprehensive Analysis

> Based on the following product information, generate a comprehensive analysis:
>
> _Product Title, Brand, Category, Description, Features_
>
> Please provide:
>
> 1. A detailed 2-3 sentence description
> 2. 2-3 main use cases
> 3. Target audience
> 4. 3-5 key features summary
> 5. 5-8 related keywords

---

#### Stage 2 · Integration

> You are a senior copywriter preparing an in-depth narrative for a product dossier.
>
> - **Source Meta Information:** _Title, Brand, Categories, Description, Features_
> - **Product Semantic Identifier** (use this exact string whenever you mention the product): _SID\_index_
> - **Enrichment from Stage 1:** _Detailed Description, Target Audience, Key Features, Related Keywords_
>
> **Task:**
>
> 1. Combine ALL of the information above into a single rich and coherent narrative of at least 10 sentences. Include every important fact, Detailed Description, scenario, Target Audience, audience insight, feature highlight, and keyword context that appears in the sources.
> 2. Every reference to the product must use the identifier `{index}`. Do NOT use the title or any other alias.
> 3. Ensure the result reads like a rich, flowing paragraph (no bullet points, headings, or enumerations). Maintain a professional and descriptive tone suitable for a product catalog.
> 4. Highlight how `{index}` fits different use cases, why its features matter, and draw from both original data and first-stage enhancements without omitting details.

---

### User-centric Reasoning Enrichment (Two-Stage)

> **Stage 1** focuses on **Reasoning Generation** — the model adopts an analyst's persona to infer latent user preferences and behavioral shifts from interaction history.
> **Stage 2** performs **Narrative Integration** — merging the raw interaction sequence with the generated reasoning into a seamless, natural-language paragraph that strictly uses Semantic IDs to represent items.

---

#### Stage 1 · Reasoning Generation

> You are an expert recommendation system analyst analyzing user behavior patterns.
>
> Your goal is to reason through the user's history and predict what the item the user would be interested in, explaining your reasoning process from your analytical perspective in first person.
>
> Given user interaction history, item descriptions, and reference next item, produce a concise first-person reasoning from an analyst's perspective to predict what kind of item the user may like in the next interactions. The reference item is only for internal guidance — reason entirely based on interaction history and item descriptions. Never mention or discuss the reference item in your reasoning. Write as a genuine real-time prediction analyzing user behavior patterns.
>
> - **User Interaction history:** _Chronological item titles_
> - **Reference next item:** _Next item title_
> - **Item Descriptions:** _Item\_descriptions_
>
> **OUTPUT REQUIREMENTS:**
>
> 1. Output ONLY reasoning monologue in first person (I) as an analyst. Keep concise but detailed. Vary sentence structures to avoid repetition.
> 2. Analyze general user preferences (genres, themes, attributes, motivations) and engagement patterns based on history.
> 3. Express potential interests or tendencies rather than deterministic conclusions or single outcomes.
> 4. Adapt depth to history length: brief key observations for short histories; step-by-step tracing of interest shifts for longer ones. Base predictions on observed patterns.
> 5. **CRITICAL:** Always use ONLY the SID format when referring to items. Never use titles, names, or `Item SID:` prefixes.
> 6. Never mention 'reference item' or imply knowledge of the target. Reason as if predicting blindly.
> 7. Start directly with reasoning. Do NOT predict a specific next item. End with a non-deterministic summary of likely interests (e.g., `may enjoy`, `tends to prefer`).
>
> **Your Reasoning:**

---

#### Stage 2 · Integration with SIDs

> Integrate the following information into a single, coherent, natural narrative paragraph:
>
> - **User interaction history:** _(Chronological item titles & SIDs)_
> - **Reference next item:** _(Item Title & SID)_
> - **Reasoning path from Stage 1**
>
> **OUTPUT REQUIREMENTS:**
>
> 1. Start your narrative by explicitly reciting the full 'User Interaction history (chronological item SIDs)' sequence EXACTLY as provided, but use varied and natural opening phrases. Ensure the full sequence is included to establish context.
> 2. Write in a natural, flowing style — avoid mechanical or formulaic language in the subsequent analysis. Make it read like a genuine narrative.
> 3. Preserve the essential reasoning insights from the reasoning path — don't just summarize, but naturally incorporate the key analytical points and logic.
> 4. When mentioning any item, ALWAYS use its SID (format: `<a_XXX><b_YYY><c_ZZZ>`) — never use item titles or names.
> 5. Keep the narrative natural and engaging.
>
> **Integrated Narrative:**
