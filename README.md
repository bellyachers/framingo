# The Teniwoha Project

```
The Teniwoha Project     てにをは計画          the undertaking
  └─ Teniwoha            てにをは              the language (lineage)
       └─ Gisaburo       ギサブロー            v1 specification
```

> **English is fine as vocabulary. It has no てにをは. This language supplies it.**
> **英語は語彙としては申し分ない。だが「てにをは」がない。この言語がそれを埋める。**

**A designed formal language for models that separate logic from knowledge — so that hallucination becomes *mechanically detectable*, not merely less frequent.**

**知識と論理を分離したモデルのための形式言語。幻覚を「減らす」のではなく、「機械的に検出可能にする」。**

> **Status / 状態** — Design charter. No implementation yet. Contributions and criticism welcome.
> 設計憲章の段階。実装はまだない。批判・貢献を歓迎する。

---

## The Claim / 主張

**EN** — Current large language models fuse *knowledge* and *logic* into a single parameter space. The fact "Paris is the capital of France" and the rule "if A→B and B→C then A→C" live in the same weights, indistinguishably. That fusion is the single cause of three pathologies:

1. **Size.** Most parameters are spent memorizing the internet, not reasoning.
2. **Undetectable hallucination.** A fabricated fact and a correct one are structurally identical at the surface — both fluent, both from the same stochastic process. Nothing outside the model can tell them apart.
3. **Unauditable reasoning.** A natural-language chain of thought may be post-hoc confabulation. There is no guarantee it corresponds to the computation that produced the answer.

Teniwoha dissolves the fusion:

> **The model learns logic only. It holds no factual knowledge.**
> **Knowledge is retrieved at inference time via function calling and placed in context.**
> **The medium connecting them is a designed formal language with no ambiguity.**

**JA** — 現行の大規模言語モデルは、**知識**と**論理**を同一のパラメータ空間に融解させている。「パリはフランスの首都である」という事実と、「A→B かつ B→C ならば A→C」という推論規則が、同じ重みの中に区別なく同居している。この融合が、三つの病理すべての単一の原因である。

1. **巨大化。** パラメータの大部分は推論ではなくインターネットの記憶に費やされている。
2. **幻覚の検出不能性。** 捏造された事実と正しい事実は、表層において構造的に同一である。どちらも流暢で、同じ確率過程から生成される。モデルの外側からは判別できない。
3. **監査不能性。** 自然言語のChain-of-Thoughtは事後的な作話でありうる。実際の計算経路と一致している保証はない。

Teniwohaはこの融合を解体する。

> **モデルには論理だけを学習させる。事実知識は一切持たせない。**
> **知識は推論時にFunction Callingで取得し、コンテクストに載せる。**
> **両者を繋ぐ媒体は、曖昧性を持たない設計された形式言語である。**

---

## The Grounding Constraint / 接地制約

**EN** — This is the technical core. Because the medium is formal, the following can be enforced *syntactically*:

> Every entity, predicate and relation appearing in the model's output must derive from one of:
> **(a)** the minimal core axioms embedded in the model,
> **(b)** knowledge currently present in context, or
> **(c)** a proposition derived from those by an explicit inference rule.
>
> **A token traceable to none of these is, by definition, a hallucination — and is detectable by string matching.**

In natural language this constraint cannot be written down, because deciding "derives from context" itself requires understanding. In Teniwoha, entities appear as normalized identifiers, so the check reduces to set operations.

This is the same kind of invention as a **type system**. A type system does not make programmers smarter or programs correct. It makes one class of error mechanically detectable before it propagates. That alone changed software reliability. Teniwoha aims for the same: not fewer hallucinations, but hallucination as an *identifiable event*.

**JA** — これが技術的中核である。媒体が形式的であるため、以下を**構文レベルで**強制できる。

> モデルの出力に現れるすべての実体・述語・関係は、次のいずれかに由来しなければならない。
> **(a)** モデル内に埋め込まれた最小核公理
> **(b)** その時点でコンテクストに載っている知識
> **(c)** 上の二つから明示された推論規則によって導出された命題
>
> **いずれにも由来しないトークンの出現は、定義により幻覚であり、文字列照合によって検出できる。**

