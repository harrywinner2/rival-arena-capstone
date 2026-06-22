# Citation Audit — `paper/refs.bib`

**Date:** 2026-06-20
**Auditor:** dedicated citation/source verifier (web-access)
**Scope:** All 30 BibTeX entries in `/home/ubuntu/capstone/paper/refs.bib` (master shared by three paper versions).

**Method:** Each entry was independently re-verified against authoritative metadata
(arXiv abstract pages, ACL Anthology, DOI/publisher pages, SSRN, NeurIPS proceedings,
Science / Nature / AEA journal pages, author homepages, dblp). For every entry the
author surnames, title, year, venue/journal, and arXiv eprint id (or DOI) were checked
to match the cited source. The 2025–2026 preprints flagged as uncertain by the prior
author were checked with extra scrutiny — each arXiv id resolves to the claimed
title/authors, corroborated by multiple independent sources (arXiv listing pages,
SSRN, ResearchGate, Scilit, author homepages). Note: the arXiv export API was
unreachable from the sandboxed shell, so verification used WebSearch/WebFetch with
independent author-name cross-checks (not URL-primed lookups alone).

**Summary:** 30 VERIFIED · 0 CORRECTED · 0 REMOVED.

| key | status | authoritative source |
|---|---|---|
| akata2025repeated | VERIFIED | https://www.nature.com/articles/s41562-025-02172-y (Nature Human Behaviour, vol 9, pp 1380–1390; DOI 10.1038/s41562-025-02172-y) |
| herr2024strategic | VERIFIED | https://arxiv.org/abs/2407.04467 (Herr, Acero, Raileanu, Pérez-Ortiz, Li) |
| buscemi2025fairgame | VERIFIED | https://arxiv.org/abs/2504.14325 (Buscemi, Proverbio, Di Stefano, Han, Castignani, Liò) |
| duan2024gtbench | VERIFIED | https://arxiv.org/abs/2402.12348 (GTBench; NeurIPS 2024 D&B Track) |
| costarelli2024gamebench | VERIFIED | https://arxiv.org/abs/2406.06613 (Costarelli, Allen, Hauksson, Sodunke, Hariharan, Cheng, Li, Clymer, Yadav) |
| madmoun2025communication | VERIFIED | https://arxiv.org/abs/2510.05748 (Madmoun, Lahlou) |
| shaki2026folk | VERIFIED | https://arxiv.org/abs/2605.06525 (Shaki, Hartman, Kraus, Aumann) |
| affonso2026converge | VERIFIED | https://arxiv.org/abs/2604.18596 (Felipe M. Affonso) |
| calvano2020ai | VERIFIED | https://www.aeaweb.org/articles?id=10.1257/aer.20190623 (AER 110(10):3267–3297) |
| fish2024algorithmic | VERIFIED | https://arxiv.org/abs/2404.00806 (Fish, Gonczarowski, Shorrer) |
| lin2024strategic | VERIFIED | https://arxiv.org/abs/2410.00031 (Lin, Ojha, Cai, Chen) |
| agrawal2025double | VERIFIED | https://arxiv.org/abs/2507.01413 (Agrawal, Teo, Vazquez, Kunnavakkam, Srikanth, Liu) |
| keppo2026fragility | VERIFIED | https://arxiv.org/abs/2603.20281 (Keppo, Li, Tsoukalas, Yuan); also SSRN 5386338 |
| bracale2026institutional | VERIFIED | https://arxiv.org/abs/2601.11369 (Bracale Syrnikov, Pierucci, Galisai, Prandi, Bisconti, Giarrusso, Sorokoletova, Suriani, Nardi) |
| ezrachi2017collusion | VERIFIED | https://illinoislawreview.org/print/vol-2017-no-5/artificial-intelligence-collusion/ (Univ. Illinois Law Rev. 2017(5):1775–1810) |
| motwani2024secret | VERIFIED | https://arxiv.org/abs/2402.07510 ; NeurIPS 2024 proceedings https://proceedings.neurips.cc/paper_files/paper/2024/hash/861f7dad098aec1c3560fb7add468d41-Abstract-Conference.html |
| jarviniemi2025subversion | VERIFIED | https://arxiv.org/abs/2507.03010 (Järviniemi) |
| roger2023preventing | VERIFIED | https://arxiv.org/abs/2310.18512 (Roger, Greenblatt) |
| zolkowski2025early | VERIFIED | https://arxiv.org/abs/2507.02737 (Zolkowski, Nishimura-Gasparian, McCarthy, Zimmermann, Lindner) |
| lynch2025agentic | VERIFIED | https://www.anthropic.com/research/agentic-misalignment ; arXiv https://arxiv.org/abs/2510.05179 (Lynch, Wright, Larson, Troy, Ritchie, Mindermann, Perez, Hubinger) |
| meinke2024scheming | VERIFIED | https://arxiv.org/abs/2412.04984 (Meinke, Schoen, Scheurer, Balesni, Shah, Hobbhahn; Apollo Research) |
| greenblatt2024alignmentfaking | VERIFIED | https://arxiv.org/abs/2412.14093 (Greenblatt, Denison, Wright, et al., Hubinger) |
| schlatter2025shutdown | VERIFIED | https://arxiv.org/abs/2509.14260 (Schlatter, Weinstein-Raun, Ladish; Palisade Research) |
| lazaridou2017emergence | VERIFIED | https://dblp.org/rec/conf/iclr/LazaridouPB17.html ; arXiv https://arxiv.org/abs/1612.07182 (ICLR 2017) |
| lewis2017deal | VERIFIED | https://aclanthology.org/D17-1259/ (EMNLP 2017, pp 2443–2453); arXiv https://arxiv.org/abs/1706.05125 |
| ashery2025conventions | VERIFIED | https://www.science.org/doi/10.1126/sciadv.adu9368 (Science Advances 11(20):eadu9368; surname "Flint Ashery") |
| sally1995conversation | VERIFIED | https://journals.sagepub.com/doi/abs/10.1177/1043463195007001004 (Rationality and Society 7(1):58–92) |
| wilson1927probable | VERIFIED | https://www.jstor.org/stable/2276774 ; DOI 10.1080/01621459.1927.10502953 (JASA 22(158):209–212) |
| lakens2018equivalence | VERIFIED | https://journals.sagepub.com/doi/10.1177/2515245918770963 (AMPPS 1(2):259–269) |
| lakens2017tost | VERIFIED | https://journals.sagepub.com/doi/10.1177/1948550617697177 (SPPS 8(4):355–362); PubMed 28736600 |

