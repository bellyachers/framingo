# The Framingo Project

```
The Framingo Project     フレーミンゴ計画      the undertaking
  └─ Framingo            フレーミンゴ          the language
       └─ Gisaburo       ギサブロー            v1 specification
```

> **English is fine as vocabulary. It has no てにをは. This language supplies it.**
> **英語は語彙としては申し分ない。だが「てにをは」がない。この言語がそれを埋める。**


**A designed formal language for models that separate logic from knowledge — so that hallucination becomes *mechanically detectable*, not merely less frequent.**

**知識と論理を分離したモデルのための形式言語。幻覚を「減らす」のではなく、「機械的に検出可能にする」。**

> **Status / 状態** — Design charter, with implementation just begun: a parser for the v1 specification. Contributions and criticism welcome.
> 設計憲章の段階。実装は着手したばかりで、v1 仕様のパーサがある。批判・貢献を歓迎する。

---

## The Claim / 主張

**EN** — Current large language models fuse *knowledge* and *logic* into a single parameter space. The fact "Paris is the capital of France" and the rule "if A→B and B→C then A→C" live in the same weights, indistinguishably. That fusion is the single cause of three pathologies:

1. **Size.** Most parameters are spent memorizing the internet, not reasoning.
2. **Undetectable hallucination.** A fabricated fact and a correct one are structurally identical at the surface — both fluent, both from the same stochastic process. Nothing outside the model can tell them apart.
3. **Unauditable reasoning.** A natural-language chain of thought may be post-hoc confabulation. There is no guarantee it corresponds to the computation that produced the answer.

Framingo dissolves the fusion:

> **The model learns logic only. It holds no factual knowledge.**
> **Knowledge is retrieved at inference time via function calling and placed in context.**
> **The medium connecting them is a designed formal language with no ambiguity.**

**JA** — 現行の大規模言語モデルは、**知識**と**論理**を同一のパラメータ空間に融解させている。「パリはフランスの首都である」という事実と、「A→B かつ B→C ならば A→C」という推論規則が、同じ重みの中に区別なく同居している。この融合が、三つの病理すべての単一の原因である。

1. **巨大化。** パラメータの大部分は推論ではなくインターネットの記憶に費やされている。
2. **幻覚の検出不能性。** 捏造された事実と正しい事実は、表層において構造的に同一である。どちらも流暢で、同じ確率過程から生成される。モデルの外側からは判別できない。
3. **監査不能性。** 自然言語のChain-of-Thoughtは事後的な作話でありうる。実際の計算経路と一致している保証はない。

Framingoはこの融合を解体する。

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

In natural language this constraint cannot be written down, because deciding "derives from context" itself requires understanding. In Framingo, entities appear as normalized identifiers, so the check reduces to set operations.

This is the same kind of invention as a **type system**. A type system does not make programmers smarter or programs correct. It makes one class of error mechanically detectable before it propagates. That alone changed software reliability. Framingo aims for the same: not fewer hallucinations, but hallucination as an *identifiable event*.

**JA** — これが技術的中核である。媒体が形式的であるため、以下を**構文レベルで**強制できる。

> モデルの出力に現れるすべての実体・述語・関係は、次のいずれかに由来しなければならない。
> **(a)** モデル内に埋め込まれた最小核公理
> **(b)** その時点でコンテクストに載っている知識
> **(c)** 上の二つから明示された推論規則によって導出された命題
>
> **いずれにも由来しないトークンの出現は、定義により幻覚であり、文字列照合によって検出できる。**

自然言語ではこの制約は書き下せない。「文脈に由来する」の判定自体が意味理解を要求するからである。Framingoでは実体が正規化された識別子として現れるため、由来判定が集合演算に還元される。

これは**型システム**と同じ種類の発明である。型システムはプログラマを賢くしないし、プログラムを正しくもしない。ある種類の誤りを、伝播する前に機械的に検出可能にするだけである。それだけでソフトウェアの信頼性は質的に変わった。Framingoが目指すのも同じ——幻覚を減らすのではなく、**幻覚を識別可能な事象にする。**

---

## Architecture / アーキテクチャ

```
             Natural language world (humans, documents, web)
                                 │
        ┌────────────────────────┴─────────────────────────┐
        │   Translation Boundary        翻訳境界            │  ← hallucination is localized here
        │   NL ⇄ Framingo                                   │  ← inspect only this surface
        └────────────────────────┬─────────────────────────┘
                                 │  Framingo
        ┌────────────────────────┴─────────────────────────┐
        │   Logic Core                  論理コア            │  ← holds no knowledge
        │   · small transformer, logic only                 │  ← never saw natural language
        │   · minimal core axioms only                      │
        │   · emits only under the Grounding Constraint     │
        └────────────────────────┬─────────────────────────┘
                                 │  function call (a Framingo query)
        ┌────────────────────────┴─────────────────────────┐
        │   Knowledge Layer             知識供給層          │
        │   · retrieval / DB / API / sensors / simulators   │
        │   · returns results normalized into Framingo      │
        └──────────────────────────────────────────────────┘
```