自然言語ではこの制約は書き下せない。「文脈に由来する」の判定自体が意味理解を要求するからである。Teniwohaでは実体が正規化された識別子として現れるため、由来判定が集合演算に還元される。

これは**型システム**と同じ種類の発明である。型システムはプログラマを賢くしないし、プログラムを正しくもしない。ある種類の誤りを、伝播する前に機械的に検出可能にするだけである。それだけでソフトウェアの信頼性は質的に変わった。Teniwohaが目指すのも同じ——幻覚を減らすのではなく、**幻覚を識別可能な事象にする。**

---

## Architecture / アーキテクチャ

```
             Natural language world (humans, documents, web)
                                 │
        ┌────────────────────────┴─────────────────────────┐
        │   Translation Boundary        翻訳境界            │  ← hallucination is localized here
        │   NL ⇄ Teniwoha                                   │  ← inspect only this surface
        └────────────────────────┬─────────────────────────┘
                                 │  Teniwoha
        ┌────────────────────────┴─────────────────────────┐
        │   Logic Core                  論理コア            │  ← holds no knowledge
        │   · small transformer, logic only                 │  ← never saw natural language
        │   · minimal core axioms only                      │
        │   · emits only under the Grounding Constraint     │
        └────────────────────────┬─────────────────────────┘
                                 │  function call (a Teniwoha query)
        ┌────────────────────────┴─────────────────────────┐
        │   Knowledge Layer             知識供給層          │
        │   · retrieval / DB / API / sensors / simulators   │
        │   · returns results normalized into Teniwoha      │
        └──────────────────────────────────────────────────┘
```

**EN** — Note what this does *not* claim. Hallucination is not eliminated; it is **localized**. It can still enter at the translation boundary. But where current architectures diffuse it through the entire reasoning process, here it is confined to a single, explicit, auditable interface — whose output is Teniwoha, and therefore checkable.

**JA** — この設計は幻覚をゼロにしない。**局在化する。** 翻訳境界には依然として幻覚が入りうる。しかし現行アーキテクチャが推論の全過程に幻覚を拡散させるのに対し、ここではそれが単一の、明示された、監査可能なインターフェースに閉じ込められる。そしてその出力はTeniwohaなので、検証器にかけられる。

---

## What Has No Precedent / 前例が確認できないもの