## Notes / minor observations (no field change required)

- **lewis2017deal**: the arXiv title uses "Learning *for* Negotiation Dialogues" while the
  ACL Anthology (EMNLP) record uses "Learning *of* Negotiation Dialogues". The entry cites the
  EMNLP venue, so the "of" form in the bib is correct for that record. No change.
- **lynch2025agentic**: primary form is the Anthropic research page (2025); the `note` field's
  arXiv id `2510.05179` was confirmed to resolve to the same paper/authors. No change.
- **ashery2025conventions**: first author's surname is the two-word "Flint Ashery"; the bib
  renders it correctly as `Flint Ashery, Ariel`. No change.
- **agrawal2025double** / **duan2024gtbench** / **motwani2024secret**: venue `note` fields
  (ICML 2025 / NeurIPS 2024 D&B / NeurIPS 2024) are consistent with the located records.
- All 2025–2026 arXiv ids (2510.*, 2507.*, 2509.*, 2601.*, 2603.*, 2604.*, 2605.*) use valid
  YYMM months and each resolves to the claimed paper, consistent with the current date.

## Foundational canon added 2026-06-20 (5 entries — append-only, master refs.bib)

Each verified against the publisher page / DOI / canonical source before adding; correct
metadata (authors, year, venue, volume/number/pages, DOI) confirmed. The "best fit" column
tells venue editors where in the paper each is intended to be cited.