**EN** — Note what this does *not* claim. Hallucination is not eliminated; it is **localized**. It can still enter at the translation boundary. But where current architectures diffuse it through the entire reasoning process, here it is confined to a single, explicit, auditable interface — whose output is Framingo, and therefore checkable.

**JA** — この設計は幻覚をゼロにしない。**局在化する。** 翻訳境界には依然として幻覚が入りうる。しかし現行アーキテクチャが推論の全過程に幻覚を拡散させるのに対し、ここではそれが単一の、明示された、監査可能なインターフェースに閉じ込められる。そしてその出力はFramingoなので、検証器にかけられる。

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

## Three Design Decisions Worth Naming / 特筆すべき三つの設計判断

### Redundancy dissolves the boundary problem / 冗長性による境界問題の解消

**EN** — "Do humans die?" — is that logic or knowledge? CYC spent forty years failing to fix this boundary. **Framingo does not need to fix it.** The minimal core and the external knowledge base are permitted to **overlap**. If the model asks *just in case* whether humans die, the knowledge base should answer that they do.

CYC collapsed because its hand-written core was the *only* source, so it had to be complete, and completeness was unreachable. Here the two are redundant: a gap in the core is caught by retrieval, a gap in retrieval is caught by the core. The only real failure is absence from both — **which is a coverage problem, not a definitional one.** Coverage can be measured and improved. Definitions could not.

A side effect: **the model no longer needs calibration.** Knowing whether you know is a famously unsolved problem. Here it is unnecessary — when in doubt, just ask.

**JA** — 「人は死ぬ」は論理か知識か。CYCは40年かけてこの境界を確定しようとし、失敗した。**Framingoは確定する必要がない。** 最小核と外部知識ベースは**重複してよい。** モデルが念のため「人は死ぬか」と問い合わせたら、知識ベースは「人は死ぬ」と答えるべきである。

CYCが崩壊したのは、手書きの核が**唯一の**知識源であり、ゆえに完全でなければならず、完全性が達成不可能だったからである。ここでは両者が冗長化されている。核の抜けは検索が拾い、検索の抜けは核が持つ。真の欠落は「両方に無い」場合だけで、**これは定義の問題ではなく網羅性の問題である。** 網羅性は測定でき、改善できる。定義はできなかった。

副次的な帰結：**モデルは較正（calibration）を必要としなくなる。** 自分が知っているかを知ることは未解決の難問だが、ここでは不要である。疑わしければ常に問い合わせればよい。

### The verifier, not the formal language, is load-bearing / 中心にあるのは形式言語ではなく検証器

**EN** — AlphaZero, Lean/Coq provers, Othello-GPT — every lineage that built intelligence out of symbol streams no human converses in shares one thing: **a machine-decidable verifier.** AlphaZero surpassed humans not because it played itself, but because win/loss was decidable without appeal to the model's own opinion. Being formal is a *precondition* for having a verifier, not the thing itself.

And here is the asymmetry that makes this project work: **the correctness of knowledge cannot be machine-verified, but logical validity can.** Because the two are separated, the training corpus for the logic core can be generated *and verified* deterministically — with zero contamination from LLM hallucination. The LLM is the proposer; a deterministic engine is the verifier.

**JA** — AlphaZero、Lean/Coqの証明モデル、Othello-GPT——人間が話さない記号列から知能を立ち上げた系譜には、例外なく**機械判定可能な検証器**がある。AlphaZeroが人類を超えたのは自己対戦したからではなく、勝敗がモデルの意見に依らず決定できたからである。形式的であることは検証器を持つための**前提条件**であって、それ自体ではない。

そしてここに、本企画を成立させる非対称性がある。**知識の正しさは機械検証できないが、論理的妥当性はできる。** 両者が分離されているため、論理コアの訓練コーパスは決定論的に生成でき、決定論的に検証できる——LLM由来の汚染ゼロで。LLMは提案者、決定論的エンジンが検証者である。

---

### Which words a model holds is decided by their shape / モデルが持つ語は、語の形で決まる

**EN** — The section above says that when in doubt, just ask. This is the
strong form of that: **do not decide.**

A model's vocabulary is finite and the world's is not. Names in particular are
arbitrary and unbounded — no amount of reasoning yields "John is a human" — so
Framingo splits its words in two and **marks the split in the orthography**.
Unmarked words are the instinct vocabulary, roughly the size of Lojban's gismu
inventory: `Cut`, `Big`, `Human`, `Apple`, learnt from use and held in the
weights. A leading `'` marks everything else.

