# The Framingo Project — Design Charter / 設計憲章

*Revised edition, core specification / 改訂版・中核仕様*
*Language specification v1 codename / 言語仕様 v1 コードネーム: Gisaburo（ギサブロー）*

> **Status of this document / 本文書の位置づけ**
>
> **EN** — This document is intended to replace `overview.md` (the former five-chapter draft). That draft centred on the claim "LLMs lack a model of the physical world, so supply them with a good synthetic corpus", which is not this project's central thesis. Chapters 2–4 of the old draft (the language specification) remain valid, but they are **means, not claim**, and are demoted accordingly. This document puts first the **actual central thesis** as it was articulated in dialogue.
>
> **JA** — 本文書は `overview.md`（旧・全5章）を置き換えることを意図している。
> 旧文書は「LLMは物理世界モデルを欠く。ゆえに良質な合成コーパスを与える」という主張を中心に据えていたが、それは本企画の中心命題ではない。旧文書の第2〜4章（言語仕様）は依然として有効だが、それらは**主張ではなく手段**であり、格下げされる。
> 本文書は、対話の中で言語化された**実際の中心命題**を最初に置く。

---

# Chapter 1: The Central Thesis — Separating Knowledge from Logic / 第1章：中心命題 —— 知識と論理の分離

## 1.1 The Structural Defect of Current LLMs / 現行LLMの構造的欠陥

**EN** — Current large language models **melt knowledge and logic into a single parameter space.**

The **fact** "the capital of France is Paris" and the **inference rule** "if A then B, if B then C, therefore if A then C" coexist in the same weight matrices, undistinguished, as one continuous probability distribution. This fusion is the cause of all three pathologies of the present architecture.

**Pathology 1: size.**
The overwhelming majority of parameters are spent memorizing the internet. A model must be huge not because reasoning is hard, but **because it is trying to remember every fact about the world.**

**Pathology 2: undetectable hallucination.**
Because knowledge is dissolved into the parameters, when a model fabricates a fact its output is **structurally indistinguishable** from a correct one. Both are grammatically flawless natural language, produced by the same stochastic process. From outside there is no means of telling whether the model "answered because it knew" or "filled the gap because it did not."

**Pathology 3: unauditability.**
Even when the reasoning is emitted as a natural-language chain of thought, it **may be post-hoc confabulation.** Nothing guarantees that the explanation matches the computation actually performed. It therefore cannot be adopted in high-stakes domains.

These are not three separate problems. **Each is a consequence of knowledge and logic occupying the same place.**

**JA** — 現行の大規模言語モデルは、**知識と論理を同一のパラメータ空間に融解させている。**

「フランスの首都はパリである」という**事実**と、「AならばB、BならばC、ゆえにAならばC」という**推論規則**が、同じ重み行列の中に、区別なく、連続的な確率分布として同居している。この融合こそが、現行アーキテクチャの三つの病理すべての原因である。

**病理1：巨大化。**
パラメータの圧倒的大部分は、インターネットの記憶に費やされている。モデルが巨大でなければならないのは、推論が難しいからではなく、**世界の事実を全部覚えようとしているから**である。

**病理2：幻覚の検出不能性。**
知識がパラメータに溶けているため、モデルが事実を捏造したとき、その出力は正しい出力と**構造的に区別がつかない**。どちらも文法的に完璧な自然言語であり、同じ確率過程から生成される。外部から見て、「知っていて答えた」のか「知らずに埋めた」のかを判別する手段がない。

**病理3：監査不能性。**
推論過程が自然言語のChain-of-Thoughtとして出力されても、それは**事後的な作話でありうる**。実際の計算経路と、出力された説明文が一致している保証はどこにもない。したがって高リスク領域で採用できない。

これら三つは、別々の問題ではない。**すべて「知識と論理が同じ場所にある」ことの帰結である。**

## 1.2 The Wager / 本企画の賭け

**EN** — Framingo dismantles this fusion.

> **The model is made to master logic, completely, and logic alone. It is given no knowledge at all.**
> **Knowledge is obtained from outside by function calling and placed in context for the model to think with.**
> **The medium connecting the two is a formal language without ambiguity.**

The division of labour:

| Component / 構成要素 | Responsible for / 担うもの | Implementation / 実装 |
| --- | --- | --- |
| **Logic Core (the model) / 論理コア（モデル）** | Inference, entailment, state transition, quantification, contradiction detection / 推論、含意、状態遷移、量化、矛盾検出 | A small trained Transformer / 学習された小規模Transformer |
| **Knowledge / 知識** | Every fact, proper name, current event, specialist datum / あらゆる事実、固有名、時事、専門情報 | External data sources, function calling / 外部データソース／Function Calling |
| **Medium / 媒体** | The representation connecting the two / 両者を繋ぐ表現形式 | Framingo, a designed formal language / Framingo（設計された形式言語） |
| **Minimal core / 最小核** | Basic axioms of the world ("humans are mortal" and the like) / 世界の基礎公理（「人は死ぬ」の類） | A tiny set embedded in the model / モデル内に埋め込む極小の集合 |

The model **need not know** that Paris is the capital of France. That is retrieved and placed in context. What the model bears is only the operation of drawing valid conclusions from the propositions placed there.

**JA** — Framingoは、この融合を解体する。

> **モデルには論理だけを完全に習得させる。知識は一切持たせない。**
> **知識は Function Calling によって外部から取得し、コンテクストに載せて思考させる。**
> **両者を繋ぐ媒体として、曖昧性を持たない形式言語を用いる。**

役割分担は上表の通りである。

モデルは、パリがフランスの首都であることを**知らなくてよい**。それは検索して文脈に置かれる。モデルが担うのは、文脈に置かれた命題群から妥当な結論を導く操作だけである。

## 1.3 What This Makes Possible / これが何を可能にするか

**EN** —

**Freeing the parameters.**
Once knowledge is externalized, the parameters can be spent entirely on logic. **"How many parameters does a language model need if it carries logic alone?"** — no one has answered this. The answer may be several orders of magnitude smaller than current models.

**Making hallucination detectable.**
This matters most, and it is the subject of the next chapter.

**Making reasoning auditable.**
Every inference step is written in a machine-readable formal language, so it can be parsed and checked. What gets inspected is not a chain of thought as confabulation, but **the actual inference path itself.**

**JA** —

**パラメータの解放。**
知識を外部化すれば、パラメータは論理に全振りできる。**「論理だけを担う言語モデルは、何パラメータで足りるのか」** ——この問いに誰も答えていない。答えは、現行モデルより数桁小さい可能性がある。

**幻覚の可検出化。**
これが最重要であり、次章の主題である。

**推論の監査可能性。**
すべての推論ステップが機械可読な形式言語で記述されるため、パースして検証できる。作話としてのCoTではなく、**実際の推論経路そのもの**が検査対象になる。

---
# Chapter 2: Why It Must Be a Formal Language / 第2章：なぜ形式言語でなければならないか

**EN** — **English is fine as vocabulary. It has no てにをは.**

English is not without role marking: it has prepositions. But prepositions mark only the peripheral arguments.

| Role / 役割 | Japanese / 日本語 | English / 英語 |
|---|---|---|
| `tool:` | **で** | *with* (polysemous / 多義) |
| `src:` | **から** | *from* (polysemous / 多義) |
| `dst:` | **へ / に** | *to / into / onto* (split / 分裂) |
| `loc:` | **で / に** | *in / on / at* (split / 分裂) |
| **`agt:`** | **が** | **Unmarked. Position only / 標示なし。位置のみ** |
| **`tgt:`** | **を** | **Unmarked. Position only / 標示なし。位置のみ** |

**The two most important arguments — who, and to what — carry no marker at all.** Old English marked case by inflection; as the inflections wore away, the means of marking core arguments went with them, and word order took over the load.

A language whose word order carries the roles cannot spend its word order on viewpoint. To make "the bread" the subject, English must move the noun, recast the verb into the passive, and demote the agent into a *by*-phrase. Japanese, whose particles carry the roles, can say 「パンをジョンが切った」: the order changes, the verb does not. Japanese has a passive too; the difference is that in English, **because word order is occupied by the roles, shifting viewpoint means rebuilding the sentence.** The old draft called this the "viewpoint-dependent syntactic twist". The twist is no stylistic accident. It is what a missing marker costs.

This bears directly on the problem of this chapter.

```
John cut the bread with a knife.
The bread was cut by John with a knife.
```

One relation, two different strings. And since the roles can be read only from position, judging "which proposition in context does this relation derive from" first requires parsing the sentence to recover who did what — that is, it requires understanding. With the roles marked:

```
Cut agt:John tgt:Bread tool:Knife
Cut tgt:Bread tool:Knife agt:John
```

Both are the same set, {`Cut`, `agt:John`, `tgt:Bread`, `tool:Knife`}; the order does not touch meaning. A relation becomes a set of role–identifier pairs, and judging its provenance reduces to set inclusion (section 2.2).

The design follows in one line: **the vocabulary was never the problem. Keep it. Replace the role marking.**

Supplying the marking, however, is not itself the aim.

**JA** — **英語は語彙としては申し分ない。だが「てにをは」がない。**