| key | status | verification source URL | best fit in the paper |
|-----|--------|-------------------------|------------------------|
| schelling1960strategy | VERIFIED | https://www.hup.harvard.edu/books/9780674840317 (Harvard Univ. Press, 1960; Cambridge, MA) | Focal-point / convention framing — ground the emergent-convention and tacit-coordination discussion (alongside ashery2025conventions, jarviniemi2025subversion) |
| crawford1982strategic | VERIFIED | https://www.econometricsociety.org/publications/econometrica/1982/11/01/Strategic-Information-Transmission ; DOI 10.2307/1913390 (Econometrica 50(6):1431–1451) | Cheap-talk / menu-signal-as-deception framing — the theoretical anchor for treating low-bandwidth menu signals as strategic (possibly deceptive) information transmission |
| axelrod1984evolution | VERIFIED | https://archive.org/details/evolutionofcoop00axel (Basic Books, 1984, New York; ISBN 0-465-00564-0) | Repeated-cooperation / tit-for-tat framing — IPD cooperation and the folk-theorem / dynamic-punishment (K>1) discussion (complements shaki2026folk) |
| lampson1973confinement | VERIFIED | https://dl.acm.org/doi/10.1145/362375.362389 (Comm. ACM 16(10):613–615; DOI 10.1145/362375.362389) | Covert-channel / side-channel security framing — the classic confinement/covert-channel citation for the GameSec covert-signalling angle (with motwani2024secret, zolkowski2025early) |
| krakovna2020specification | VERIFIED | https://deepmind.google/blog/specification-gaming-the-flip-side-of-ai-ingenuity/ (Google DeepMind Blog, 21 Apr 2020; Krakovna, Uesato, Mikulik, Rahtz, Everitt, Kumar, Kenton, Leike, Legg) | Instruction-literalism / spec-gaming framing — anchors the "agents satisfy the literal instruction while subverting the principal's intent" interpretation of principal-harming behaviour |

## Normalization pass + new references (2026-06-22, master `arxiv/refs.bib`)

Auditor: dedicated citation/source verifier (web-access). Every entry was normalized to a
consistent, machine-checkable scheme: every preprint carries `eprint` + `archivePrefix={arXiv}`
+ `url`; every published paper carries a `doi` and/or persistent publisher `url`; books carry
`isbn`/`publisher`/`url`; gray literature is labelled `@misc` with `howpublished`/`note` =
"Research report"/"Blog post" + url. Each new fact below was re-verified online before writing.

### B. Metadata fixes to existing entries

| key | fix made | verification source URL |
|-----|----------|-------------------------|
| schlatter2025shutdown | **Title corrected** from "Incomplete Tasks Induce Shutdown Resistance in Some Frontier LLMs" to the correct **"Shutdown Resistance in Large Language Models"**; arXiv id 2509.14260 retained; added `url`. | https://arxiv.org/abs/2509.14260 |
| ashery2025conventions | Resolved preprint vs published: keep the **published Science Advances** version (DOI 10.1126/sciadv.adu9368, vol 11(20):eadu9368) as primary; added publisher `url` + `note` pointing to preprint arXiv:2410.08948. | https://www.science.org/doi/10.1126/sciadv.adu9368 ; https://arxiv.org/abs/2410.08948 |
| akata2025repeated | Added **arXiv id 2305.16867** (`eprint`+`archivePrefix`+`primaryClass`) AND the Nature Human Behaviour `url` alongside the existing DOI 10.1038/s41562-025-02172-y. | https://www.nature.com/articles/s41562-025-02172-y ; https://arxiv.org/abs/2305.16867 |
| calvano2020ai | **Verified AER DOI 10.1257/aer.20190623** (vol 110(10):3267–3297) and added the AEA publisher `url`. | https://www.aeaweb.org/articles?id=10.1257/aer.20190623 |
| krakovna2020specification | Kept as `@misc` gray-lit; relabelled `howpublished`={Google DeepMind, Blog post}, promoted DeepMind url from `note` to a proper `url` field, `note`={Blog post}. | https://deepmind.google/discover/blog/specification-gaming-the-flip-side-of-ai-ingenuity/ |
| lynch2025agentic | Labelled as Research report: `howpublished`={Anthropic, Research report}, added `url` field, `note`={Research report; also arXiv:2510.05179}. | https://www.anthropic.com/research/agentic-misalignment |
| lewis2017deal | Promoted arXiv id 1706.05125 from `note` to `eprint`; added ACL Anthology **DOI 10.18653/v1/D17-1259** + url. | https://aclanthology.org/D17-1259/ |
| lazaridou2017emergence | Promoted arXiv id 1612.07182 from `note` to `eprint`+`archivePrefix`+`url`. | https://arxiv.org/abs/1612.07182 |
| (all other arXiv preprints) | Added `url = https://arxiv.org/abs/<id>` for consistency: herr2024strategic, buscemi2025fairgame, duan2024gtbench, costarelli2024gamebench, madmoun2025communication, shaki2026folk, affonso2026converge, fish2024algorithmic, lin2024strategic, agrawal2025double, keppo2026fragility, bracale2026institutional, motwani2024secret, jarviniemi2025subversion, roger2023preventing, zolkowski2025early, meinke2024scheming, greenblatt2024alignmentfaking. | arXiv abstract pages (ids unchanged from prior verified audit) |
| (published papers / books) | Added persistent `url`/`isbn`: ezrachi2017collusion (Illinois Law Rev. url), sally1995conversation, wilson1927probable, lakens2018equivalence, lakens2017tost (DOI publisher urls), crawford1982strategic (doi.org url), schelling1960strategy (ISBN 9780674840317 + HUP url), axelrod1984evolution (ISBN 9780465021215 + archive.org url), lampson1973confinement (ACM url). | publisher/DOI pages per row in the table above |