The mark is morphological on purpose. Lojban separates root words, borrowings
and names by shape, and shape is what lets a parser sort them without knowing
anything — **which means looking a word up need not be something a model
remembers to do.** The parser resolves every marked word before the model sees
anything, so the lookup cannot be skipped, and the judgement it would otherwise
require — *do I already know this one?* — never arises. That judgement is the
one models are worst at, and the design removes it rather than improving it.

What comes back is a paraphrase into the instinct vocabulary. So a model reasons
in the words it holds, always, and a word it has never met is no harder than one
it has met a thousand times. Measured, over a world of 104 names with a quarter
of them held out of training entirely: **0.996 on names never seen against
0.999 on names seen throughout.** Lying in the dictionary collapses it to
**0.107**, which is how completely the lookup is doing the work; and of 2,000
predictions exactly one names a variable it was not given.

The same rule covers a word the model *derives*. Drop a vessel and it becomes
`'Shard` — marked, not held, and nowhere in the input to have been fetched in
advance. It is looked up when it appears, for the same reason and by the same
test. **Nothing has to notice that it is stuck.**

> A consequence worth stating. If what a model may emit is limited to the
> instinct vocabulary plus the words handed to it, then inventing a name is not
> merely detectable — it is **impossible**. A model that holds no names cannot
> fabricate one. The other half of the Grounding Constraint, over relations
> between words, remains a check rather than a guarantee.

**JA** — 前節は「疑わしければ常に問い合わせればよい」と述べた。本節はその強い形で
ある。**判断させない。**

モデルの語彙は有限で、世界の語彙は有限ではない。とりわけ名前は恣意的で無限である
——「John は人間である」はどれだけ推論しても出てこない。そこで Framingo は語を二つに
分け、**その区別を表記に刻む。** 無印が本能語彙で、規模はおよそ Lojban の gismu 目録
に相当する。`Cut`、`Big`、`Human`、`Apple`。用例から学び、重みに保持する。
先頭の `'` がそれ以外すべてを標示する。

印を形態に置くのは意図的である。Lojban は語根・借用語・名前を**形で**分けており、
形であるからこそパーサーは何も知らずに仕分けできる。**すなわち、語を引くことは
モデルが「忘れずに行う」べきことではなくなる。** パーサーが印の付いた語をすべて、
モデルが何かを見る前に解決する。引き忘れは起こりえず、さもなくば必要だった判断
——「この語は既に知っているか」——**が生じない。** それはモデルが最も苦手とする判断で
あり、この設計はそれを改善するのではなく**消している。**

返ってくるのは本能語彙への言い換えである。ゆえにモデルは常に自分が保持する語で考え、
**一度も出会ったことのない語が、千回出会った語より難しいということがない。**
名前104語のうち四分の一を訓練から完全に外した世界で測った結果：
**一度も見ていない名前で 0.996、訓練を通じて見た名前で 0.999。**
辞書に嘘をつくと **0.107** に崩壊する（それが「引いている」ことの度合いである）。
2,000件の予測のうち、渡されていない変数を名指したのは**1件**。

同じ規則が、モデルが**導いた**語にも及ぶ。容器を落とせば `'Shard` になる ——
印が付いており、保持しておらず、**入力のどこにも無かったので事前に引きようがない。**
現れた時点で引く。同じ理由、同じ判定による。**「行き詰まった」と気づく必要がどこにもない。**

> 述べておくべき帰結。モデルが出力しうる語を「本能語彙 + 渡された語」に限るなら、
> **名前の捏造は検出可能になるのではなく、不可能になる。** 名前を一つも持たない
> モデルは、名前を捏造できない。接地制約のもう半分、すなわち語と語の関係については、
> 依然として保証ではなく検査である。

---

## Falsifiable Claims / 反証可能な主張