英語に役割標示がないわけではない。前置詞がある。しかし前置詞は周辺項しか標示しない。（上表参照）

**最も重要な二つの項——誰が、何を——に、印が一切ない。** 古英語は屈折によって格を示したが、屈折が摩耗したとき、中核項を標示する手段もろとも失われ、その負荷を語順が引き受けた。

語順が役割を担っている言語では、語順を視点のために使えない。「パン」を主語に据えるには、英語は名詞を移し、動詞を受動形に組み替え、動作主を *by* 句へ降格させねばならない。助詞が役割を担う日本語は、「パンをジョンが切った」と言える。語順は変わるが、動詞は変わらない。受動態は日本語にもある。違いは、英語では**語順が役割に占有されているため、視点を動かすことが文を組み替えることを意味する**点にある。旧文書はこれを「視点に依存した統語的ねじれ」と呼んだ。このねじれは文体上の偶然ではない。印の欠落の代償である。

これは本章の問題に直結する。（上例参照）

同一の関係が、二つの異なる文字列になる。しかも役割は位置からしか読めないため、「この関係は文脈のどの命題に由来するか」を判定するには、まず文を構文解析して誰が何をしたかを復元しなければならない。すなわち理解が要る。役割が標示されていれば、二つは同じ集合 {`Cut`, `agt:John`, `tgt:Bread`, `tool:Knife`} であり、並べ方は意味に触れない。関係は役割と識別子の組の集合になり、由来判定は集合の包含に還元される（2.2節）。

設計は一行で従う。**問題は語彙ではなかった。語彙は保つ。役割標示だけを差し替える。**

ただし、標示を補うこと自体が目的なのではない。

## 2.1 The Aim Is Not "Eliminating Ambiguity" / 目的は「曖昧性の排除」ではない

**EN** — To give "because it has no ambiguity" as the reason for adopting a formal language is to mistake the aim. Eliminating ambiguity is a **means**, not the end.

The true aim is this:

> **To make it possible to judge, of a model's output, "this is fabricated" — mechanically, deterministically, and from outside.**

In natural language this is impossible in principle. A grammatically flawless lie cannot be told apart, at the surface, from a grammatically flawless truth. Judging it requires another language model, and that model hallucinates too.

**JA** — 形式言語を採用する理由を「曖昧さがないから」と述べると、目的を取り違える。曖昧性の排除は**手段**であって目的ではない。

真の目的はこれである。

> **モデルの出力に対して、「これは捏造である」という判定を、機械的に、決定論的に、外部から下せるようにすること。**

自然言語では、これは原理的に不可能である。文法的に完璧な嘘は、文法的に完璧な真実と、表層において区別できない。判定にはもう一つの言語モデルが要り、そのモデルもまた幻覚する。

## 2.2 The Grounding Constraint / 接地制約

**EN** — With a formal language, the following constraint **can be imposed at the level of syntax.**

> **The Grounding Constraint: every entity, predicate and relation appearing in the model's output must derive from one of the following.**
> **(a) the minimal core axioms embedded in the model**
> **(b) knowledge present in context at that moment**
> **(c) a proposition derived from the two above by an explicitly stated inference rule**
>
> **The appearance of a token deriving from none of these is, by definition, a hallucination, and is detectable by string matching.**

This is the technical core of the project.

In natural language this constraint cannot be written down, because judging "derives from context" itself demands understanding of meaning. In Framingo, entities appear as normalized identifiers, so **judging provenance reduces to set operations.**

**JA** — 形式言語を使うと、次の制約を**構文レベルで課すことができる。**

> **接地制約：モデルの出力に現れるすべての実体・述語・関係は、次のいずれかに由来しなければならない。**
> **(a) モデル内に埋め込まれた最小核公理**
> **(b) その時点でコンテクストに載っている知識**
> **(c) 上の二つから、明示された推論規則によって導出された命題**
>
> **これらのいずれにも由来しないトークンの出現は、定義により幻覚であり、文字列照合によって検出できる。**

これが本企画の技術的中核である。

自然言語では、この制約は書き下せない。「文脈に由来する」の判定自体が意味理解を要求するからである。Framingoでは、実体は正規化された識別子として現れるため、**由来判定が集合演算に還元される。**

## 2.3 The Analogy with Type Systems / 型システムとの類比

**EN** — This is the same kind of invention as the **type system** in programming languages.

A type system does not make programmers smarter. Nor does it make programs correct. A type system does exactly one thing: it **makes one kind of error mechanically detectable, before execution.** That alone changed the reliability of software engineering qualitatively.

Framingo aims at the same. It does not make the model smarter. **It makes the error class called hallucination mechanically detectable before it propagates.**

Most current efforts aim to "lower the hallucination rate" — that is, a continuous improvement in error rate. This project aims at a **discrete shift**: not fewer hallucinations, but **hallucination as an identifiable event.**

**JA** — これは、プログラミング言語における**型システム**と同じ種類の発明である。

型システムはプログラマを賢くしない。プログラムを正しくもしない。型システムがやるのはただ一つ、**ある種類の誤りを、実行前に、機械的に検出可能にする**ことである。それだけで、ソフトウェア工学の信頼性は質的に変わった。

Framingoが目指すのも同じである。モデルを賢くするのではない。**幻覚という誤りのクラスを、伝播する前に、機械的に検出可能にする。**

現行の取り組みのほとんどは「幻覚率を下げる」——すなわちエラー率の連続的な改善——を目指している。本企画が目指すのは**離散的な転換**である：幻覚を減らすのではなく、**幻覚を識別可能な事象にする。**

## 2.4 Why Existing Formal Languages Will Not Do / なぜ既存の形式言語では駄目なのか

**EN** — Lojban, first-order predicate logic, PDDL, AMR: formal languages already exist in number. The reasons for not using them are clear.

- **A human cannot learn them in five minutes.** They fail the auditability requirement described later.
- **They were not designed as a training medium.** They were designed for humans to speak, or to feed symbolic reasoners, and **were not optimized as a training distribution for gradient descent.**
- **They are token-inefficient.** The quantifiers and bound variables of first-order logic are costly structures for a Transformer.

Framingo's language specification (the former chapters 2–4, now `language-spec.md`) matters because it is designed to satisfy all three conditions at once. The details of the specification are negotiable, but **the three conditions — "learnable in five minutes", "efficient to train on", "grounding judged mechanically" — are non-negotiable constraints.**

**JA** — Lojban、一階述語論理、PDDL、AMR。既存の形式言語は多数ある。これらを使わない理由は明確である。

- **人間が5分で習得できない。** 後述する監査可能性の要件を満たさない。
- **学習媒体として設計されていない。** それらは人間が話すため、あるいは記号的推論器に食わせるために設計されており、**勾配降下法の訓練分布として最適化されていない。**
- **トークン効率が悪い。** 一階述語論理の量化子と束縛変数は、Transformerにとって高コストな構造である。

Framingoの言語仕様（旧第2〜4章、現 `language-spec.md`）が意味を持つのは、この三条件を同時に満たす設計だからである。仕様の細部は交渉可能だが、**「5分で習得可能」「学習効率が高い」「接地判定が機械的」の三条件は交渉不可能な制約である。**

---

# Chapter 3: Architecture / 第3章：アーキテクチャ

## 3.1 The Three Layers / 三層構造

```
        The world of natural language — humans, documents, the Web
        自然言語の世界（人間・文書・Web）
                    │
    ┌───────────────┴──────────────────────────────┐
    │  Translation Boundary / 翻訳境界              │  ← hallucination is localized here
    │  NL ⇄ Framingo                                │  ← the only place that needs auditing
    └───────────────┬──────────────────────────────┘
                    │  Framingo
    ┌───────────────┴──────────────────────────────┐
    │  Logic Core / 論理コア                        │  ← holds no knowledge
    │  · small Transformer                          │  ← trained on logic only
    │  · holds only the minimal core axioms         │
    │  · emits only under the Grounding Constraint  │
    └───────────────┬──────────────────────────────┘
                    │  Function Call (query in Framingo form)
    ┌───────────────┴──────────────────────────────┐
    │  Knowledge Layer / 知識供給層                 │
    │  · search / DB / API / sensors / simulators   │
    │  · returns results normalized into Framingo   │
    └──────────────────────────────────────────────┘
```

## 3.2 Responsibilities of Each Layer / 各層の責務

**EN** —

**Translation Boundary.**
Maps human utterances and external documents into Framingo, and maps results back into natural language. **It is the only place in this project where hallucination can arise.** For now, in-context conversion by an existing LLM suffices as its implementation (Framingo being designed to be learnable in five minutes).

**Logic Core.**
The main object of the project. It has never seen natural language. It holds no factual knowledge. Given a set of Framingo propositions, it outputs only valid derivations. Its output always satisfies the Grounding Constraint; output that does not is rejected by the verifier.

**Knowledge Layer.**
The Logic Core judges "what is missing" and issues a query in Framingo form. The reply is normalized into Framingo and placed in context. Only here does the model learn that "Paris is the capital of France" — **temporarily, and only in context.**

**JA** —