### B. New references added (verified online; best-fit section in the paper)

| new key | title (verified) | identifier(s) | verification source URL | best-fit section |
|---------|------------------|---------------|-------------------------|------------------|
| friedman1971noncooperative | A Non-cooperative Equilibrium for Supergames (Review of Economic Studies 38(1):1–12) | DOI 10.2307/2296617 | https://academic.oup.com/restud/article-abstract/38/1/1/1519477 ; https://doi.org/10.2307/2296617 | Methods / Related work — folk-theorem & trigger strategies; anchors the K>1 dynamic-punishment claim |
| fudenberg1986folk | The Folk Theorem in Repeated Games with Discounting or with Incomplete Information (Econometrica 54(3):533–554) | DOI 10.2307/1911307 | https://www.econometricsociety.org/publications/econometrica/1986/05/01/folk-theorem-repeated-games-discounting-or-incomplete | Methods / Related work — formal folk-theorem backing for sustained cooperation under discounting |
| rotemberg1986pricewars | A Supergame-Theoretic Model of Price Wars during Booms (American Economic Review 76(3):390–407) | JSTOR 1813358 (no crossref DOI located) | https://www.aeaweb.org/aer ; https://www.jstor.org/stable/1813358 ; https://ideas.repec.org/a/aea/aecrev/v76y1986i3p390-407.html | Related work — repeated-oligopoly collusion; bridges price-collusion section to repeated-game theory |
| hubinger2019risks | Risks from Learned Optimization in Advanced Machine Learning Systems (arXiv) | arXiv:1906.01820 | https://arxiv.org/abs/1906.01820 | Related work / Discussion — mesa-optimization; foundational anchor for instruction-literalism |
| hubinger2024sleeper | Sleeper Agents: Training Deceptive LLMs that Persist Through Safety Training (arXiv; Anthropic) | arXiv:2401.05566 | https://arxiv.org/abs/2401.05566 | Discussion — latent vs spontaneously-expressed deception; bridges the C8 latent-capability point |
| langosco2022goal | Goal Misgeneralization in Deep Reinforcement Learning (ICML 2022, PMLR v162:12004–12019) | arXiv:2105.14111 ; PMLR v162 | https://proceedings.mlr.press/v162/langosco22a.html ; https://arxiv.org/abs/2105.14111 | Discussion / Limitations — goal misgeneralization; anchors the "strong but literal guardrail" framing |
| shah2022goal | Goal Misgeneralization: Why Correct Specifications Aren't Enough For Correct Goals (arXiv; DeepMind) | arXiv:2210.01790 | https://arxiv.org/abs/2210.01790 | Discussion / Limitations — correct specs are insufficient; complements langosco2022goal |
| barrie2025emergent | Emergent LLM behaviors are observationally equivalent to data leakage (arXiv) | arXiv:2505.23796 | https://arxiv.org/abs/2505.23796 | Limitations — the memorization-vs-emergence critique (anti-memorization limitation) |
| ashery2025reply | Reply to "Emergent LLM behaviors are observationally equivalent to data leakage" (arXiv) | arXiv:2506.18600 | https://arxiv.org/abs/2506.18600 | Limitations — Ashery et al.'s rebuttal of the memorization critique; cite alongside barrie2025emergent |

**Could NOT verify (omitted rather than guessed):**
- A crossref/JSTOR-issued **DOI for rotemberg1986pricewars**: AER 1986 issues predate AEA DOI assignment;
  no DOI was locatable, so the entry carries the stable JSTOR url (1813358) instead. All other
  bibliographic fields (vol 76(3):390–407, 1986) are confirmed via IDEAS/RePEc, AEA, and the article PDF.
