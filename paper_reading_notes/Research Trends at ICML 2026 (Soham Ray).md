# Research Trends at ICML 2026

**Author:** Soham Ray (@sohmray) — Sierra, tau-bench team

**Tweet:** https://x.com/sohmray/status/2077157003387109542

**X article:** https://x.com/i/article/2077127538808356864

**Type:** X long-form article (personal conference-trends essay, linked from a tweet)

**Posted:** 2026-07-14 · **Updated:** 2026-07-15

---

<!-- Reading progress: read the intro and §1–§3 (the three research-trend themes) together; done. The final personal "On tau" closing (tau-bench reception + hiring) was intentionally skipped. Plain prose is Ray's; my own takes are called out. -->

## What this is

Not a paper — a personal field-notes essay from ICML 2026 in Seoul, where Soham Ray (Sierra, tau-bench team) presented three tau papers. He lists the trends that stood out, grouped into four themes: how research gets done, evaluation, data and memory, and a closing note on tau-bench.

**My one-line read:** building is getting cheap and fast, so the scarce things now are **judgment** (what is worth doing) and **measurement** (whether it worked).

## 1. How research gets done is changing

Three observations, which the author simply lists. My read: the first two are the same force — cheap generation, especially code — showing up at two different levels.

**Automated research is heating up — but verification lags.** Lots of work on AI "research scientists," and Google is investing heavily (its [End-to-End AI Scientist](https://icml.cc/virtual/2026/75728) panel, the [MARS](https://arxiv.org/abs/2602.02660) agent). Ray's caution is the point: despite the hype around [automating research at scale](https://arxiv.org/abs/2601.14525), "we're not there yet." The [AI Scientists workshop](https://icml.cc/virtual/2026/workshop/54099) admits the field can't yet tell which claims hold up, and there are [calls to stop automating peer review](https://icml.cc/virtual/2026/poster/67247) until evaluation is rigorous. The real bottleneck is **verification, not generation**.

**Everything is a factory.** As code gets cheap, people build more elaborate pipelines and generator loops. Data-generation and LLM-judge pipelines are far more thorough than before. Ray expects this to speed up research on both axes at once: **thoroughness** and **throughput**.

> **My experience.** This is my daily reality. Trainers, data generation, and evaluation can all be stood up with coding agents like Claude Code. Experiments that took weeks now take days — and they can be genuinely solid, not hacky — so ideas get validated fast enough to really iterate.
>
> **But fast and solid-looking isn't the same as correct.** Once anyone can spin up a thorough-looking pipeline in days, the real question becomes whether the evaluation measures the right thing. That is exactly the next theme.

**Taste is the open question.** "Taste" is condensing years of experience into a feel for which directions are worth pulling. LLMs hold huge world knowledge but seem to lack it. What is taste — and can you quantify, replicate, or scale it? [InnoEval](https://arxiv.org/abs/2602.14367) is an early attempt.

**The thread** *(my read).* "Automated research" is cheap generation aimed at the *whole* researcher; "factory" is the same force aimed at the *parts* (data and judging pipelines). Capability climbs on knowledge and throughput — but taste, the judgment layer, stays missing. That gap is what pushes the weight onto **evaluation** next.

## 2. The weight is shifting to evaluation

As building gets easy, the bottleneck moves to evaluation — and the hard half is *what* to evaluate, not *how*.

**What to evaluate is the hard part.** Citing Arvind Narayanan's talk [What will be left for us to work on?](https://icml.cc/virtual/2026/invited-talk/67274), Ray separates two things: *how* to evaluate (the metric and benchmark mechanics, relatively tractable) and *what* to evaluate (which capability is even worth measuring). The second is the hard one — and automating it, letting a system decide what to measure, is a key step toward recursive self-improvement.

**Benchmarks are saturating.** A [systematic study of 60 benchmarks](https://arxiv.org/abs/2602.16763) found about half showing saturation symptoms. Two responses stood out: the oral [Benchmarking at the Edge of Comprehension](https://icml.cc/virtual/2026/oral/71031) asks what to do when humans can no longer even author discriminative tasks, and [contamination-resistant design](https://icml.cc/virtual/2026/poster/67191) targets the overfitting-and-leakage gap. The deeper reason a saturated benchmark misleads: models are mostly good at what they were trained on, with limited cross-task transfer, so a score really only tells you about the distribution it was optimized for.

**Benchmark is not deployment.** The public benchmark suite is a narrow sample of the real deployment distribution. Optimize only against it and you get models that score well but feel worse in actual use — a [clinical-AI position paper](https://icml.cc/virtual/2026/poster/67107) puts it bluntly: benchmark scores don't measure deployment readiness. Frontier labs close the gap with large suites of internal environments and mountains of usage data that replicate deployment offline. So a public-benchmark win buys initial **perception**, not lasting **adoption**.

**LLM judges are maturing.** More reliable judges are coming: [REAL](https://arxiv.org/abs/2603.17145) trains judges as calibrated reward scorers, and [Rubric Curriculum RL](https://icml.cc/virtual/2026/poster/64634) evolves the rubric itself — a curriculum of criteria that advances as training progresses.

> **My read — this is last chapter's taste problem again.** Deciding "what to evaluate" is the same judgment as deciding "which direction is worth pulling." The factory automated *how* and *throughput*; what is still missing is automating *what matters*. It is also why the labs' real moat is private evaluation, not public benchmarks.

## 3. Data and memory

Two loosely related topics bundled together: where training data comes from, and what an agent keeps.

**Synthetic data keeps getting better** — in quality, diversity, and complexity. Concretely: the oral [Less is Enough](https://icml.cc/virtual/2026/oral/71029) matches a 300K-sample dataset with just 2K feature-targeted synthetic samples, and Google's [Simula](https://arxiv.org/abs/2603.29791) pitches agentic generation as a replacement for expensive human annotation. Ray's operational advice: whatever you believe "still needs human data" is probably a few months out of date, so re-ask it at every model release. And a subtle shift — a lot of synthetic generation now goes into building *environments*, not just datasets.

**Memory is what makes an agent yours.** Several threads:

- *What to keep or forget.* [Learning to Share](https://icml.cc/virtual/2026/poster/62890) learns which agent steps are worth keeping; [MemEvolve](https://icml.cc/virtual/2026/poster/61379) evolves the memory architecture itself; a [position paper](https://icml.cc/virtual/2026/poster/67101) argues modular memory is the key to continual learning; there is even a [workshop](https://icml.cc/virtual/2026/workshop/54086) on what models *shouldn't* remember.
- *Personalization.* Memory is what personalizes an agent — [Persona2Web](https://icml.cc/virtual/2026/poster/61367) benchmarks web agents reasoning over user history, and [MCP-Persona](https://icml.cc/virtual/2026/poster/60873) does the same for tools and tasks.
- *It only counts across sessions.* Memory matters only if it holds up session to session ([interdependent multi-session tasks](https://icml.cc/virtual/2026/poster/64842) tests exactly this).
- *It is also an attack surface.* Once memory persists, the same store that personalizes your agent is the one an attacker most wants to write to — hence work on [memory-poisoning defenses](https://icml.cc/virtual/2026/poster/61006).

Ray closes the theme by admitting that evaluating any of this well is still mostly open ground.

> **My read.** The sharpest line here: the thing that makes an agent *yours* and the thing an attacker most wants to touch are the *same* persistent store. Personalization and vulnerability are two sides of persistence. And the closing admission — "how to evaluate this is open" — loops straight back to §2. Evaluation is the bottleneck that keeps reappearing.