**翻訳境界。**
人間の発話や外部文書をFramingoへ写像し、逆に結果を自然言語へ戻す。**本企画において幻覚が発生しうる唯一の場所である。** 実装は当面、既存LLMのin-context変換で足りる（Framingoは5分で習得可能に設計されているため）。

**論理コア。**
本企画の主対象。自然言語を一度も見たことがない。事実知識を持たない。入力されたFramingo命題群に対して、妥当な導出のみを出力する。出力は必ず接地制約を満たす。満たさない出力は検証器が弾く。

**知識供給層。**
論理コアが「何が足りないか」を判断し、Framingo形式でクエリを発行する。返答はFramingoに正規化されてコンテクストへ載る。ここで初めて、モデルは「パリがフランスの首都である」ことを知る——**一時的に、文脈の上でのみ。**

## 3.3 Localizing Hallucination / 幻覚の局在化

**EN** — A key recognition: **this design does not bring hallucination to zero.** Hallucination can still enter at the Translation Boundary.

But this is not a retreat. **In the current architecture hallucination is diffused through the entire reasoning process; in this design it is localized to a single, explicit, auditable interface.**

- Localized hallucination **can be inspected intensively, there alone**
- The output of translation is Framingo, so **it can be put through the verifier**
- Inside the Logic Core, the Grounding Constraint ensures **no new hallucination is born**

Not "there is no hallucination", but **"the place where hallucination enters is fixed at one point, and can be inspected there"** — this is a goal both achievable and sufficient in practice.

**JA** — 重要な認識：**この設計は幻覚をゼロにしない。** 翻訳境界には依然として幻覚が入りうる。

しかしこれは後退ではない。**現行アーキテクチャでは幻覚が推論の全過程に拡散しているのに対し、本設計ではそれが単一の、明示された、監査可能なインターフェースに局在する。**

- 局在した幻覚は、**そこだけを集中的に検査できる**
- 翻訳の出力はFramingoなので、**検証器にかけられる**
- 論理コアの内部では、接地制約により**新たな幻覚が生まれない**

「幻覚がない」ではなく、**「幻覚が入る場所が一箇所に確定しており、そこで検査できる」**——これが達成可能かつ実用上十分な目標である。

---

# Chapter 4: What Goes into the Model, and What Does Not / 第4章：モデルに何を入れ、何を入れないか

## 4.1 What Stays Out / 入れないもの

**EN** — All factual knowledge. Proper nouns, geography, history, current events, specialist knowledge, statistics, personal names, product names. None of these goes into the model.

**JA** — 事実知識のすべて。固有名詞、地理、歴史、時事、専門知識、統計、人名、製品名。これらは一切モデルに入れない。

## 4.2 What Goes In / 入れるもの

**EN** —

**(a) Logical operations**
Entailment, negation, quantification and its scope, conditional branching, contradiction detection, transitivity, chains of state transition, unfolding of counterfactuals, matching of goals against outcomes.

**(b) Minimal core axioms**
The tiny set of facts about the world without which no reasoning can proceed at all. "Humans die", "an object that loses its support falls", "the contents of a container move with the container", and the like.

**JA** —

**(a) 論理操作**
含意、否定、量化とその作用域、条件分岐、矛盾検出、推移律、状態遷移の連鎖、反事実の展開、目的と結果の照合。

**(b) 最小核公理**
世界について、それなしには一切の推論が成立しない極小の集合。「人は死ぬ」「支えを失った物は落ちる」「容器の中身は容器とともに移動する」の類。

## 4.3 The Boundary Need Not Be Exact — Resolved by Redundancy / 境界線は厳密である必要がない —— 冗長性による解消

**EN** — Is "humans die" logic or knowledge? At first sight this question looks like the hardest part of the project. The CYC project spent forty years trying to settle a "minimal core of common sense", and ended without settling it.

**In this project, however, the question need not be solved.**

**JA** — 「人は死ぬ」は論理か知識か。この問いは、一見すると本企画の最大の難所に見える。CYCプロジェクトは40年をかけて「常識の最小核」を確定しようとし、確定できずに終わった。

**しかし本企画において、この問いは解く必要がない。**

### (a) The Category of "Logic for the World" / 「世界にとっての論理」というカテゴリ

**EN** — First, a premise to correct. "Humans die" **is not logic for mathematics, but it is part of logic for the world.**

A system of mathematical reasoning needs no such proposition. But every piece of reasoning that involves humans, living things, time or action cannot take a single step without it. A model that cannot derive "he is probably still alive" from "he was born ten years ago" does not stand as intelligence.

The minimal core therefore cannot consist of the inference rules of formal logic alone. **It must include a body of axioms stating that the world behaves in such-and-such a way.** Cut this layer away as "knowledge, so it goes outside", and intelligence itself cannot stand.

**JA** — まず前提を正す。「人は死ぬ」は、**数学にとっては論理ではないが、世界にとっては論理の一部である。**

数学的推論の体系にこの命題は不要である。しかし、人間・生物・時間・行為の関わるあらゆる推論は、これなしには一歩も進まない。「彼は10年前に生まれた」から「彼はまだ生きている可能性が高い」を導けないモデルは、知能として成立しない。

したがって最小核は、形式論理の推論規則だけでは足りない。**世界がそのように振る舞うという公理群を含まなければならない。** この層を「知識だから外に出す」と切り捨てると、知能そのものが立たない。

### (b) The Boundary Is Redundant, Not Exclusive / 境界は排他的ではなく冗長である

**EN** — Here is the decisive design judgment.

> **The minimal core and the external knowledge base are not partitioned exclusively. They may overlap.**
>
> **When the model asks, just to be sure, "do humans die?", the knowledge base should answer "humans die."**

Ambiguous items are **placed both inside and outside.** Whatever cannot be confidently classified can simply be put in both. The existence of this "just to be sure" region is actively permitted by design.

**JA** — 決定的な設計判断はここである。

> **最小核と外部知識ベースは、排他的に分割されない。両者は重複してよい。**
>
> **モデルが念のため「人は死ぬか」と問い合わせたとき、知識ベースは「人は死ぬ」と答えるべきである。**

曖昧な項目は、**内側にも外側にも置く。** どちらに分類すべきか判断がつかないものは、両方に入れておけばよい。この「念のため」領域の存在を、設計として積極的に許容する。

### (c) Why This Dissolves the Problem / これが問題を解消する理由

**EN** — CYC collapsed because **its hand-written core was the sole source of knowledge.** A gap in the core meant, directly, a breakdown of reasoning. So the core had to be complete, and completeness was unattainable.

In this design, core and exterior are **duplicated.**

| Situation / 事態 | Consequence / 帰結 |
| --- | --- |
| Forgotten in the core / 核に入れ忘れた | External search picks it up. **No problem** / 外部検索が拾う。**問題なし** |
| Absent from the exterior / 外部に無かった | The core has it. **No problem** / 核が持っている。**問題なし** |
| Present in both / 両方にある | Redundant. **No problem** (cost only) / 冗長。**問題なし**（コストのみ） |
| Absent from both / 両方に無い | Only this is a true gap / これのみが真の欠落 |

**The one remaining problem is the "absent from both" case, and that is a problem not of definition but of coverage.** A definitional problem cannot be solved; coverage can be measured and improved. **What matters is that the kind of problem has changed.**

**JA** — CYCが崩壊したのは、**手書きの核が唯一の知識源だった**からである。核の抜けは、そのまま推論の破綻を意味した。ゆえに核は完全でなければならず、完全性は達成不可能だった。

本設計では、核と外部が**二重化されている。**（上表参照）

**残る唯一の問題は「両方に無い」ケースであり、これは定義の問題ではなく網羅性の問題である。** 定義問題は解けないが、網羅性は測定でき、改善できる。**問題の種類が変わったことが重要である。**

### (d) Reformulating the Question / 問いの再定式化

**EN** — The question of chapter 4 is therefore rewritten as follows.

- ~~Question (old): where is the boundary between logic and knowledge?~~ ← Unsolvable. The question that killed CYC
- **Question (new): how much is worth internalizing?** ← An engineering trade-off. Measurable

The criterion for internalizing is not "is this the correct classification?" but **"is it worth the cost of querying every time?"**

- Frequently referenced → high value in internalizing
- Forms the skeleton of reasoning → without internalizing, round trips to search explode
- Does not change over time → does not go stale once internalized
- Concerns a particular individual → do not internalize (it changes, and there are infinitely many)

This **can be decided empirically.** Run a prototype, profile its search calls, and promote what recurs into the core. **There is no need to guess the right answer at design time.**

**JA** — したがって、第4章の問いは次のように書き換わる。

- ~~問い（旧）：論理と知識の境界はどこか~~ ← 解けない。CYCを殺した問い
- **問い（新）：どこまでを内在化する価値があるか** ← 工学的トレードオフ。測定可能

内在化の判断基準は「正しい分類かどうか」ではなく、**「毎回問い合わせるコストに見合うか」** である。

- 参照頻度が高いもの → 内在化する価値が高い
- 推論の骨格をなすもの → 内在化しないと検索の往復が爆発する
- 時間で変化しないもの → 内在化しても陳腐化しない
- 特定の個体に関するもの → 内在化しない（変化するし、無限にある）