**EN** — Most components have prior art (neo-Davidsonian semantics, AMR, Schank's Conceptual Dependency, STRIPS/PDDL, RAG, neurosymbolic AI). The following, to our knowledge, do not:

- **Training a model whose native and only medium is a designed formal language, having never seen natural language.** Existing formal-native models (theorem provers, code models) are almost always initialized from NL-pretrained weights.
- **Deliberately withholding factual knowledge from the model.** The argument that "an LLM should be a reasoning engine, not a knowledge base" has been *made* many times; a model actually built without knowledge has not.
- **Syntactic detection of hallucination via a grounding constraint.** Countless efforts *reduce* hallucination; none convert it into a mechanically identifiable event.
- **The human crossing over to the formal side.** For half a century the arrangement has been fixed: formal language on the machine side, natural language on the human side — even SHRDLU (1972) conversed in English about a fully formal blocks world.
- **The combination of the four.**

**JA** — 個々の構成要素にはほぼ先行研究がある（ネオ・デイヴィドソン流意味論、AMR、Schankの概念依存理論、STRIPS/PDDL、RAG、ニューロシンボリックAI）。以下については、我々の知る限り前例がない。

- **自然言語を一度も見せず、設計された形式言語をネイティブかつ唯一の媒体として訓練すること。** 既存の形式言語ネイティブモデル（証明支援、コード生成）は、ほぼ全て自然言語事前学習済みモデルからの初期化である。
- **モデルから事実知識を意図的に排除する設計。** 「LLMは知識ベースではなく推論エンジンであるべきだ」という**主張**は繰り返しなされてきたが、実際に知識を持たないモデルを構築した例はない。
- **接地制約による幻覚の構文的検出。** 幻覚を**減らす**取り組みは無数にあるが、それを機械的に識別可能な事象へ**転換する**アーキテクチャはない。
- **人間が形式言語の側へ渡ること。** 半世紀にわたり配置は固定されてきた——形式言語は常に機械側、自然言語は常に人間側。SHRDLU（1972）でさえ、完全に形式的なブロック世界を英語で語っていた。
- **上記四点の組み合わせ。**

---

## Two Design Decisions Worth Naming / 特筆すべき二つの設計判断

### Redundancy dissolves the boundary problem / 冗長性による境界問題の解消

**EN** — "Do humans die?" — is that logic or knowledge? CYC spent forty years failing to fix this boundary. **Teniwoha does not need to fix it.** The minimal core and the external knowledge base are permitted to **overlap**. If the model asks *just in case* whether humans die, the knowledge base should answer that they do.

CYC collapsed because its hand-written core was the *only* source, so it had to be complete, and completeness was unreachable. Here the two are redundant: a gap in the core is caught by retrieval, a gap in retrieval is caught by the core. The only real failure is absence from both — **which is a coverage problem, not a definitional one.** Coverage can be measured and improved. Definitions could not.

A side effect: **the model no longer needs calibration.** Knowing whether you know is a famously unsolved problem. Here it is unnecessary — when in doubt, just ask.

**JA** — 「人は死ぬ」は論理か知識か。CYCは40年かけてこの境界を確定しようとし、失敗した。**Teniwohaは確定する必要がない。** 最小核と外部知識ベースは**重複してよい。** モデルが念のため「人は死ぬか」と問い合わせたら、知識ベースは「人は死ぬ」と答えるべきである。

CYCが崩壊したのは、手書きの核が**唯一の**知識源であり、ゆえに完全でなければならず、完全性が達成不可能だったからである。ここでは両者が冗長化されている。核の抜けは検索が拾い、検索の抜けは核が持つ。真の欠落は「両方に無い」場合だけで、**これは定義の問題ではなく網羅性の問題である。** 網羅性は測定でき、改善できる。定義はできなかった。

副次的な帰結：**モデルは較正（calibration）を必要としなくなる。** 自分が知っているかを知ることは未解決の難問だが、ここでは不要である。疑わしければ常に問い合わせればよい。

### The verifier, not the formal language, is load-bearing / 中心にあるのは形式言語ではなく検証器

**EN** — AlphaZero, Lean/Coq provers, Othello-GPT — every lineage that built intelligence out of symbol streams no human converses in shares one thing: **a machine-decidable verifier.** AlphaZero surpassed humans not because it played itself, but because win/loss was decidable without appeal to the model's own opinion. Being formal is a *precondition* for having a verifier, not the thing itself.

And here is the asymmetry that makes this project work: **the correctness of knowledge cannot be machine-verified, but logical validity can.** Because the two are separated, the training corpus for the logic core can be generated *and verified* deterministically — with zero contamination from LLM hallucination. The LLM is the proposer; a deterministic engine is the verifier.

**JA** — AlphaZero、Lean/Coqの証明モデル、Othello-GPT——人間が話さない記号列から知能を立ち上げた系譜には、例外なく**機械判定可能な検証器**がある。AlphaZeroが人類を超えたのは自己対戦したからではなく、勝敗がモデルの意見に依らず決定できたからである。形式的であることは検証器を持つための**前提条件**であって、それ自体ではない。

そしてここに、本企画を成立させる非対称性がある。**知識の正しさは機械検証できないが、論理的妥当性はできる。** 両者が分離されているため、論理コアの訓練コーパスは決定論的に生成でき、決定論的に検証できる——LLM由来の汚染ゼロで。LLMは提案者、決定論的エンジンが検証者である。

---

## Falsifiable Claims / 反証可能な主張

| # | Claim / 主張 | Falsified if / 反証条件 |
|---|---|---|
| 1 | **Parameter efficiency** — logic-only models reach comparable reasoning with orders of magnitude fewer parameters / 論理のみのモデルは数桁少ないパラメータで同等の推論能力に達する | Logical ability turns out to depend strongly on knowledge scale / 論理能力が知識量に強く依存する場合 |
| 2 | **Detection** — hallucination detection under the grounding constraint reaches practical rates (≥99%) / 接地制約下で幻覚検出率が実用水準に達する | The model routinely evades the constraint by miscombining known tokens / 既知トークンの誤結合で制約を回避する場合 |
| 3 | **Format matters** — holding meaning fixed, role-tagged flat form generalizes compositionally better than word-order form / 意味を固定したとき、役割タグ付きフラット形式は語順依存形式より高い組成的汎化を示す | No difference. Then format is irrelevant and only the generator matters — also an important result / 差が出ない場合。形式ではなく生成器がすべてという結論になり、これも重要な知見 |
| 4 | **Invariance transfers** — a model trained on conservation-as-string-persistence generalizes to invariants never encoded that way / 文字列永続性として教えた保存則が、そう教えなかった不変量にも汎化する | It does not. Then the model learned copying, not invariance — and a central assumption falls / 汎化しない場合。モデルは不変性ではなくコピーを学習しており、中心的仮定が反証される |
| 5 | **Conversation** — a human and a small model that has never seen natural language hold a multi-turn exchange entirely in Teniwoha / 自然言語を見たことのない小規模モデルと人間が、Teniwohaのみで多ターンの対話を成立させる | — *(no precedent exists / 前例のない到達点)* |

---

## On Languages / 言語について

**EN** — This repository is bilingual, and that is not a courtesy. It is part of the argument.

Teniwoha's **vocabulary is English**; its **grammar is Japanese**. The case-marking argument is set out under [The Name](#the-name--名前について) above; what follows is why *this repository* is bilingual.

The three properties the charter names as central are ordinary daily operations in Japanese:

- **Order invariance** — Japanese permits scrambling. 「ジョンがナイフでパンを切った」「パンをジョンがナイフで切った」 are both grammatical and identical in meaning. English cannot do this.
- **Argument dropping** — 「パンを切った」 is complete and natural. The charter's "gradient of abstraction" needs no explanation to a Japanese speaker; an English speaker needs the passive voice to approximate it.
- **Separable case marking** — Japanese case particles attach to nouns without fusing, unlike Latin or Russian case endings. `:` is functionally a 格助詞.

So the project combines **the global reach of English vocabulary with the logical regularity of Japanese structure.** Describing an English-lexified formal language *in English* makes it impossible to tell which intuitions come from the design and which leak in from English. Writing in Japanese forces that boundary to be explicit — you cannot explain `agt:` by saying "well, it's the subject."

The Japanese text is the primary source. The English is the door.

**JA** — 本リポジトリは英日併記だが、これは配慮ではなく**主張の一部**である。

Teniwohaは、**語彙は英語だが、文法は日本語である。** 格標示についての議論は上の[名前について](#the-name--名前について)に置いた。ここで述べるのは、**このリポジトリが**英日併記である理由である。

憲章が中核的特徴として掲げる三つの性質は、日本語では日常の運用にすぎない。

- **順序不変性** — 日本語はスクランブリングを許す。「ジョンがナイフでパンを切った」と「パンをジョンがナイフで切った」は両方文法的で同義。英語では不可能。
- **項の脱落** — 「パンを切った」で完結し自然。憲章の「抽象度のグラデーション」は日本語話者には説明を要しない。英語話者は受動態で近似するしかない。
- **格の分離可能性** — 日本語の格助詞は名詞に融合せず後接する。ラテン語やロシア語の格語尾とは違う。`:` は機能的に格助詞である。

すなわち本企画は、**英語語彙の世界的普遍性と、日本語構造の論理性を組み合わせる。** 英語語彙の形式言語を英語で語ると、どの直感が設計由来でどの直感が英語からの漏れ込みかを切り分けられない。日本語で書けば境界が強制的に明示化される——`agt:` を「主語だよね」で済ませられない。

日本語テキストが正本である。英語は扉である。

---

## The Name / 名前について

**EN** — **English is fine as vocabulary. It has no てにをは. This language supplies it.**

てにをは (*teniwoha*) is the classical Japanese term for the particles that mark grammatical relations — を, に, で, から, が, は. The word comes from the ヲコト点, marks placed at the corners of Chinese characters so that a Japanese reader could recover which particle belonged where; read the corners in order and you get て・に・を・は. **From the start it is the name of a technique for supplying Japanese case marking to a foreign vocabulary.** That is exactly what this language does.

### The precise claim

English is not without role marking — it has prepositions. But prepositions mark only the periphery.

| role | Japanese | English |
|---|---|---|
| `tool:` | **で** | *with* (polysemous) |
| `src:` | **から** | *from* (polysemous) |
| `dst:` | **へ / に** | *to / into / onto* (split) |
| `loc:` | **で / に** | *in / on / at* (split) |
| **`agt:`** | **が** | **unmarked — position only** |
| **`tgt:`** | **を** | **unmarked — position only** |

**The two most important arguments carry no marker at all.** Old English inflected for nominative, accusative, genitive and dative; modern English kept case only in the pronouns (*he/him*) and the genitive clitic. When the inflections went, the means of marking core arguments went with them — and word order had to take over the load.

**This is why English has a passive voice.** In Japanese you change one particle — パンを切った / パンが切られた — and nothing else need move. In English you must relocate the noun, restructure the verb, and demote the agent into a *by*-phrase. **The passive is the detour a language needs when it has no を.** The charter calls this the "viewpoint-dependent syntactic twist" that forces a model to spend its attention on surface parsing. The twist is not a stylistic accident; it is the mechanical consequence of a missing marker.

The design follows in one line: **the vocabulary was never the problem. Keep it. Replace the role marking.**

### The name states the failure condition

The Japanese idiom 「てにをはが合わない」 — *the teniwoha do not match* — is what you say when a piece of writing does not hold together, when the connections fail. **That is precisely what the verifier checks.** A well-formed statement in this language is one whose teniwoha match.

### Spelling

Romanized **Teniwoha** throughout: the form a Japanese writer's hands produce (the IME takes `wo`), and phonotactically even — CV.CV.CV.CV, where *tenioha* leaves a bare vowel in hiatus. Also written *tenioha*; the kana is てにをは.

---

**JA** — **英語は語彙としては申し分ない。だが「てにをは」がない。この言語がそれを埋める。**

「てにをは」は、文法関係を標示する助詞——を・に・で・から・が・は——を指す古典的な呼称である。語源はヲコト点、すなわち漢字の四隅に打たれた符号で、どの助詞をそこに補うかを日本語の読み手に示すものだった。四隅を順に読むと「て・に・を・は」になる。**すなわちこの語は、はじめから「外国語の語彙に日本語の格標示を補う技術」の名である。** 本言語がやっているのは、まさにそれである。

### 主張の精密な形

英語に役割標示がないわけではない。前置詞がある。**しかし前置詞は周辺項しか標示しない。**

| 役割 | 日本語 | 英語 |
|---|---|---|
| `tool:` | **で** | *with*（多義） |
| `src:` | **から** | *from*（多義） |
| `dst:` | **へ / に** | *to / into / onto*（分裂） |
| `loc:` | **で / に** | *in / on / at*（分裂） |
| **`agt:`** | **が** | **標示なし。位置のみ** |
| **`tgt:`** | **を** | **標示なし。位置のみ** |

**最も重要な二つの項に、印が一切ない。** 古英語は主格・対格・属格・与格に屈折したが、現代英語が保持した格は代名詞（*he/him*）と属格の `'s` だけである。屈折が失われたとき、**中核項を標示する手段もろとも失われ**、その負荷を語順が引き受けることになった。

**だから英語には受動態がある。** 日本語は助詞を一つ替えればよい——「パンを切った」「パンが切られた」——他は何も動かす必要がない。英語は名詞を移動させ、動詞を組み替え、動作主を *by* 句へ降格させねばならない。**受動態とは、「を」を持たない言語が必要とする迂回路である。** 憲章はこれを「視点に依存した統語的ねじれ」と呼び、モデルに表層解析の負荷を強いる元凶とした。**このねじれは文体上の偶然ではなく、印の欠落がもたらす力学的な帰結である。**

設計は一行で従う。**問題は語彙ではなかった。語彙は保つ。役割標示だけを差し替える。**

### 名前が、不合格条件を述べている

**「てにをはが合わない」**——文章の繋がりが成立していないとき、日本語話者はこう言う。**これは検証器が判定するものそのものである。** この言語における整形式の文とは、てにをはが合っている文である。

### 綴り

本文では **Teniwoha** で統一する。日本語話者の手が自然に打つ形であり（IME入力が `wo`）、音韻的にも CV.CV.CV.CV で均質である（*tenioha* は裸母音が一つ挟まる）。*tenioha* とも綴られる。仮名は「てにをは」。

---

## Gisaburo — the first specification / 最初の仕様

**EN** — Named for **Kiyose Gisaburō Norikura** (清瀬義三郎則府, 1931–2017), Altaic linguist (Jurchen, Manchu, Old Korean; Indiana, then Hawaii), who built a derivational grammar on a single thesis: **Japanese verbs do not conjugate.** They agglutinate — morphemes attach without fusing, and nothing about the stem changes.

The v1 specification makes the same commitment by design. Verbs never inflect; tense, aspect and modality become separable slots rather than stem mutations; suffixes attach regularly. **What Kiyose argued descriptively about Japanese, Gisaburo implements.**

**JA** — **清瀬義三郎則府**（1931–2017）に由来する。アルタイ言語学者（女真語・満洲語・古代朝鮮語。インディアナ大学を経てハワイ大学）であり、**「日本語の動詞は活用しない」**という一つの主張のうえに派生文法を築いた。動詞は膠着する——形態素は融合せずに接合し、語幹は何も変化しない。

v1 仕様は同じ立場を設計として採る。動詞は決して屈折せず、時制・相・法は語幹の変異ではなく分離可能なスロットになり、接尾辞は規則的に接合する。**清瀬が日本語について記述的に論じたことを、Gisaburo は実装する。**

---

## Charles J. Fillmore (1929–2014)

**EN** — Not a namesake, but the origin of the undertaking.

"The Case for Case" (1968) proposed deep cases as universal semantic roles. Frame semantics followed. He spent the last seventeen years of his life building **FrameNet**, a machine-readable inventory of frames and their elements, and died with it unfinished.

FrameNet's limit was that it *annotated* English. The frames were a target representation predicted *from* natural language, because nothing in his era could make them the medium itself. **This project inverts that: the frames are the primary medium, and natural language never enters the loop.** It attempts what Fillmore was reaching for, with tools he did not have.

He and Kiyose were near-contemporaries, an ocean apart, and as far as we know never met. One worked on case, the other on agglutination — **the two halves of the same object.** This language is built on both. Fillmore's name stays on the roster; some future specification will earn it.

**JA** — 名の由来ではない。企画の出発点である。

「The Case for Case」(1968) は深層格を普遍的意味役割として提案した。フレーム意味論がそれに続いた。彼は生涯最後の17年を **FrameNet**——フレームと格要素の機械可読な目録——の構築に費やし、未完のまま没した。

FrameNet の限界は、それが英語への**注釈**だったことである。フレームは自然言語から予測される目標表現にすぎなかった。当時、それ自体を媒体にする方法がなかったからである。**本企画はそれを反転させる。フレームが一次媒体であり、自然言語はループに入らない。** Fillmore が手を伸ばしていたものを、彼が持たなかった道具で試みる。

彼と清瀬はほぼ同時代人であり、大洋を隔てて、我々の知る限り会うことはなかった。一方は格を、他方は膠着を研究した——**同じ対象の二つの半分である。** 本言語はその両方の上に建っている。Fillmore の名は名簿に残る。いずれかの世代が、それを得るだろう。

### Version naming / バージョン命名

**EN** — Chapter 11 of the charter expects the language to be extended and revised by successive generations. The project name is therefore permanent, and each specification is codenamed:

> **Each version is named for a linguist whose thesis that version embodies.**

`v1 = Gisaburo` — verbs do not conjugate. The full roster is kept in [`docs/version-names.md`](docs/version-names.md), organized by what a version would have to do to earn each name.

**JA** — 憲章第11章は、言語が世代を重ねて拡張・改訂されることを前提とする。したがって企画名は恒久とし、各仕様がコードネームを持つ。

> **各バージョンは、その世代が体現する主張を論じた言語学者の名を冠する。**

`v1 = Gisaburo` ── 動詞は活用しない。名簿の全体は [`docs/version-names.md`](docs/version-names.md) に置く。**その名を得るために各世代が何をしなければならないか**で整理してある。

---

## Documents / 文書

| File | Contents |
|---|---|
| [`docs/core-thesis.md`](docs/core-thesis.md) | **Design charter (current).** The central claim, architecture, verifier, recursive loop, falsifiable propositions. / **設計憲章（現行）。** 中心命題、アーキテクチャ、検証器、再帰ループ、反証可能な命題 |
| [`docs/version-names.md`](docs/version-names.md) | **Version codename roster.** Linguists whose theses future specifications could embody, and the rule for assigning them. / **バージョン・コードネーム名簿。** 各世代が体現しうる主張と、その割り当て規則 |
| [`docs/overview.md`](docs/overview.md) | Original 5-chapter draft. Ch. 2–4 (language specification) remain valid as *means*; ch. 1 and 5 are superseded by `core-thesis.md`. / 初期草稿。第2〜4章（言語仕様）は手段として有効。第1・5章は `core-thesis.md` が置き換える |

---

## Open Problems / 未解決の問題

1. **Coverage of the minimal core** — the boundary need not be exact, but "absent from both core and retrieval" remains a real gap. / 最小核の網羅性——境界の確定は不要になったが、「核にも外部にも無い」は残る
2. **Design of the translation boundary** — the only place hallucination can enter. / 翻訳境界の設計——幻覚が入りうる唯一の場所
3. **Can logic be learned without knowledge?** Open, and this project effectively tests it. / 知識なしに論理は学べるか——開いた問い
4. **Query bootstrapping** — knowing *what to ask for* may itself require knowledge. / クエリ発行のブートストラップ
5. **No dialogue layer yet** — no speaker/hearer, no speech acts, no cross-turn anaphora. / 対話層が存在しない
6. **The verifier is unimplemented** — and every claim above depends on it. / 検証器が未実装——上記のすべてがこれに依存している

---

## Contributing / 貢献について

**EN** — What is passed between generations of this project is not model weights. It is the language specification, the verifier, the corpus generator, and the minimal core — all human-readable, machine-checkable, version-controlled artifacts.

Contributions are therefore judged the same way regardless of whether a human or a machine wrote them: **does the diff pass the verifier?** Chapter 11 of the charter was written by Claude (Opus 5) and is marked as such. It is subject to the same standard.

**JA** — 本企画で世代を超えて受け渡されるのはモデルの重みではない。言語仕様、検証器、コーパス生成器、最小核——すべて人間可読で、機械検証可能で、バージョン管理された成果物である。

したがって貢献は、それを書いたのが人間か機械かを問わず同じ基準で判定される。**その差分は検証器を通るか。** 憲章第11章はClaude（Opus 5）が執筆し、その旨が明記されている。同じ基準に服する。

---

## License / ライセンス

Documentation and specification: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
Code, when it exists, will be Apache 2.0.

文書および仕様：CC BY 4.0。コードは、存在するようになった時点で Apache 2.0。

A specification under a copyleft license does not get adopted. That would defeat the purpose.
コピーレフトの仕様は採用されない。それでは目的に反する。