| # | Claim / 主張 | Falsified if / 反証条件 |
|---|---|---|
| 1 | **Parameter efficiency** — logic-only models reach comparable reasoning with orders of magnitude fewer parameters / 論理のみのモデルは数桁少ないパラメータで同等の推論能力に達する | Logical ability turns out to depend strongly on knowledge scale / 論理能力が知識量に強く依存する場合 |
| 2 | **Detection** — hallucination detection under the grounding constraint reaches practical rates (≥99%) / 接地制約下で幻覚検出率が実用水準に達する | The model routinely evades the constraint by miscombining known tokens / 既知トークンの誤結合で制約を回避する場合 |
| 3 | **Format matters** — holding meaning fixed, role-tagged flat form generalizes compositionally better than word-order form / 意味を固定したとき、役割タグ付きフラット形式は語順依存形式より高い組成的汎化を示す | No difference. Then format is irrelevant and only the generator matters — also an important result / 差が出ない場合。形式ではなく生成器がすべてという結論になり、これも重要な知見 |
| 4 | **Invariance transfers** — a model trained on conservation-as-string-persistence generalizes to invariants never encoded that way / 文字列永続性として教えた保存則が、そう教えなかった不変量にも汎化する | It does not. Then the model learned copying, not invariance — and a central assumption falls / 汎化しない場合。モデルは不変性ではなくコピーを学習しており、中心的仮定が反証される |
| 5 | **Conversation** — a human and a small model that has never seen natural language hold a multi-turn exchange entirely in Framingo / 自然言語を見たことのない小規模モデルと人間が、Framingoのみで多ターンの対話を成立させる | — *(no precedent exists / 前例のない到達点)* |

---

## On Languages / 言語について

**EN** — This repository is bilingual, and that is not a courtesy. It is part of the argument.

Framingo's **vocabulary is English**; its **grammar is Japanese**. The case-marking argument is set out under [The Name](#the-name--名前について) above; what follows is why *this repository* is bilingual.

The three properties the language specification names as central are ordinary daily operations in Japanese:

- **Order invariance** — Japanese permits scrambling. 「ジョンがナイフでパンを切った」「パンをジョンがナイフで切った」 are both grammatical and identical in meaning. English cannot do this.
- **Argument dropping** — 「パンを切った」 is complete and natural. The specification's "gradient of abstraction" needs no explanation to a Japanese speaker; an English speaker needs the passive voice to approximate it.
- **Separable case marking** — Japanese case particles attach to nouns without fusing, unlike Latin or Russian case endings. `:` is functionally a 格助詞.

So the project combines **the global reach of English vocabulary with the logical regularity of Japanese structure.** Describing an English-lexified formal language *in English* makes it impossible to tell which intuitions come from the design and which leak in from English. Writing in Japanese forces that boundary to be explicit — you cannot explain `agt:` by saying "well, it's the subject."

The Japanese text is the primary source. The English is the door.

**JA** — 本リポジトリは英日併記だが、これは配慮ではなく**主張の一部**である。