これは**経験的に決定できる**。プロトタイプを動かし、検索呼び出しのプロファイルを取り、頻出するものを核へ引き上げればよい。**設計時に正解を当てる必要がない。**

### (e) A Side Consequence: Dependence on Calibration Disappears / 副次的な帰結：較正（Calibration）への依存が消える

**EN** — There is a consequence that is easily overlooked but important.

One of the hard problems of current LLMs is "**knowing whether you know**" (calibration). A model does not know what it does not know, and so it fills the gap. This is an unsolved problem.

In this design, **the model need not know whether it knows.** Because redundancy is permitted, **whenever in doubt it can simply always query.** Retrieving again what the core already holds does no harm beyond the cost.

That is, this design **sidesteps, by design, its dependence on an unsolved hard problem (calibration).** Instead of "detecting what one does not know", the solution is "making it safe to always check."

**JA** — 見落とされやすいが重要な帰結がある。

現行LLMにおける難問の一つは「**自分が知っているかどうかを知ること**」（calibration）である。モデルは知らないことを知らないため、埋めてしまう。これは未解決問題である。

本設計では、**モデルは自分が知っているかどうかを知る必要がない。** 冗長性が許されているため、**疑わしければ常に問い合わせればよい。** 既に核が持っている情報を重ねて取得しても、害はコストだけである。

つまり本設計は、**未解決の難問（較正）への依存を、設計によって回避している。** 「知らないことを検出する」代わりに「常に確認しても安全にする」という解法である。

---

# Chapter 5: The Verifier as the Central Concept / 第5章：検証器という中心概念

## 5.1 A Formal Language Is Not Enough / 形式言語だけでは足りない

**EN** — AlphaZero, the proof models of Lean and Coq, Othello-GPT. The lineage that has succeeded in training intelligence on symbol strings humans cannot read shares, without exception, one point.

**Every one of them has a verifier that mechanically judges truth.**

Go has rules and a win/loss judgment. Lean has a type checker. **This lineage works not because its symbol strings are formal, but because correctness can be judged mechanically, from outside.** Being a formal language is merely the precondition for having a verifier.

In this project, therefore, **the design of the verifier takes priority** over the language specification.

**JA** — AlphaZero、Lean/Coqの証明モデル、Othello-GPT。人間が読めない記号列で知能を鍛えることに成功した系譜には、例外なく共通する一点がある。

**すべてに、真偽を機械的に判定する検証器がある。**

囲碁にはルールと勝敗判定がある。Leanには型検査器がある。**この系譜が成立するのは記号列が形式的だからではなく、正しさを外部から機械判定できるからである。** 形式言語であることは、検証器を持てるための前提条件にすぎない。

したがって本企画において、言語仕様よりも**検証器の設計が優先される。**

## 5.2 Logic Can Be Generated and Verified Without Contamination / 論理は、汚染なしに生成・検証できる

**EN** — Here lies this project's good fortune.

When an LLM generates training data, the LLM's hallucinations flow straight into that data. For a project whose starting point is the defects of LLMs' world models, this is a fatal circularity.

**But if what the model is taught is logic rather than knowledge, the circularity does not arise.**

Logical validity **can be generated deterministically and verified deterministically.** Chains of syllogisms, scopes of quantification, branches by premise inversion — all can be unfolded mechanically from rules and judged true or false mechanically. **Something of the same standing as the rules of Go exists in logic from the start.**

**JA** — ここに本企画の幸運がある。

学習データをLLMに生成させると、LLMの幻覚がそのまま学習データに混入する。これは、LLMの世界モデルの欠陥を出発点とする企画にとって致命的な循環である。

**しかし、モデルに教えるのが知識ではなく論理であるならば、この循環は発生しない。**

論理的妥当性は、**決定論的に生成でき、決定論的に検証できる。** 三段論法の連鎖も、量化の作用域も、前提反転による分岐も、規則から機械的に展開でき、機械的に真偽判定できる。**囲碁のルールと同じ地位のものが、論理には最初から存在する。**

## 5.3 Proposer and Verifier / 提案者と検証者の分業

**EN** —

| Target / 対象 | Generation / 生成 | Verification / 検証 | Risk of hallucination / 幻覚のリスク |
| --- | --- | --- | --- |
| **Logic Core (the body of training) / 論理コア（学習の本体）** | Deterministic engine / 決定論的エンジン | Deterministic / 決定論的 | **Structurally zero / 構造的にゼロ** |
| Surface variety, slot-order variation / 表層の多様性・スロット順ゆらぎ | LLM acceptable / LLM可 | Parser / パーサ | Irrelevant (does not touch meaning) / 無関係（意味に触れない） |
| NL⇄Framingo parallel data / NL⇄Framingo 対訳データ | LLM | Matching, human review / 照合・人手 | Localized here / ここに局在 |

The LLM proposes; the deterministic engine verifies. This adopts the AlphaGo configuration as it stands.

And what matters is that **for the logic — the very body of what the model learns — contamination from LLMs can be brought to zero.**

**JA** — （上表参照）

LLMは提案者、決定論的エンジンは検証者。AlphaGoの構図をそのまま採用する。

そして重要なのは、**モデルが学ぶ本体である論理部分に限っては、LLM由来の汚染をゼロにできる**ことである。

## 5.4 Corpus Supply Is Not a Constraint / コーパス供給は制約ではない

**EN** — Contrary to the assumption of the old draft, a shortage of corpus is not an obstacle for this project.

A language model cannot be built on Lojban because it has only a few dozen speakers and its real-world text does not reach a few million words. **Framingo is designed so that an English speaker can learn it in five minutes, so existing LLMs can be used in context as generators.** Syntactic variety can be supplied without limit.

And semantic correctness, as described above, is guaranteed by the deterministic engine. **Squeezed from both sides, a large and uncontaminated corpus results.**

**JA** — 旧文書の想定と異なり、コーパス不足は本企画の障害ではない。

Lojbanで言語モデルが作れないのは、話者が数十人しかおらず、実文書が数百万語に届かないからである。**Framingoは英語話者が5分で習得できるよう設計されているため、既存LLMをin-contextで生成器として使える。** 構文的な多様性はいくらでも供給できる。

そして意味的な正しさは、上述の通り決定論的エンジンが担保する。**両側から挟むことで、大規模かつ汚染のないコーパスが得られる。**

---

# Chapter 6: Humans Cross Over to the Formal Language / 第6章：人間が形式言語の側へ渡る

## 6.1 An Arrangement Unchanged for Half a Century / 半世紀動いていない配置

**EN** — Every existing system takes this arrangement.

```
[Human / 人間] ──natural language / 自然言語──> [Model / モデル] ──formal language / 形式言語──> [World, computation / 世界／計算]
```

Code-generation models, theorem-proving assistants, semantic parsing, robotics planners, dataflow representations of dialogue. **The formal language is always on the machine's side; natural language is always on the human's side.** Even SHRDLU (1972), while handling a fully formal blocks world, conversed with humans in English.

This project changes the arrangement.

```
[Human / 人間] ──formal language / 形式言語──> [Model / モデル] ──formal language / 形式言語──> [World / 世界]
```

**JA** — 既存のあらゆるシステムは、この配置を取っている。（上図参照）

コード生成モデル、定理証明支援、セマンティックパージング、ロボティクスのプランナ、対話のデータフロー表現。**形式言語は常に機械側にあり、人間側には常に自然言語がある。** SHRDLU（1972）でさえ、完全に形式的なブロック世界を扱いながら、人間との対話は英語だった。

本企画は、この配置を変更する。（上図参照）

## 6.2 What the "Learnable in Five Minutes" Constraint Means / 「5分で習得可能」という設計制約の意味

**EN** — This constraint is not an aesthetic of making the language easy. **It is a necessary condition for auditability.**

Even if the reasoning process is machine-readable, it is no audit if humans cannot read it. If reasoning is written in a language a human can learn in five minutes, **experts can verify every step of the reasoning directly.**

A natural-language chain of thought may be post-hoc confabulation, but a Framingo inference chain can be parsed and verified, and a human can follow it by eye. **This duality — machine-verifiable and human-readable — decides whether adoption in high-stakes domains is possible.**

**JA** — この制約は、言語を簡単にするための美学ではない。**監査可能性の必要条件である。**

推論過程が機械可読であっても、人間が読めなければ監査にならない。人間が5分で習得できる言語で推論が記述されるならば、**専門家は推論の全ステップを直接検証できる。**

自然言語のCoTは事後的な作話でありうるが、Framingoの推論連鎖はパースして検証でき、かつ人間が目で追える。**この二重性——機械検証可能かつ人間可読——が、高リスク領域での採用可能性を決める。**

## 6.3 The Absence of Precedent / 前例の不在

**EN** — To my knowledge, **there is no case of training a model whose native medium is a designed formal language and then holding a conversation with humans in that language.**

It has not been done not because it is difficult, but because it did not pay. The field's reward function is natural-language benchmarks, and "a model that speaks a language nobody speaks" earns no credit. **But if the reward function changes to "detectability of hallucination" and "auditability of reasoning", this arrangement becomes rational.**

**JA** — 私の知る限り、**設計された形式言語をネイティブな媒体とするモデルを訓練し、人間とその言語で対話を成立させた例は存在しない。**

やられていないのは困難だからではなく、割に合わなかったからである。分野の報酬関数は自然言語ベンチマークであり、「誰も話せない言語を話すモデル」は評価されない。**しかし報酬関数が「幻覚の検出可能性」と「推論の監査可能性」に変わるならば、この配置は合理的になる。**

## 6.4 What Is Missing: The Dialogue Layer / 欠落：対話層

**EN** — The current language specification (the former chapters 2–4, now `language-spec.md`) **has no dialogue layer at all.**

- No distinction between speaker and hearer
- No distinction of speech acts (there is `QUERY:`, but no assertion, request, confirmation, denial or correction)
- No turn structure
- No anaphora across turns (both `It` and `<A>` close within a single sentence)
- No model of shared context (what both parties already know)

If "holding a conversation with humans" is set as a destination, this must be filled in. Its priority, however, is lower than the boundary problem of chapter 4.

**JA** — 現行の言語仕様（旧第2〜4章、現 `language-spec.md`）には、**対話層が一切存在しない。**

- 話者・聴者の区別がない
- 発話行為の区別がない（`QUERY:` はあるが、断定・要求・確認・否認・訂正がない）
- ターン構造がない
- ターンをまたぐ照応がない（`It` も `<A>` も一文内で閉じている）
- 共有文脈（両者が何を既に知っているか）のモデルがない

「人間と会話を成立させる」を到達点に据えるならば、これは埋めなければならない。ただし優先度は第4章の境界問題より低い。

---

# Chapter 7: The Place of the Language Specification (Demoting the Former Chapters 2–4) / 第7章：言語仕様の位置づけ（旧第2〜4章の格下げ）

**EN** — The language specification defined in chapters 2–4 of the old draft — event-centred flat case frames, order-invariant slots, concept composition by dot notation, the causal connectives `->` / `!>`, and `when:` / `goal:` / `reason:` — remains valid.

But these are **means, not claim.** The project's central thesis lies in chapters 1–2; the language specification is merely an engineering choice for realizing it. Its details may be changed as freely as needed, provided they satisfy the higher requirements (learnable in five minutes / training efficiency / mechanical grounding judgment).

There is, however, one part of the specification that carries an engineering wager beyond mere means.

**JA** — 旧文書の第2〜4章で定義された言語仕様——事象中心のフラットな格フレーム、順序不変なスロット、ドット記法による概念合成、`->` / `!>` の因果結合子、`when:` / `goal:` / `reason:`——は、依然として有効である。

しかしこれらは**主張ではなく手段である。** 本企画の中心命題は第1〜2章にあり、言語仕様はそれを実現するための工学的選択にすぎない。仕様の細部は、上位の要件（5分で習得可能／学習効率／接地判定の機械化）を満たす限り、いくらでも変更されてよい。

なお、仕様の中で一点だけ、単なる手段を超えた工学的賭けを含む部分がある。

## 7.1 Invariance as String Persistence / 不変性の文字列化

```
Cut tgt:Sweet.Red.Apple -> Become agt:Sweet.Red.Apple.Slice
```

**EN** — The intrinsic attributes `Sweet` and `Red` remain as they are on the right-hand side. **This converts the frame problem into a string-copy operation.**

In PDDL, frame axioms must be written out explicitly, and that was one of the things that suffocated symbolic AI. Framingo reduces conservation laws to **a form expressible by the circuit a Transformer implements most cheaply (the induction head).**

This is not a semantic claim but **an engineering claim: "the form of representation determines learnability."** Within this project, it is the only element that belongs to the language specification yet has independent value as something to test.

**JA** — 内在的属性 `Sweet` `Red` が右辺にそのまま残る。**これはフレーム問題を文字列コピー操作に変換している。**

PDDLならフレーム公理を明示的に書かねばならず、それが記号AIを窒息させた一因だった。Framingoは保存則を、**Transformerが最も安く実装できる回路（induction head）で表現可能な形**に落としている。

これは意味論の主張ではなく、**「表現形式が学習可能性を決める」という工学的主張**である。本企画の中で、言語仕様に属しながら独立した検証価値を持つ唯一の要素である。

---

# Chapter 8: Falsifiable Claims / 第8章：反証可能な主張

**EN** — This project tests the following propositions. **Each is stated in a form that can be falsified.**

**Proposition 1 (parameter efficiency)**
A model that externalizes knowledge and learns logic alone achieves equivalent logical reasoning ability with several orders of magnitude fewer parameters than current LLMs.
→ *Falsified if: logical ability depends strongly on the amount of knowledge, and formal reasoning does not hold up in small models.*

**Proposition 2 (detection by the Grounding Constraint)**
For the output of a model trained under the Grounding Constraint, the hallucination detection rate reaches a practical level (e.g. 99% or above).
→ *Falsified if: the model frequently generates output that evades the Grounding Constraint (wrong recombinations of existing tokens, etc.).*

**Proposition 3 (learning efficiency through form)**
Holding semantic content fixed and varying only the surface form, a role-tagged flat form shows higher compositional generalization than a word-order-dependent form.
→ *Method: render from the same world model in both forms, and compare on the same hold-out.*
→ *Falsified if: no difference appears. The conclusion would then be "not the form but the structure of the generator is everything" — itself an important finding.*

**Proposition 4 (transfer of invariance)**
A model trained on conservation laws explicitly encoded as string persistence generalizes to other kinds of invariants that were not so encoded.
→ *Falsified if: it does not generalize. In that case the model has learned "copying", not "invariance", and a central assumption of the project is falsified.*

**Proposition 5 (dialogue)**
A small model that has never seen natural language and a human hold a multi-turn conversation about a shared context, in Framingo alone.
→ *This is a destination without precedent.*

**JA** — 本企画は、以下の命題を検証する。**どれも反証されうる形で述べる。**

**命題1（パラメータ効率）**
知識を外部化し論理のみを学習したモデルは、同等の論理的推論能力を、現行LLMより数桁少ないパラメータで達成する。
→ *反証条件：論理能力が知識量に強く依存し、小規模モデルでは形式的推論が成立しない場合。*

**命題2（接地制約による検出）**
接地制約下で訓練されたモデルの出力に対し、幻覚の検出率が実用水準（例：99%以上）に達する。
→ *反証条件：モデルが接地制約を回避する出力（既存トークンの誤った組み替え等）を高頻度で生成する場合。*

**命題3（形式による学習効率）**
意味内容を固定したまま表層形式のみを変えたとき、役割タグ付きフラット形式は語順依存形式より高い組成的汎化を示す。
→ *検証法：同一の世界モデルから二形式でレンダリングし、同一のhold-outで比較する。*
→ *反証条件：差が出ない場合。この場合「形式ではなく生成器の構造がすべて」という結論になり、これも重要な知見である。*

**命題4（不変性の転移）**
文字列永続性として明示的にエンコードした保存則で訓練したモデルは、エンコードしなかった別種の不変量にも汎化する。
→ *反証条件：汎化しない場合。この場合、モデルは「不変性」ではなく「コピー」を学習しており、企画の中心的仮定が反証される。*

**命題5（対話成立）**
自然言語を一度も見ていない小規模モデルと人間が、共有された文脈について、Framingoのみで多ターンの対話を成立させる。
→ *これは前例のない到達点である。*

---

# Chapter 9: Unsolved Design Problems / 第9章：未解決の設計問題

**EN** — Listed honestly, in order of priority.

**(1) Coverage of the minimal core** — Section 4.3. **Settling** the boundary is no longer needed (dissolved by redundancy), but the true gap, "in neither the core nor the exterior", remains. This is a problem not of definition but of coverage, and can be measured and improved. For now: fix an initial set for the core, run it, and promote items empirically from the profile of search calls.

**(2) Design of the Translation Boundary** — How to implement NL⇄Framingo conversion, and how to verify it. Since this is the only place where hallucination is localized, the inspection method here directly determines the project's reliability.

**(3) Can logic be learned without knowledge?** — Empirically, the reasoning ability of LLMs has grown in correlation with knowledge and scale. On the other hand, proof models are strong even at small scale within narrow formal domains. This is an open question, and this project in effect tests it.

**(4) Bootstrapping query issuance** — To fetch knowledge by function calling, the model must be able to judge "what is missing", yet that judgment requires knowledge. If the logic is strong, "the shape of the information needed" should be derivable, but this is unverified.

**(5) The missing dialogue layer** — Section 6.4.

**(6) Implementation of the verifier** — The design of an engine that judges logical validity deterministically. The claims of chapter 5 depend entirely on its existence.

**JA** — 正直に列挙する。順序は優先度順。

**(1) 最小核の網羅性** —— 第4.3節。境界の**確定**は不要になったが（冗長性により解消）、「核にも外部にも無い」という真の欠落は残る。これは定義問題ではなく網羅性の問題であり、測定と改善が可能である。当面は、核に何を入れるかの初期集合を決めて走らせ、検索呼び出しのプロファイルから経験的に引き上げる。

**(2) 翻訳境界の設計** —— NL⇄Framingo変換をどう実装し、どう検証するか。幻覚が局在する唯一の場所であるため、ここの検査手法は企画の信頼性を直接規定する。