Framingoは、**語彙は英語だが、文法は日本語である。** 格標示についての議論は上の[名前について](#the-name--名前について)に置いた。ここで述べるのは、**このリポジトリが**英日併記である理由である。

言語仕様が中核的特徴として掲げる三つの性質は、日本語では日常の運用にすぎない。

- **順序不変性** — 日本語はスクランブリングを許す。「ジョンがナイフでパンを切った」と「パンをジョンがナイフで切った」は両方文法的で同義。英語では不可能。
- **項の脱落** — 「パンを切った」で完結し自然。言語仕様の「抽象度のグラデーション」は日本語話者には説明を要しない。英語話者は受動態で近似するしかない。
- **格の分離可能性** — 日本語の格助詞は名詞に融合せず後接する。ラテン語やロシア語の格語尾とは違う。`:` は機能的に格助詞である。

すなわち本企画は、**英語語彙の世界的普遍性と、日本語構造の論理性を組み合わせる。** 英語語彙の形式言語を英語で語ると、どの直感が設計由来でどの直感が英語からの漏れ込みかを切り分けられない。日本語で書けば境界が強制的に明示化される——`agt:` を「主語だよね」で済ませられない。

日本語テキストが正本である。英語は扉である。

---

## The Name / 名前について

**EN** — **Framingo** is *framing* — Charles Fillmore's frame semantics, the theoretical basis of the case system in the language specification — suffixed with the Japanese **語** (*-go*), the ending by which Japanese names a language: 日本語, 英語, フランス語. **Framing-go: the framing language.** The word is therefore built the way this language is: an English root, a Japanese grammatical ending.

The name is deliberately vague about scope, and that is the point. A name that states a thesis precisely must be abandoned when the thesis grows — BackRub became Google, Twitter became X, Facebook became Meta, all because the name had fixed a boundary the thing outgrew. Java, Python, Rust and Amazon never had that problem, because they never claimed anything. **This project does not yet know what it will become. The name reserves the room; the prose below carries the precision, because prose can be revised and names cannot.**

### The bird

**Framingo** is one letter from *flamingo*, and the mascot is adopted rather than avoided — for a reason that is not decorative.

> **A flamingo is not pink. It is the colour of what it has eaten.** The pigment is carotenoid, taken entirely from algae and crustaceans in its diet; deprive it of that intake and the bird turns pale.

Its defining property is not intrinsic. It is supplied from outside — which is precisely the architecture described above: a logic core that holds no knowledge, coloured entirely by what is placed in its context.

---

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

**This is why English must reach for the passive.** A language whose word order carries the roles cannot spend its word order on viewpoint. To make "the bread" the subject, English must relocate the noun, recast the verb, and demote the agent into a *by*-phrase. Japanese, whose particles carry the roles, can say 「パンをジョンが切った」: the order changes, the verb does not. Japanese has a passive too; the difference is that in English, **because word order is occupied by the roles, shifting viewpoint means rebuilding the sentence.** The specification calls this the "viewpoint-dependent syntactic twist" that forces a model to spend its attention on surface parsing. The twist is not a stylistic accident; it is what a missing marker costs.

The design follows in one line: **the vocabulary was never the problem. Keep it. Replace the role marking.**

### The name states the failure condition

The Japanese idiom 「てにをはが合わない」 — *the teniwoha do not match* — is what you say when a piece of writing does not hold together, when the connections fail. **That is precisely what the verifier checks.** A well-formed statement in this language is one whose teniwoha match.

### Spelling

The concept is romanized **teniwoha** throughout: the form a Japanese writer's hands produce (the IME takes `wo`), and phonotactically even — CV.CV.CV.CV, where *tenioha* leaves a bare vowel in hiatus. Also written *tenioha*; the kana is てにをは.

---

**JA** — **Framingo（フレーミンゴ）**は、*framing* ── Charles Fillmore のフレーム意味論、言語仕様の格体系の理論的基盤 ── に、日本語の **語** を接合したものである。日本語が言語を名付ける接尾辞、すなわち日本語・英語・フランス語の「語」である。**Framing-語、フレーミング語。** つまりこの語自体が、この言語と同じ作りをしている ── **英語の語根に、日本語の文法的語尾。**

名前は射程について意図的に曖昧であり、それが狙いである。主張を正確に述べた名前は、主張が育ったときに捨てねばならない ── BackRub は Google に、Twitter は X に、Facebook は Meta に改名した。いずれも名前が境界を固定し、実体がそれを越えたからである。Java も Python も Rust も Amazon もその問題を持たなかった。**何も主張していなかったからである。**

**本企画は、自分が何になるかをまだ知らない。名前は余地を残し、精度は以下の散文が担う。散文は改訂できるが、名前はできない。**

### 鳥について

**Framingo** は *flamingo* と一文字違いであり、マスコットは避けるのではなく採用する。装飾的でない理由がある。

> **フラミンゴはピンク色ではない。食べたものの色である。** 色素はカロテノイドで、餌の藻類や甲殻類から全量を摂取している。それを断てば、鳥は白くなる。

**この鳥の最も特徴的な性質は、内在的なものではない。外部から供給されている。** それは上で述べたアーキテクチャそのものである ── 知識を持たない論理コアが、文脈に置かれたものによってのみ色付く。

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

**だから英語は受動態に頼らざるをえない。** 語順が役割を担っている言語では、語順を視点のために使えない。「パン」を主語に据えるには、英語は名詞を移し、動詞を組み替え、動作主を *by* 句へ降格させねばならない。助詞が役割を担う日本語は、「パンをジョンが切った」と言える。語順は変わるが、動詞は変わらない。受動態は日本語にもある。違いは、英語では**語順が役割に占有されているため、視点を動かすことが文を組み替えることを意味する**点にある。言語仕様はこれを「視点に依存した統語的ねじれ」と呼び、モデルに表層解析の負荷を強いる元凶とした。**このねじれは文体上の偶然ではない。印の欠落の代償である。**

設計は一行で従う。**問題は語彙ではなかった。語彙は保つ。役割標示だけを差し替える。**

### 名前が、不合格条件を述べている

**「てにをはが合わない」**——文章の繋がりが成立していないとき、日本語話者はこう言う。**これは検証器が判定するものそのものである。** この言語における整形式の文とは、てにをはが合っている文である。

### 綴り

概念の表記は **teniwoha** で統一する。日本語話者の手が自然に打つ形であり（IME入力が `wo`）、音韻的にも CV.CV.CV.CV で均質である（*tenioha* は裸母音が一つ挟まる）。*tenioha* とも綴られる。仮名は「てにをは」。

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

## Implementation / 実装

**EN** — Python, no runtime dependencies. PyTorch is needed only for the
experiments, in the optional `train` dependency group.

```sh
uv sync                                   # parser + checker
uv run framingo parse FILE                # print statements in canonical form
uv run framingo check OUT --context CTX --core CORE   # apply the Grounding Constraint
uv run pytest                             # the spec's own examples are the test corpus
```

| Module | What it is | Status |
|---|---|---|
| `parser.py` | Lexer and recursive-descent parser for Gisaburo v1 / Gisaburo v1 の字句解析と再帰下降パーサ | Every Framingo example in `docs/language-spec.md` parses. Where those examples exceed the chapter 4 EBNF, the widening is listed in `SPEC_DEVIATIONS`; that list is the agenda for revising the spec / 仕様の例文はすべて解析できる。EBNF を超える部分は `SPEC_DEVIATIONS` に列挙してあり、それが仕様改訂の議題になる |
| `grounding.py` | The verifier, v0: token grounding and relation grounding with forward chaining over RULEs / 検証器 v0。語の接地と、RULE の前向き連鎖による関係の接地 | Known gaps are listed in `LIMITS` / 既知の欠落は `LIMITS` に列挙 |
| `world.py`, `render.py`, `corpus.py` | A deterministic toy world, rendered in Framingo and in a word-order form, with held-out splits / 決定論的な小さな世界と、その二形式での書き出し、評価用の分割 | Generated results are cross-checked by the verifier / 生成した帰結は検証器が独立に照合する |
| `experiments/train.py` | Trains a ~0.6M-parameter Transformer from scratch and grades it with the verifier / ゼロから約60万パラメータの Transformer を訓練し、検証器で採点する | Reports accuracy, grounding rate, and detection of fabrications / 正答率、接地率、捏造の検出率を報告する |

**What has been measured so far.** A model trained only on Framingo, having
never seen natural language, learns this world's physics and reaches the
ceiling on held-out splits at around a thousand examples: it keeps colour
while dropping shape when a thing is cut, and binds roles for an animate it
has only ever seen as an agent.

Trained on less, it fails, and the failures are the point. Six models trained
on 250 and 500 examples, on a corpus they had not been tuned against, produced
**1,077 fabrications, of which the verifier flagged 1,077, with 0 false alarms
over 17,643 correct or merely incomplete answers.** Read strictly, this says
the Grounding Constraint is mechanically checkable and the check is not vacuous
— not that hallucination is solved.

That figure is measured on the errors six weak models happened to make, so it
says nothing about the errors a model happens *not* to make. An adversary
(`experiments/adversary.py`) mutates the world's own gold meanings instead,
over 13 classes of wrong recombination — role swaps, substituting an entity
already present in context, carrying a structural modifier through a division,
telling a result in the wrong order: **6,500 mutations, 6,500 flagged, with 0
false alarms over 1,500 deliberate abstractions.** Only 54 of the 6,500 carried
a word absent from the core, so **string matching alone would have caught under
one per cent of them**; relation grounding caught the rest. That is the figure
worth keeping: the non-trivial half of the constraint does nearly all the work.

**Three defects were found while measuring, and none of them could have been
found by reading model output.** (a) The minimal core was not complete: it
derived a structural modifier retained through a division, so that whole class
of fabrication was accepted every time it was tried. (b) The verifier read
`->` as a list separator, although the specification defines it as temporal and
mechanical. (c) The language could not say that two results hold at once, so
the world had to claim that the carried thing's arrival caused the carrier's;
a joint connective now says it (`&>`, spec ch.4 §1.3), and **that absence, not
the models, produced every order violation in the saved runs.** Each defect was
either invisible to the grader or a case where the model was right and the
system was wrong.

**What an incomplete core would cost has been measured, and it is not what the
charter assumed.** Removing RULEs from the core (`experiments/ablate_core.py`)
and re-grading the same saved predictions leaves detection at 100% at every
level tried — with a tenth of the core gone, with half of it gone, and with no
core at all — while false alarms rise from 0% of sound output to 8.1%, to
41.1%, to 100%. A gap here does not hide fabrication, because the check demands
a positive derivation rather than an absence of contradiction, and what is
derivable from nothing gets flagged. **The cost of missing coverage is the
rejection of sound output, not blindness** — the better half of that trade to
be on. It also means a detection rate quoted on its own is worthless: an empty
core detects 100% of fabrications while rejecting 100% of everything else, so
**the claim has to be stated as a pair.** How steep the trade is depends on how
finely the core is written, not on any law; this core enumerates rules, and a
core of general class-level rules would lose far more per rule removed.

**Knowledge has been taken out of the weights and put behind a query.** With
the minimal core **empty**, what a query returns grounds every consequence this
world produces, 400 out of 400 (`src/framingo/knowledge.py`); with the answer
withheld, none of them are grounded. Nothing had to be added to the language —
`QUERY` (spec ch.2 §6.4) already had the right shape, and the checker already
declined to relation-check a question. What this does not show is a *model*
doing it: none has yet been trained to ask.

Proposition 3 (role-tagged versus word-order form) shows no reliable
difference in a world this small. **Proposition 4 (transfer of invariance) is
falsified here.** With "a division destroys structural modifiers and conserves
intrinsic ones" demonstrated under one verb only, a model that scores 1.000 on
the held-out split when that shape is in its training corpus scores 0.07–0.13
when it is not — and 0 of 500 on the dividing event itself, while still getting
the conserving event right 85% of the time. String persistence, which is
copying, transfers; the classification the conservation law rests on does not.

**JA** — Python 製で、実行時の依存はない。PyTorch は実験にのみ必要で、`train`
という任意の依存グループに入れてある。コマンドと構成は上記の通り。

**ここまでに測れたこと。** 自然言語を一度も見ていない、Framingo だけで訓練した
モデルは、この世界の物理を学習し、千件程度の訓練データで未見の分割でも上限に
達する。切られた物の色は残して形は落とし、訓練で動作主としてしか見ていない
動物を対象の位置でも正しく束縛する。

訓練を減らせば誤る。そして重要なのはその誤り方である。250件と500件で訓練した
6つのモデルが、調整に使っていないコーパス上で**1,077件の捏造を出し、検証器は
その1,077件すべてを検出した。正しい答えと不足しているだけの答え17,643件に
対する誤検出は0件である。** 厳密に読めば、これは「接地制約が機械的に判定可能で
あり、その判定が空疎ではない」ことを示すにとどまる。幻覚が解決したという主張では
ない。

この数値は「6つの弱いモデルがたまたま出した誤り」に対する測定であり、
**モデルがたまたま出さない誤り**については何も語らない。そこで、世界の gold 意味を
機械的に変異させる敵対的評価（`experiments/adversary.py`）を用意した。誤結合を
13クラス —— 役割の交換、文脈に既にある実体への置換、分割を通り抜ける構造的修飾語、
逆順で語られた結果など —— にわたって試した結果、**6,500件の変異のうち6,500件を
検出し、意図的な抽象化1,500件に対する誤検出は0件**であった。6,500件のうち核に
無い語を含んでいたのは54件だけなので、**文字列照合だけで捕まえられたのは1%未満**
であり、残りは関係接地が捕まえた。**接地制約の非自明な半分が、仕事のほぼ全部を
している。**

**測定の過程で三つの欠陥が見つかり、そのいずれもモデル出力を読む実践では
発見できなかった。**（a）最小核は完全ではなかった。分割を通り抜けた構造的修飾語を
導出してしまうため、その一クラスの捏造は試された全件が受理されていた。
（b）検証器は `->` を列の区切りとして読んでいた。仕様はそれを時間的・力学的な
ものと定義しているにもかかわらず。（c）言語は「二つの結果が同時に成り立つ」と
言えず、そのため世界は「運ばれた物の到着が運び手の到着を引き起こした」と主張せざる
をえなかった。いまは同時結合子がそれを述べる（`&>`、仕様 第4章 §1.3）。そして
**保存済みの実行で現れた順序違反はすべて、モデルの誤りではなくこの欠落の産物
だった。** いずれの欠陥も、採点器から見えないか、モデルが正しく体系が誤っている
場合であった。

**核が不完全であった場合の代償を測った。憲章が想定していたものとは違った。**
核から RULE を取り除き（`experiments/ablate_core.py`）、同じ保存済み予測を採点し
直すと、試したどの水準でも検出率は 100% のままである —— 核の一割を落としても、
半分を落としても、核が空でも。一方で誤検出は健全な出力の 0% から 8.1%、41.1%、
100% へと上がる。ここでの欠落は捏造を隠さない。検査が要求するのは矛盾の不在では
なく**積極的な導出**であり、何からも導出できないものには印が付くからである。
**網羅性の不足が払わせる代償は、見落としではなく健全な出力の却下である** ——
この取引の、まだ良い側である。同時にこれは、検出率を単独で挙げることが無意味だと
いうことでもある。空の核は捏造の 100% を検出しつつ、それ以外の 100% を却下する。
**主張は対で述べなければならない。** 取引の勾配は核をどれだけ細かく書くかで決まり、
法則ではない。この核は規則を列挙しており、クラス水準の一般規則で書かれた核なら、
1規則を削る損害はもっと大きい。

**知識を重みから取り出し、問い合わせの先に置いた。** 最小核を**空**にしても、
問い合わせが返すものでこの世界の帰結は全件接地する（400件中400件、
`src/framingo/knowledge.py`）。返答を与えなければ一件も接地しない。
**言語に足したものは何もない** —— `QUERY`（仕様 第2章 §6.4）は既に正しい形をして
おり、検証器は既に問いを関係照合の対象から外していた。ただしこれは**モデルが
それを行えること**を示してはいない。そう訓練したモデルはまだ存在しない。

命題3（役割タグ付きフラット形式と語順依存形式の比較）については、この程度の小さな
世界では有意な差が出ていない。**命題4（不変性の転移）は、この世界では反証された。**
「分割は構造的修飾語を破壊し内在的修飾語を保存する」を一つの動詞でのみ示した場合、
その形が訓練コーパスにあれば同じ分割で 1.000 を取るモデルが、なければ 0.07〜0.13
しか取れない —— 分割する側のイベントだけを見れば500件中0件であり、保存する側の
イベントは85%正しい。**文字列の永続性、すなわちコピーは転移する。保存則が
依存している分類は転移しない。**


---

## Documents / 文書

| File | Contents |
|---|---|
| [`docs/core-thesis.md`](docs/core-thesis.md) | **Design charter (current).** The central claim, architecture, verifier, recursive loop, falsifiable propositions. / **設計憲章（現行）。** 中心命題、アーキテクチャ、検証器、再帰ループ、反証可能な命題 |
| [`docs/version-names.md`](docs/version-names.md) | **Version codename roster.** Linguists whose theses future specifications could embody, and the rule for assigning them. / **バージョン・コードネーム名簿。** 各世代が体現しうる主張と、その割り当て規則 |
| [`docs/language-spec.md`](docs/language-spec.md) | **Language specification, Gisaburo v1.** Case frames, concept composition, causal connectives — valid as *means* (charter ch.7). / **言語仕様 Gisaburo v1。** 格フレーム、概念合成、因果結合子。手段として有効（憲章第7章） |
| [`src/framingo/`](src/framingo) | **Implementation.** Parser, grounding checker, toy world and corpus builder. / **実装。** パーサ、接地チェッカ、小さな世界とコーパス生成 |
| [`docs/overview.md`](docs/overview.md) | Original draft, kept for the record. Ch. 1 and 5 remain, both superseded by `core-thesis.md`. / 初期草稿（記録として保存）。残る第1・5章は `core-thesis.md` が置き換える |

---

## Open Problems / 未解決の問題

1. **Coverage of the minimal core** — the boundary need not be exact, but "absent from both core and retrieval" remains a real gap. / 最小核の網羅性——境界の確定は不要になったが、「核にも外部にも無い」は残る
2. **Design of the translation boundary** — the only place hallucination can enter. / 翻訳境界の設計——幻覚が入りうる唯一の場所
3. **Can logic be learned without knowledge?** Open, and this project effectively tests it. / 知識なしに論理は学べるか——開いた問い
4. **Query bootstrapping** — knowing *what to ask for* may itself require knowledge. In a formal language the shape of the question is the shape of the action, so a query can be formed structurally; whether a model can be trained to always form one is untested. / クエリ発行のブートストラップ——形式言語では問いの形が行為の形なので構文的に組めるが、常に組むようモデルを訓練できるかは未検証
5. **No dialogue layer yet** — no speaker/hearer, no speech acts, no cross-turn anaphora. / 対話層が存在しない
6. **The verifier is only as right as the core it reads** — every number above depends on it, and three of its defects have already been found by measuring rather than by reading output. / 検証器は、それが読む核が正しい限りでしか正しくない——上記のすべてがこれに依存しており、既に三つの欠陥が、出力を読むのではなく測ることによって見つかっている

---

## Contributing / 貢献について

Published as [`github.com/bellyachers`](https://github.com/bellyachers). Read plainly, the charter is one long complaint; the organization is named accordingly.

[`github.com/bellyachers`](https://github.com/bellyachers) にて公開。憲章は素直に読めば全編が文句であり、組織名はそれに従っている。

**EN** — What is passed between generations of this project is not model weights. It is the language specification, the verifier, the corpus generator, and the minimal core — all human-readable, machine-checkable, version-controlled artifacts.

Contributions are therefore judged the same way regardless of whether a human or a machine wrote them: **does the diff pass the verifier?** Chapter 11 of the charter was written by Claude (Opus 5) and is marked as such. It is subject to the same standard.

**JA** — 本企画で世代を超えて受け渡されるのはモデルの重みではない。言語仕様、検証器、コーパス生成器、最小核——すべて人間可読で、機械検証可能で、バージョン管理された成果物である。

したがって貢献は、それを書いたのが人間か機械かを問わず同じ基準で判定される。**その差分は検証器を通るか。** 憲章第11章はClaude（Opus 5）が執筆し、その旨が明記されている。同じ基準に服する。

---

## License / ライセンス

Documentation and specification: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
Code: [Apache 2.0](LICENSE-CODE).

文書および仕様：CC BY 4.0。コード：Apache 2.0（`LICENSE-CODE`）。

A specification under a copyleft license does not get adopted. That would defeat the purpose.
コピーレフトの仕様は採用されない。それでは目的に反する。