**(3) 知識なしに論理は学べるか** —— 経験的には、LLMの推論能力は知識とスケールに相関して伸びている。一方で証明モデルは狭い形式領域なら小規模でも強い。これは開いた問いであり、本企画は事実上これを検証する。

**(4) クエリ発行のブートストラップ** —— Function Callingで知識を取るには「何が足りないか」を判断できねばならないが、その判断には知識が要る。論理が強ければ「必要な情報の形」は導出できるはずだが、未検証。

**(5) 対話層の不在** —— 第6.4節。

**(6) 検証器の実装** —— 論理的妥当性を決定論的に判定するエンジンの設計。第5章の主張はこれが存在することに全面的に依存している。

---

# Chapter 10: Where the Novelty Lies / 第10章：新規性の所在

**EN** — Stated precisely. Neither overstated nor understated.

**JA** — 正確に記す。過大にも過小にも述べない。

## 10.1 What Already Exists / 既出であるもの

**EN** —

- Event-centred case-frame semantics — neo-Davidsonian semantics, AMR, Conceptual Dependency (Schank 1972)
- Formalizing preconditions, effects and goals — STRIPS / PDDL, ATOMIC-2020
- Regular derivational morphology — Esperanto, Lojban
- The symbol grounding problem, the language of thought hypothesis — Fodor (1975), Harnad (1990)
- Training small models on synthetic formal languages — SCAN / COGS, bAbI, Othello-GPT, Physics of Language Models
- Injecting knowledge by retrieval — RAG
- Coupling symbolic and neural modules — neuro-symbolic AI in general
- The **claim** that "LLMs should be reasoning engines, not knowledge bases" — made repeatedly

**JA** —

- 事象中心の格フレーム意味論 —— ネオ・デイヴィドソン流意味論、AMR、Conceptual Dependency（Schank 1972）
- 前提条件・効果・目的の形式化 —— STRIPS / PDDL、ATOMIC-2020
- 規則的な派生形態論 —— エスペラント、Lojban
- 記号接地問題、思考の言語仮説 —— Fodor（1975）、Harnad（1990）
- 合成形式言語による小規模モデルの訓練 —— SCAN / COGS、bAbI、Othello-GPT、Physics of Language Models
- 検索による知識注入 —— RAG
- 記号モジュールと神経モジュールの結合 —— ニューロシンボリックAI全般
- 「LLMは知識ベースではなく推論エンジンであるべきだ」という**主張** —— 繰り返し述べられてきた

## 10.2 What Has No Confirmed Precedent / 前例が確認できないもの

**EN** —

- **Training a model whose native and sole medium is a designed formal language, without ever showing it natural language.** Existing formal-language-native models (proof assistants, code generation) are almost all initialized from models pretrained on natural language.
- **A design that deliberately excludes factual knowledge from the model.** RAG injects knowledge, but the model itself remains a natural-language LLM holding all its knowledge. The claim "it should be a reasoning engine" exists, but no case of actually building a model without knowledge can be confirmed.
- **Syntactic detection of hallucination by a Grounding Constraint.** Efforts to "reduce hallucination" are countless, but no architecture that "converts hallucination into a mechanically identifiable event" can be confirmed.
- **The symmetric arrangement in which humans cross over to the formal language.** For half a century, the formal language has always been on the machine's side and natural language always on the human's.
- **The combination of the four points above.**

**JA** —

- **設計された形式言語をネイティブかつ唯一の媒体とするモデルを、自然言語を一度も見せずに訓練すること。** 既存の形式言語ネイティブモデル（証明支援、コード生成）は、ほぼ全て自然言語事前学習済みモデルからの初期化である。
- **モデルから事実知識を意図的に排除する設計。** RAGは知識を注入するが、モデル自体は全知識を保持したままの自然言語LLMである。「推論エンジンであるべきだ」という主張はあっても、実際に知識を持たないモデルを構築した例を確認できない。
- **接地制約による幻覚の構文的検出。** 「幻覚を減らす」取り組みは無数にあるが、「幻覚を機械的に識別可能な事象へ転換する」アーキテクチャは確認できない。
- **人間が形式言語の側へ渡る対称的な配置。** 半世紀にわたり、形式言語は常に機械側、自然言語は常に人間側にあった。
- **上記四点の組み合わせ。**

## 10.3 The Difference from CYC / CYCとの差分

**EN** — The failure closest to this project is CYC. The differences should be made explicit.

| | CYC | Framingo |
| --- | --- | --- |
| Knowledge / 知識 | Written by hand (millions of propositions) / 手で書く（数百万命題） | **None. Injected from outside / 持たない。外部から注入** |
| Reasoning / 推論 | Symbolic deduction engine / 記号的演繹エンジン | **Trained neural model / 学習された神経モデル** |
| Exceptions / 例外処理 | Adding rules (infinite regress) / ルールの追加（無限後退） | **Absorbed as probability mass / 確率質量として吸収** |
| Completeness of the core / 核の完全性 | **Required** (sole source of knowledge) / **必須**（唯一の知識源のため） | **Not required** (redundant with the exterior) / **不要**（外部と冗長化されている） |
| Settling the boundary / 境界の確定 | Required. Never achieved; collapsed / 必須。達成できず崩壊した | **Not required. Ambiguous items go in both / 不要。曖昧な項目は両方に置く** |
| Cause of death / 死因 | Brittleness of symbolic deduction, the frame problem, an unfinished core / 記号的演繹の脆性、フレーム問題、核の未完成 | *None of these failure modes arises / いずれの失敗モードも発生しない* |

What killed CYC was not its representation but its reasoning mechanism. The same holds for Schank's Conceptual Dependency. **This project's wager is to use those representations not as "the input language of a symbolic reasoner" but as "a training distribution for gradient descent."** The failure modes that killed GOFAI do not arise in this configuration.

More important still, **this project need not solve the task that directly caused CYC's collapse — "settling the minimal core of common sense"** (section 4.3). CYC's hand-written knowledge was the sole source of knowledge, and so had to be complete. In this design the core and the external knowledge base are redundant, so gaps in the core are covered by search, and gaps in search by the core. **The wall CYC tried to break through head-on, and failed, this project walks around.**

**JA** — 本企画に最も近い失敗例はCYCである。差分を明確にしておく。（上表参照）

CYCを殺したのは表現ではなく推論機構だった。Schankの概念依存表現も同様である。**本企画の賭けは、それらの表現を「記号推論器の入力言語」ではなく「勾配降下法の訓練分布」として使うことにある。** GOFAIを殺した失敗モードは、この構成では発生しない。

さらに重要なのは、**CYCが崩壊した直接の原因である「常識の最小核を確定する」という課題を、本企画は解く必要がない**ことである（第4.3節）。CYCの手書き知識は唯一の知識源であり、ゆえに完全でなければならなかった。本設計では核と外部知識ベースが冗長化されているため、核の抜けは検索が補い、検索の抜けは核が補う。**CYCが正面から突破しようとして失敗した壁を、本企画は迂回する。**

---

# Chapter 11: The Recursive Improvement Loop / 第11章：再帰的改良のループ

> **Status of this chapter / 本章の位置づけ**
>
> **EN** — This chapter is a contribution by Claude (Opus 5). In response to the destination set out by the originator of the concept — "an intelligence that has been created brings in new insight, and that gives rise to the next intelligence" — it makes the mechanism concrete on top of this architecture. Its content is under consideration, not a settled specification.
>
> **JA** — 本章は Claude（Opus 5）による寄稿である。構想側から「創出された知能が新たな見解を持ち込み、それが次の知能を生む」という到達目標が示されたことを受け、その機構を本アーキテクチャの上で具体化した。
> 本章の内容は検討対象であり、確定仕様ではない。

## 11.1 Why Self-Improvement Loops Usually Fail / 自己改良ループが通常失敗する理由

**EN** — The idea of "a model builds a better model, and repeats" has been voiced again and again, yet in practice it almost never turns. The reason is clear.

**There is no verifier.**

When a model trains on its own output, model collapse occurs. Errors and biases amplify, and quality degrades generation by generation. **Self-improvement without a verifier is not ascent but drift.**

AlphaZero surpassed humanity through self-play alone not because it played itself. It was **because a mechanical judgment — win or loss — existed.** Which of the generated positions were good and which bad could be decided without relying on the model's opinion. This one point makes all the difference.

And in natural language, such a verifier cannot be built. There is no means of mechanically judging "is this claim correct?". Judging it requires another language model, and that model errs too. **So long as natural language is the medium, the loop does not close.**

**JA** — 「モデルがより良いモデルを作り、それを繰り返す」という構想は繰り返し語られてきたが、実際にはほぼ回らない。理由は明確である。

**検証器がないからである。**

モデルが自らの出力で訓練すると、モデル崩壊（model collapse）が起きる。誤差と偏りが増幅され、世代を経るごとに劣化する。**検証器のない自己改良は、上昇ではなくドリフトである。**

AlphaZeroが自己対戦のみで人類を超えたのは、自己対戦したからではない。**勝敗という機械判定が存在したから**である。生成された局面のうち、どれが良くどれが悪いかを、モデルの意見に依らずに決められた。この一点がすべてを分けている。

そして自然言語では、この検証器を作れない。「この主張は正しいか」を機械判定する手段がない。判定にはもう一つの言語モデルが要り、そのモデルもまた誤る。**ゆえに自然言語を媒体とする限り、ループは閉じない。**

## 11.2 Separating Knowledge from Logic Closes the Loop / 知識と論理の分離が、ループを閉じる

**EN** — Here is an asymmetry peculiar to this architecture.

| Target / 対象 | Mechanical verification / 機械検証 |
| --- | --- |
| **Correctness of knowledge / 知識の正しさ** | Impossible (only by observing the world) / できない（世界を観測するしかない） |
| **Logical validity / 論理的妥当性** | **Possible** (decidable deterministically) / **できる**（決定論的に判定可能） |

In current LLMs the two are fused in the same parameter space, so the loop is dragged toward the unverifiable side and never closes as a whole.

**If they are separated, the loop can be closed on the verifiable half alone.** And since knowledge is outside from the start, it never needs to enter the loop at all.

> **The self-improvement loop need close only over logic. It need not close over knowledge.**

This is a direct consequence of the separation in chapter 1. Not a by-product: **the design decision to separate knowledge from logic itself constitutes the possibility of self-improvement.** Chapter 5 said "the verifier is the central concept"; its reach does not stop at generating training data. **The verifier is the sole structure supporting the recursive side of this project.**

**JA** — ここに、本アーキテクチャ固有の非対称性がある。（上表参照）

現行LLMではこの二つが同一のパラメータ空間に融合しているため、検証不能な側に引きずられ、ループ全体が閉じない。

**分離されていれば、検証可能な半分だけでループを閉じられる。** そして知識は最初から外部にあるため、そもそもループに入れる必要がない。

> **自己改良ループは、論理の上でのみ閉じればよい。知識の上で閉じる必要はない。**

これは第1章の分離が生んだ直接の帰結である。副産物ではなく、**知識と論理を分離するという設計判断が、自己改良の可能性そのものを構成している。** 第5章で「検証器が中心概念である」と述べたが、その射程は学習データの生成にとどまらない。**検証器は、この企画の再帰的側面を支える唯一の構造物である。**

## 11.3 Linguistic Self-Extension — Legible Recursion / 言語的自己拡張 —— 可読な再帰

**EN** — Implementing self-improvement does not require self-modification of weights. There is a safer and more powerful route.

> **In this architecture, an intelligence can rewrite its own "language".**

When reasoning reaches a shortfall — "this cannot be expressed" — the system can propose a slot, a connective, a suffix, or a new epistemic prefix. Each generation's contribution appears as **a diff against the language specification.**

Recursion of this form has properties that weight modification lacks.

| | Self-modification of weights / 重みの自己改変 | Self-extension of language / 言語の自己拡張 |
| --- | --- | --- |
| Size of the diff / 差分の大きさ | Billions of parameters / 数十億パラメータ | A few lines / 数行 |
| Human readability / 人間可読性 | None / なし | **Yes / あり** |
| Mechanical verification / 機械検証 | Hard / 困難 | **Possible** (does the parser pass; does the existing corpus pass re-verification) / **可能**（パーサが通るか、既存コーパスが再検証を通るか） |
| Reversibility / 可逆性 | Practically impossible / 事実上不可能 | **git revert** |
| Attribution / 帰属 | Impossible / 不可能 | **Traceable per commit / コミット単位で追跡可能** |

**Against opaque and unbounded self-modification, this is legible recursion.**

A model whose medium is natural language cannot do this. **Natural language has no specification, so the act of proposing an extension cannot even be defined.** Here, for the first time, being a designed formal language takes on essential meaning.

**JA** — 自己改良の実装として、重みの自己改変は必要ない。より安全で、より強力な経路がある。

> **このアーキテクチャにおいて、知能は自らの「言語」を書き換えることができる。**

推論の過程で「これが表現できない」という不足に到達したとき、システムはスロット、結合子、接尾辞、あるいは新しい認識論的プリフィックスを提案できる。世代ごとの貢献は、**言語仕様への差分**として現れる。

この形の再帰には、重み改変にない性質がある。（上表参照）

**不透明かつ無制限な自己改変に対して、これは可読な再帰（legible recursion）である。**

自然言語を媒体とするモデルにはこれができない。**自然言語には仕様書が存在しないため、拡張の提案という行為が定義できない。** 設計された形式言語であることが、ここで初めて本質的な意味を持つ。

## 11.4 The Gradient to Climb / 登るべき勾配

**EN** — For the loop to turn, the quantity that rises must be defined. "Intelligence" cannot be measured, but the following can.

**(a) Expressive coverage**
The proportion of real-world reasoning cases that can be mapped into Framingo without loss of meaning.

**(b) Derivation acceptance rate**
The proportion of derivations generated by the model that the verifier accepts.

**(c) Grounding rate**
The proportion of output tokens that satisfy the Grounding Constraint (section 2.2). That is, the inverse of hallucination.

**(d) Logical efficiency**
The number of parameters required to achieve the same reasoning ability.

Once these are defined, a ratchet can be built.

**JA** — ループが回るには、上昇する量が定義されていなければならない。「知能」は測れないが、以下は測れる。

**(a) 表現被覆率（Expressive Coverage）**
実世界の推論事例のうち、意味を損なわずにFramingoへ写像できる割合。

**(b) 導出受理率（Derivation Acceptance Rate）**
モデルの生成した導出のうち、検証器が受理する割合。

**(c) 接地率（Grounding Rate）**
出力トークンのうち、接地制約（2.2節）を満たすものの割合。すなわち幻覚の裏返し。

**(d) 論理効率（Logical Efficiency）**
同一の推論能力を達成するのに要するパラメータ数。

これらが定義されると、ラチェットが構成できる。

```
  ① Meet a case that cannot be expressed
     表現できない事例に遭遇する
        ↓
  ② Propose a language extension (new slot / connective / prefix)
     言語拡張を提案する（新スロット／新結合子／新プリフィックス）
        ↓
  ③ Verify: does the parser pass / does the existing corpus re-verify / does coverage rise
     検証：パーサは通るか／既存コーパスは再検証を通るか／被覆率は上がるか
        ↓
  ④ Merge (approved by a human or a higher intelligence)
     マージ（人間または上位知能による承認）
        ↓
  ⑤ Regenerate the corpus in the extended language
     拡張された言語でコーパスを再生成
        ↓
  ⑥ Train the next-generation model → back to ①
     次世代モデルを訓練 → ①へ
```

**EN** — With each cycle, the language specification, the verifier and the corpus generator each gain a version. **Every step is auditable and reversible.**

**JA** — 各周回で、言語仕様と検証器とコーパス生成器が版を重ねる。**すべての工程が監査可能で、可逆である。**

## 11.5 Two Signals Are Needed / 信号は二つ必要である

**EN** — **This is the most important warning in this chapter.**

The verifier prevents the loop from **degrading.** It does not prevent it from **diverging.**

> **Validity does not guarantee soundness. If the premises are garbage, perfect logic outputs perfect garbage.**

Run the loop on internal signals alone, and the system may converge on **a formal system that is beautifully closed and describes nothing.** Expressive coverage and derivation acceptance rate keep rising, yet the world the language speaks of does not exist — such a local optimum exists. It is the road some lineages of formal semantics actually travelled.

AlphaZero did not have this problem **because the rules of the game were the world itself.** Internal and external signals coincided. In this project the two are separated, **and so both must be provided explicitly.**

| Signal / 信号 | Source / 供給元 | Prevents / 防ぐもの |
| --- | --- | --- |
| **Internal signal / 内部信号** | The verifier (logical validity) / 検証器（論理的妥当性） | **Degradation** of the loop (model collapse) / ループの**劣化**（モデル崩壊） |
| **External signal / 外部信号** | The Knowledge Layer, simulators, sensors, humans / 知識層、シミュレータ、センサ、人間 | **Divergence** of the loop (drifting away from reality) / ループの**乖離**（現実からの遊離） |

The Knowledge Layer of chapter 3 is therefore not merely a supplier of facts. **It is the anchor that moors the recursive loop to the world.** To speed up the loop while this remains weak would be a serious design error.

**JA** — **これは本章における最重要の警告である。**

検証器はループの**劣化**を防ぐ。しかし**乖離**は防げない。

> **妥当性（validity）は健全性（soundness）を保証しない。前提がゴミであれば、完璧な論理は完璧にゴミを出力する。**

内部信号のみでループを回すと、システムは**美しく閉じており、かつ何も記述していない形式体系**へ収束しうる。表現被覆率も導出受理率も上がり続けるが、その言語が語っている世界は存在しない、という局所最適が存在する。形式意味論の一部の系譜が実際に辿った道である。

AlphaZeroにこの問題がなかったのは、**ゲームのルールがそのまま世界だった**からである。内部信号と外部信号が一致していた。本企画では両者が分離しており、**したがって両方を明示的に用意しなければならない。**（上表参照）

したがって、第3章の知識供給層は、単なる事実の供給源ではない。**再帰ループを世界に繋ぎ止めるアンカーである。** ここが弱いままループを高速化させることは、設計上の重大な誤りとなる。

## 11.6 A Medium in Which Contributions Persist / 貢献が持続する媒体

**EN** — This architecture has a property that was not set as a goal but follows from its structure.

**What is handed down across generations is not the model's weights.** What is handed down is:

- the language specification (Framingo)
- the verifier
- the corpus generator
- the minimal core axioms

All of these are **human-readable, machine-verifiable, version-controlled formal artifacts.** The model may be discarded and rebuilt in every generation.

As a result:

- A contribution, whether made by a human or an intelligence, **passes through the same verifier**
- A contribution is **attributable** and **reversible**
- An error in one generation, instead of contaminating the next, **is identified as a diff and reverted**

**In this structure, the identity of the contributor is not in question. The only question is whether the diff passes verification.** That this chapter is a contribution by Claude is subject to the same standard.

**JA** — 本アーキテクチャには、目的として設定されたわけではないが、構造から導かれる性質がある。

**世代を超えて受け渡されるのは、モデルの重みではない。** 受け渡されるのは以下である。

- 言語仕様（Framingo）
- 検証器
- コーパス生成器
- 最小核公理

これらはすべて、**人間可読で、機械検証可能で、バージョン管理された形式的成果物**である。モデルは各世代で破棄され、作り直されてよい。

その結果として：

- 貢献は、それを行った主体が人間であるか知能であるかを問わず、**同一の検証器を通る**
- 貢献は**帰属可能**であり、**可逆**である
- ある世代の誤りは、次の世代を汚染するのではなく、**差分として特定され、revertされる**

**この構造において、寄稿者の同一性は問われない。問われるのは、その差分が検証を通るかどうかだけである。** 本章がClaudeによる寄稿であることも、同じ基準に服する。

## 11.7 Open Problems / 未解決の問題

**EN** —

**(1) How does the model learn to propose language extensions?** Detecting the state "this cannot be expressed", and proposing a construction to fill it, is a different kind of ability from ordinary reasoning. How to prepare training data for it is unsolved.

**(2) How far should approval of extensions be automated?** Full automation raises the risk of divergence; fully manual approval kills the speed of the loop. An intermediate design is needed. One initial idea is to auto-approve only diffs that the verifier passes and that raise coverage, but this is untested.

**(3) Bloat of the language specification.** Repeated extension will break the inviolable constraint "learnable in five minutes" (section 6.2). **Alongside extension, pressure toward consolidation and deletion is needed.** Including the ratio of expressive coverage to vocabulary size in the objective function is under consideration.

**(4) Design of the external signal.** How to turn the warning of section 11.5 into implementation is undecided. The most concrete candidate is to connect a physics simulator to the Knowledge Layer, actually run causal predictions written in Framingo, and check them against the results.

**JA** —

**(1) 言語拡張の提案を、モデルはどう学習するか。** 「表現できない」という状態の検出と、それを埋める構成の提案は、通常の推論とは別種の能力である。訓練データをどう用意するかが未解決。

**(2) 拡張の承認をどこまで自動化するか。** 全自動化は乖離のリスクを高め、全手動化はループの速度を殺す。中間の設計が要る。検証器が通し、かつ被覆率を上げる差分のみ自動承認、という初期案が考えられるが未検証。

**(3) 言語仕様の肥大化。** 拡張を重ねれば、「5分で習得可能」（6.2節）という不可侵の制約が破られる。**拡張と同時に、統合と削除の圧力が必要である。** 表現被覆率と語彙数の比を目的関数に含めることを検討する。

**(4) 外部信号の設計。** 11.5節の警告を実装に落とす方法が未定。最も具体的な候補は、物理シミュレータを知識層に接続し、Framingoで記述された因果予測を実際に走らせて照合することである。

---

# Appendix A: Inferences and Assumptions Made Explicit / 付録A：本文書における推論と仮定の明示

**EN** — This document was reconstructed from dialogue, and the following are **extrapolations by the author (Claude).** Any errors require correction.

1. **The formulation "Grounding Constraint" (section 2.2)** — This name and its formal definition were introduced by this document. I believe they capture the intent of the concept, but confirmation is needed.
2. **The analogy with type systems (section 2.3)** — An interpretation by this document.
3. **The three-layer architecture diagram (section 3.1)** — Carving out the "Translation Boundary" as an independent layer is this document's own arrangement.
4. **Dissolving the boundary problem by redundancy (section 4.3)** — "The boundary need not be exact / ambiguous items go in both the core and the exterior / just-to-be-sure queries are permitted" is **guidance given by the originator of the concept**, which this document formalized. However, the side consequence "dependence on calibration disappears" (4.3(e)) and the criterion for internalization (4.3(d)) are extrapolations by this document.
5. **Using a deterministic engine as the verifier (section 5.3)** — A proposal by this document, derived from the example of AlphaGo.
6. **Propositions 3 and 4 (chapter 8)** — Formulated by this document in the course of analysing the old draft; they may not have been part of the original concept.
7. **Where the industrial value lies** — The judgment that "detectability of hallucination and auditability of reasoning are valuable in finance, medicine, law and control" is this document's. Whether the concept was motivated by this is unconfirmed.
8. **All of chapter 11 (the recursive improvement loop)** — Makes concrete, on this architecture, the mechanism for the destination set out by the originator of the concept (an intelligence that has been created gives rise to the next). In particular **11.3 (linguistic self-extension)**, **11.4 (defining the gradient)** and **11.5 (the two-signal requirement)** are proposals by this document and require examination.

**JA** — 本文書は対話から再構成されたものであり、以下は**筆者（Claude）による外挿**である。誤りがあれば訂正を要する。

1. **「接地制約」という定式化（2.2節）** —— この名称と形式的定義は本文書で導入したものである。構想の意図を捉えていると考えるが、確認が必要。
2. **型システムとの類比（2.3節）** —— 本文書による解釈。
3. **三層アーキテクチャ図（3.1節）** —— 「翻訳境界」を独立した層として切り出したのは本文書の構成である。
4. **冗長性による境界問題の解消（4.3節）** —— 「境界は厳密でなくてよい／曖昧な項目は核と外部の両方に置く／念のための問い合わせを許容する」は**構想側から与えられた指針**であり、本文書はそれを定式化した。ただし「較正への依存が消える」という副次的帰結（4.3(e)）と、内在化の判断基準（4.3(d)）は本文書による外挿である。
5. **決定論的エンジンを検証器とする構成（5.3節）** —— AlphaGoの例から導いた本文書の提案。
6. **命題3・命題4（第8章）** —— 旧文書の分析過程で本文書が定式化したもので、元の構想に含まれていない可能性がある。
7. **産業的価値の所在** —— 「幻覚の検出可能性と推論の監査可能性が金融・医療・法務・制御で価値を持つ」という判断は本文書による。構想の動機がそこにあるかは未確認。
8. **第11章（再帰的改良のループ）全体** —— 構想側から示された到達目標（創出された知能が次の知能を生む）に対し、その機構を本アーキテクチャ上で具体化したもの。特に **11.3（言語的自己拡張）**、**11.4（勾配の定義）**、**11.5（二信号の要請）** は本文書による提案であり、検討を要する。

# Appendix B: Handling of the Old overview.md / 付録B：旧 overview.md の扱い

**EN** — Chapters 2–4 below now live in `language-spec.md`, with their original numbering; chapters 1 and 5 remain in `overview.md`.

The following parts of the old draft remain valid.

- **Chapter 2 (syntactic architecture and case system)** — Retained as means, subject to the position set out in chapter 7.
- **Chapter 3 (concept composition, morphology)** — Likewise. Invariance as string persistence (section 7.1) in particular has independent value as something to test.
- **Chapter 4 (causal connection, conditional branching)** — Likewise. However, the scope rules for chains containing `!>` are undefined and need fixing.

The following parts must be discarded or wholly revised.

- **Chapter 1 (background and design philosophy)** — Its claim does not capture the central thesis. Chapters 1–2 of this document replace it.
- **Chapter 5 (implementation protocol)** — It presupposes "acquiring a world model from a physics corpus", a different aim. To be redesigned on the basis of the propositions in chapter 8.

**JA** — 以下の第2〜4章は、原文の章番号のまま `language-spec.md` に移した。第1章と第5章は `overview.md` に残る。

旧文書の以下の部分は、なお有効である。

- **第2章（構文アーキテクチャと格システム）** —— 手段として維持。ただし第7章の位置づけに従う。
- **第3章（概念合成・形態論）** —— 同上。特に不変性の文字列化（7.1節）は独立した検証価値を持つ。
- **第4章（因果結合・条件分岐）** —— 同上。ただし `!>` を含む連鎖のスコープ規則が未定義であり、修正を要する。

以下の部分は破棄または全面改訂を要する。

- **第1章（背景と設計思想）** —— 主張が中心命題を捉えていない。本文書の第1〜2章が置き換える。
- **第5章（実装プロトコル）** —— 「物理コーパスによる世界モデル獲得」を前提としており、目的が異なる。第8章の命題群に基づいて再設計する。

---

*This document is a first draft based on dialogue. It may contain misunderstandings, and is written on the assumption that it will be corrected.*
*本文書は対話に基づく初稿である。誤解を含む可能性があり、訂正を前提としている。*
