# Framingo Language Specification — Gisaburo (v1) / Framingo 言語仕様 —— Gisaburo（v1）

> **Status of this document / 本文書の位置づけ**
>
> **EN** — This file holds chapters 2–4 of the original draft `overview.md`. Chapter 7 of the charter (`core-thesis.md`) places this specification as **means, not claim**: its details may change freely so long as it stays learnable in five minutes, efficient to train on, and mechanically checkable for grounding. The chapters keep their original numbers so that cross-references — the charter's "former chapters 2–4", and "the previous chapter" / "the next chapter" in the text — still resolve. Chapter 1 and chapter 5 remain in `overview.md`, superseded by the charter.
>
> Because the specification is dense with code, EN and JA prose alternate around each Framingo sample, and each sample appears once. Comments inside samples are given in both languages. The Japanese is the primary source; the English follows it closely and does not revise the specification.
>
> **JA** — 本ファイルは、初期草稿 `overview.md` の第2〜4章を移したものである。憲章（`core-thesis.md`）第7章は、本仕様を**主張ではなく手段**と位置づける。5分で習得可能、学習効率が高い、接地判定が機械的、の三条件を満たす限り、細部はいくらでも変更されてよい。章番号は原文のまま残した。憲章の「旧第2〜4章」や、本文中の「前章」「次章」という参照を生かすためである。第1章と第5章は `overview.md` に残り、憲章によって置き換えられている。
>
> 本仕様はコード例が多いため、Framingo の例文ごとに EN と JA の散文を交互に置き、例文そのものは一度だけ示す。例文中のコメントは二言語で併記する。日本語が正本であり、英語はそれに忠実に従い、仕様を改めるものではない。

---

# Chapter 2: Syntactic Architecture and the Case System / 第2章：構文アーキテクチャと格システム

*Framingo Design Specification and Development Charter / Framingo 設計仕様・開発憲章*

## 1. The Foundation of Syntax: An Engineering Implementation of Neo-Davidsonian Semantics / 構文設計の根幹：ネオ・デイヴィドソン流意味論の工学的実装

**EN** — To realize the idea set out in the previous chapter — "serialize the raw data of thought without distortion" — this language (Framingo) adopts as its basic syntactic structure the framework of Neo-Davidsonian semantics from the philosophy of language and semantics.

**JA** — 前章で定義した「思考の生データを歪みなく直列化（シリアライズ）する」という思想を具現化するにあたり、本言語（Framingo）は言語哲学および意味論におけるネオ・デイヴィドソン流意味論（Neo-Davidsonian Semantics）の枠組みを構文の基礎構造として採用する。

### 1.1 Discarding Traditional Grammar (Syntax) / 伝統的文法（統語論）の破棄

**EN** — In natural languages (especially SVO languages, English first among them), the sentence has long been treated as an asymmetric binary opposition of "subject + verb phrase". Yet in physical reality, and in the cognitive model of events, no privileged slot called "subject" really exists. When we observe the event "John cut the bread with a knife", for example, the physical fact objectively taking place is merely an equal combination of the following elements.

- Event type: cutting (Cut)
- The physical agent that caused the action: John
- The object acted upon (Patient/Target): Bread
- The physical instrument that mediated it (Instrument/Tool): Knife

Natural language, following the speaker's subjective focus (viewpoint), elevates "John" to the subject position, or uses the passive to raise "the bread" to subject. This **"viewpoint-dependent syntactic twist"** is precisely what forces needless syntactic-parsing load on LLMs.

**JA** — 自然言語（特に英語をはじめとするSVO型言語）において、文は長らく「主語（Subject）＋動詞句（Verb Phrase）」という非対称な二項対立として扱われてきた。しかし、物理的現実や事象の認知モデルにおいて、「主語」という特権的なスロットは本来存在しない。 例えば、「ジョンがナイフでパンを切った」という現象を観察したとき、客観的に生起している物理的事実は以下の要素の等価な結合に過ぎない。

- 事象の種類（Event Type）：切断（Cut）
- 動作を引き起こした物理主体（Agent）：ジョン（John）
- 作用を受けた対象（Patient/Target）：パン（Bread）
- 媒介された物理的器具（Instrument/Tool）：ナイフ（Knife）

自然言語は、発話者の主観的フォーカス（視点）に基づいて「ジョン」を主語の位置に祭り上げたり、受動態を用いて「パン」を主語に繰り上げたりする。この「視点に依存した統語的ねじれ」こそが、LLMに不要な統語解析の負荷を強いる元凶である。

### 1.2 A Flat Case Frame Centred on the Event / 事象（Event）を中心としたフラットな格フレーム

**EN** — In Framingo, the minimal unit of a sentence is "one independent event". An event is defined as a core "predicate" joined, in a completely flat key–value form, with the various "case arguments (slots)" surrounding that event.

Mathematically, an event e is modelled as a conjunction of first-order predicates such as:

**JA** — Framingoにおいて、文の最小構成単位は「独立した1つの事象（Event）」である。 事象は、核となる「述語（Predicate）」と、その事象を取り巻く各種の「格引数（Case Arguments / Slots）」が完全にフラットなキー・バリュー形式で結合されたものとして定義される。

数学的には、ある事象 e は以下のような一階述語の論理積としてモデル化される。

Event(e)∧Predicate(e,Cut)∧agt(e,John)∧tgt(e,Bread)∧tool(e,Knife)

**EN** — Framingo's concrete syntax writes this logical structure down directly as a token sequence.

**JA** — Framingoの具象構文（Concrete Syntax）は、この論理構造をトークン列として直接書き下す。

```
Action: Cut agt:John tgt:Bread tool:Knife
```

**EN** — A more concise notation, taking the predicate itself as the header, is also accepted as equivalent.

**JA** — または、より簡潔に述語を直接ヘッダとする記法も等価として許容する。

```
Cut: agt:John tgt:Bread tool:Knife
```

**EN** — With this structure, every slot is fully orthogonal (independent), and no slot stands in a grammatical dependency on another.

**JA** — この構造により、各スロットは完全に直交（独立）し、相互に文法的な従属関係を持たない。

## 2. Slot Order Invariance and Symmetry / スロットの順序不変性（Order Invariance）と対称性

**EN** — A crucial feature of this syntactic architecture is that "the order of the case slots following the predicate is entirely free, and order does not change meaning."

**JA** — 本構文アーキテクチャの極めて重要な特徴は、「述語の後に続く格スロットの並び順は完全に任意であり、順序によって意味が変化しない」という点である。

### 2.1 The Benefits of Order Invariance / 順序不変性のメリット

**EN** — The following three sentences are evaluated as exactly the same event by Framingo's parser and interpreter.

**JA** — 以下の3つの文は、Framingoのパーサーおよび意味解釈系において完全に同一の事象として評価される。

```
// Pattern 1: agent first (close to an English speaker's intuition)
// パターン1：動作主先行（英語の話者直感に近い配置）
Action: Cut agt:John tgt:Bread tool:Knife

// Pattern 2: target first (focused on the object acted upon)
// パターン2：対象先行（作用を受ける物体にフォーカスした配置）
Action: Cut tgt:Bread tool:Knife agt:John

// Pattern 3: tool first (interface-oriented)
// パターン3：道具先行（インターフェース重視の配置）
Action: Cut tool:Knife agt:John tgt:Bread
```

**EN** — The effect of this order invariance on LLM training is immense. A Transformer trained on natural language devotes many of its attention heads to parsing positional encoding, in order to work back from word order to case relations (who did what to whom). In Framingo, however, every token carries an explicit role marker such as `agt:` or `tgt:`, so self-attention can put its weight directly on "the correspondence between predicate and case" without depending on positional encoding.

**JA** — この順序不変性がLLMの学習に与える影響は絶大である。 自然言語を学習するトランスフォーマーモデルは、「語順（Word Order）」から格関係（誰が誰をどうしたか）を逆算するために、アテンション層の多くのヘッドを位置エンコーディング（Positional Encoding）の解析に割いている。 しかしFramingoでは、各トークンが `agt:` や `tgt:` という明示的な格タグ（Role Marker）を冠しているため、位置エンコーディングに依存することなく、自己注意機構（Self-Attention）はダイレクトに「述語と格の対応関係」へ重みを張ることができる。

### 2.2 Order Shuffling as Data Augmentation / データ拡張（Data Augmentation）としての順序シャッフル

**EN** — When generating synthetic data, the slot order of the same event is shuffled randomly and mixed into the training corpus. This cuts the model off completely from "overfitting to particular word-order patterns", and it acquires **the ability to perceive "which slots are present in context, and what each value is" as a pure logical set.**

**JA** — 合成データを生成する際、同一の事象に対してスロットの順序をランダムにシャッフルして学習コーパスに混入させる。これにより、モデルは「特定の語順パターンへの過学習」から完全に遮断され、**「文脈の中にどのスロットが存在し、それぞれの値が何であるか」という純粋な論理集合としての認識能力**を獲得する。

## 3. Optionality of Case Slots and the Gradient of Abstraction / 格スロットの任意性（Optionality）と抽象度のグラデーション

**EN** — As established in the discussion of the previous chapter, capturing the essence of physical law and causation does not require every case slot to be present at all times. On the contrary, "slots dropping out as needed, and the abstraction of the sentence shifting smoothly as a result" is the very source of Framingo's expressive power.

**JA** — 前章の議論で確立された通り、物理法則や因果の本質を捉える上で、すべての格スロットが常に揃っている必要はない。むしろ、「必要に応じてスロットが脱落し、それによって文の抽象度が滑らかに変化する」ことこそが、Framingoの表現力の源泉である。

### 3.1 Minimizing Obligatory Arguments (Predicate and Target as the Core) / 必須項の最小化（コアとしての述語と対象）

**EN** — In describing an event, the minimal core that truly cannot be stripped away is, in most cases, just two things: the "predicate (what happens)" and the "target (to what it happens)".

**JA** — 事象を記述する上で、理論上真に削ぎ落とせない最小限の核は、多くの場合「述語（何が起きるか）」と「対象（何に対して起きるか）」の2点のみである。

- **Maximum resolution (individual episode) / 最大解像度（個別エピソード）：**
  ```
  Action: Cut agt:John tgt:Bread[1] tool:Knife tense:past
  ```
  EN — All the information — "who cut what, with what, when" — is specified.
  JA — 「誰が、何を、何を使って、いつ切ったか」の全情報が特定されている。
- **Abstracting the agent (passive, cause unspecified) / 動作主の抽象化（受動・原因不問）：**
  ```
  Action: Cut tgt:Bread[1] tool:Knife
  ```
  EN — Describes only the fact that the bread was cut with a knife. Whether John or a mechanical arm cut it is left open.
  JA — パンがナイフで切られた事実のみを記述。ジョンが切ったのか、機械のアームが切ったのかは問わない。
- **Abstracting the tool (means unspecified) / 道具の抽象化（手段不問）：**
  ```
  Action: Cut tgt:Bread[1]
  ```
  EN — Extracts only the core of the event "it was cut", whether by laser or by blade.
  JA — レーザーで切られたのか、刃物で切られたのかを問わず、「切断された」という事象の核のみを抽出。
- **Ultimate abstraction (pure causal law) / 極限の抽象化（純粋因果則）：**
  ```
  Action: Cut tgt:Bread
  ```
  EN — Even the individual identifier drops out; this refers to "the act of cutting bread in general".
  JA — 個体識別子すら脱落し、「パンを切るという行為一般」を指す。

**EN** — By experiencing this gradient, the model naturally acquires flexible, Bayesian-like reasoning behaviour: "with more information, the resolution of the inferred result rises; with less, the result too falls back to a general, abstract state."

**JA** — モデルはこのグラデーションを経験することで、「情報が多ければ推論結果（Result）の解像度が上がり、情報が少なければ結果もまた一般的・抽象的な状態へとフォールバックする」という、柔軟なベイズ的推論の挙動を自然に獲得する。

## 4. The Selected Core Case Slots / 厳選されたコア格スロット一覧（Core Case Slots）

**EN** — Grammars of natural languages contain dozens of cases and prepositional uses, but to cover the mechanics of the physical world, state transitions and agents' action plans, it suffices to define the following **eight principal case slots** strictly.

| Slot / スロット名 | Full name / 正式名称 | Physical and semantic definition / 物理・意味論的定義 | Typical examples / 典型例 |
| ------------- | ---------------------------- | ---------------------------------------------- | ------------------------------------------------ |
| **`agt:`**    | Agent（動作主） | The mechanical or volitional source that actively brings about the event / 事象を能動的に引き起こす力学的・意志的ソース | `agt:John`, `agt:Robot_Arm`, `agt:Wind` |
| **`tgt:`**    | Target / Patient（対象） | The entity that receives the event's direct action and changes state / 事象の直接的な作用を受け、状態が変化する実体 | `tgt:Bread`, `tgt:Apple`, `tgt:Door` |
| **`tool:`**   | Instrument（道具・媒介） | The object the agent interposes to act on the target / 動作主が対象に作用を及ぼすために媒介させる物体 | `tool:Knife`, `tool:Key`, `tool:Hammer` |
| **`src:`**    | Source（起点・出所） | The starting point of spatial movement, or the initial state of a state transition / 空間移動の出発点、または状態遷移の初期状態 | `src:Table`, `src:Room_A`, `src:Inside.Box` |
| **`dst:`**    | Destination（終点・目標） | The end point of spatial movement, or the end state of a state transition / 空間移動の到達点、または状態遷移の到達先 | `dst:Floor`, `dst:Room_B`, `dst:On.Chair` |
| **`loc:`**    | Location（静的位置） | The spatial or environmental context in which the whole event takes place / 事象全体が生起している空間的・環境的文脈 | `loc:Kitchen`, `loc:Outdoor`, `loc:Dark.Room` |
| **`goal:`**   | Goal / Intention（目的） | The expected result state driving the action / そのアクションを駆動している期待結果状態 | `goal:(Become agt:Bread.Slice)` |
| **`reason:`** | Reason / Cause（理由・死因） | The direct mechanical trigger of a failure or event / 失敗や事象の直接的な力学的トリガー | `reason:Slip`, `reason:Friction`, `reason:Block` |

**JA** — 自然言語の文法書には何十種類もの格や前置詞用法が存在するが、物理世界の力学、状態遷移、エージェントの行動計画を網羅するためには、以下の**8つの主要格スロット**を厳格に定義すれば十分である。（上表参照）

### 4.1 Describing Space and Topology (`src:`, `dst:`, `loc:`) / 空間・トポロジーの記述（`src:`, `dst:`, `loc:`）

**EN** — When describing the physics of movement and placement, one must not fall into the labyrinth of prepositions (in, on, at, into, onto, from). In Framingo, every spatial change is unified as "a transition from a source (`src:`) to a destination (`dst:`)".

**JA** — 移動や配置の物理学を記述する場合、前置詞の迷宮（in, on, at, into, onto, from）に陥ってはならない。Framingoでは、空間変化はすべて「起点（`src:`）から終点（`dst:`）への遷移」として統一される。

```
// The cat jumps from under the table onto the chair
// 猫がテーブルの下から椅子の上へ飛び乗る
Action: Move agt:Cat src:Under.Table dst:On.Chair

// Put the apple into the box
// リンゴを箱の中に入れる
Action: Put agt:John tgt:Apple src:On.Counter dst:In.Box
```

**EN** — The mechanical, geometric vector of "from where to where" is fixed without ambiguity by just two slots.

**JA** — 「どこからどこへ」という力学的な幾何学ベクトルが、わずか2つのスロットで曖昧さなく確定する。

### 4.2 Separating Intention from Action (`goal:`) / 意図と行為の分離（`goal:`）

**EN** — In robotics and in the thought processes of autonomous agents, describing "the actual action" separately from "the intention (expectation) that gave rise to it" is decisive for planning and debugging.

The `goal:` slot makes it possible to hold a "nested expected state" inside an event.

**JA** — ロボット工学や自律型エージェントの思考プロセスにおいて、「実際のアクション」と「それを起こした意図（期待）」を分離して記述することは、計画（Planning）とデバッグにおいて決定的な意味を持つ。

`goal:` スロットは、事象の中に「入れ子の期待状態」を保持することを可能にする。

```
Action: Push agt:Robot tgt:Door goal:(State tgt:Door is:Open)
```

**EN** — After this action is performed, the causal connectives described later contrast "whether the door actually opened (success)" with "whether it was locked and did not open (failure)". The model thus becomes able to perceive the gap between "attempt" and "outcome".

**JA** — このアクションが実行された後、後述する因果結合子によって「実際にドアが開いたか（成功）」あるいは「鍵がかかっていて開かなかったか（失敗）」が対比される。これにより、モデルは「試み（Attempt）」と「結果（Outcome）」のギャップを認知できるようになる。

## 4bis. Words the Model Does Not Hold: the Mark `'` / モデルが持たない語：印 `'`

**EN** — A model's vocabulary is finite. The world's is not. Names in
particular are arbitrary, unbounded and particular: no amount of reasoning
yields "John is a human", and no training set can contain every name there
will be.

Framingo therefore divides its words in two, **and marks the division in the
orthography**.

```
Cut agt:'John tgt:Big.Red.Apple tool:Knife
```

Here `'John` lies outside the instinct vocabulary and is fetched; `Cut`, `Big`,
`Red`, `Apple` and `Knife` are held.

- **Instinct vocabulary** — unmarked. Roughly the size of Lojban's gismu
  inventory: the words a model is trained on and holds in its weights.
  `Cut`, `Big`, `Human`, `Apple`. A model is expected to know these the way any
  language model knows a word, from use.
- **Outside it** — marked with a leading `'`. Names, borrowings, anything the
  vocabulary does not cover. A model holds none of them.

The mark is morphological on purpose. Lojban separates root words, borrowings
and names **by shape**, and shape is what lets a parser sort them without
knowing anything. Here it has a sharper consequence: **because the mark is
visible before the word is understood, resolving it is not something a model
must remember to do.** A parser fetches every marked word and hands the results
over with the input, so a model cannot fail to look one up. What would
otherwise be a habit — and a habit that requires judging whether one already
knows a word, which is the judgement models are worst at — becomes a mechanical
step that happens before the model sees anything.

What comes back is a paraphrase **into the instinct vocabulary**: `'John` is a
human, `'Quokka` is a small animal that eats grass. So a model reasons in the
words it holds, always, and a word it has never met is no harder than one it
has met a thousand times.

> **A consequence worth stating.** If what a model may emit is limited to the
> instinct vocabulary plus the words handed to it, then inventing a name is not
> merely detectable — it is **impossible**. A model that holds no names cannot
> fabricate one. The other half of the Grounding Constraint, over relations
> between words, remains a check rather than a guarantee.

**JA** — モデルの語彙は有限である。世界の語彙は有限ではない。とりわけ名前は恣意的で
無限で個別的であり、「John は人間である」はどれだけ推論しても出てこないし、
これから現れるすべての名前を含む訓練集合も存在しない。

そこで Framingo は語を二つに分け、**その区別を表記に刻む。**

```
Cut agt:'John tgt:Big.Red.Apple tool:Knife
```

ここで `'John` は本能語彙の外にあり取得される。`Cut`・`Big`・`Red`・`Apple`・`Knife`
は保持される。

- **本能語彙** —— 無印。Lojban の gismu 目録とおよそ同程度の規模。モデルが訓練を
  通じて重みに保持する語。`Cut`、`Big`、`Human`、`Apple`。通常の言語モデルが語を
  知るのと同じ仕方で、用例から知っていることを期待する。
- **その外** —— 先頭に `'` を付す。名前、借用語、語彙が覆わないもの一切。
  モデルはこれらを一つも保持しない。

印を形態的に置くのは意図的である。Lojban は語根・借用語・名前を**形で**分けており、
形であるからこそパーサーは何も知らずに仕分けできる。ここではそれがより鋭い帰結を持つ。
**印は語を理解する前に見えるので、それを解決することはモデルが「忘れずに行う」べき
ことではなくなる。** パーサーが印の付いた語をすべて引き、その結果を入力とともに渡す。
モデルは引き忘れることができない。**さもなくば習慣になっていたもの —— しかも
「その語を既に知っているか」という、モデルが最も苦手とする判断を要する習慣 —— が、
モデルが何かを見る前に済んでいる機械的な一段になる。**

返ってくるのは**本能語彙への**言い換えである。`'John` は人間である、`'Quokka` は草を
食べる小さな動物である。ゆえにモデルは常に自分が保持する語で考え、**一度も出会った
ことのない語が、千回出会った語より難しいということがない。**

> **述べておくべき帰結。** モデルが出力しうる語を「本能語彙 + 渡された語」に限るなら、
> **名前の捏造は検出可能になるのではなく、不可能になる。** 名前を一つも持たない
> モデルは、名前を捏造できない。接地制約のもう半分、すなわち語と語の関係については、
> 依然として保証ではなく検査である。

---

## 5. TAM (Tense, Aspect, Modality) and Quantitative Modifiers as Slots / TAM（時制・相・法）および定量的修飾子のスロット化

**EN** — TAM (tense, aspect, modality), the greatest breeding ground of irregularity in natural language, never causes the verb to change form (conjugate) in Framingo; **all of it is treated equally as independent modifier slots.**

**JA** — 自然言語における最大の不規則性の温床であるTAM（Tense, Aspect, Modality：時制・相・法）は、Framingoにおいては動詞の語形変化（活用）を一切起こさせず、**すべて独立した修飾スロット（Modifier Slots）として等価に扱う。**

### 5.1 TAM Slot Specification / TAMスロットの仕様

#### (1) `tense:` (tense / position on the time axis) / `tense:`（時制 / 時間軸上の位置）

**EN** — Temporal position relative to the time of utterance (the present).

- `tense:past` (settled past fact)
- `tense:present` (current state, habit)
- `tense:future` (prediction, plan) — however, in universal physical laws (`RULE:`), this slot is as a rule omitted (unmarked).

**JA** — 発話時（現在）を基準とした時間的位置付け。

- `tense:past`（過去の確定事実）
- `tense:present`（現在の状態・習慣）
- `tense:future`（未来の予測・予定） ※ただし、普遍的な物理法則（`RULE:`）においては、このスロットは原則として省略（無標）される。

#### (2) `asp:` (aspect) / `asp:`（相 / アスペクト）

**EN** — The internal temporal structure of the event (whether completed or ongoing).

- `asp:completed` (completive: the event has ended and its result state persists)
- `asp:progressive` (progressive: the physical process of the event is currently under way)
- `asp:iterative` (iterative: the same action is repeated intermittently)

**JA** — 事象の内部時間的構造（完了しているか、継続中か）。

- `asp:completed`（完了相：事象が終結し、結果状態が残存している）
- `asp:progressive`（進行相：事象の物理プロセスが現在進行中である）
- `asp:iterative`（反復相：同様の動作が断続的に繰り返されている）

#### (3) `mod:` (modality) / `mod:`（法 / モダリティ）

**EN** — Necessity, possibility and ability of the event.

- `mod:can` (possibility, ability: there is latent capacity to bring about the event)
- `mod:must` (necessity, obligation: unavoidable as a physical constraint or logical consequence)
- `mod:may` (probability: may occur with a probability of around 50%)

**JA** — 事象の必然性、可能性、能力。

- `mod:can`（可能・能力：その事象を引き起こす潜在能力がある）
- `mod:must`（必然・義務：物理的拘束または論理的帰結として不可避である）
- `mod:may`（蓋然性：50%前後の確率で生起し得る）

### 5.2 Quantity and Frequency Slots / 定量・頻度スロット（Quantifiers & Frequency）

**EN** — The number of repetitions and the frequency of an event are likewise placed flat, as slots modifying the verb.

- **`iter:` (number of repetitions):** `iter:1`, `iter:3`, `iter:many`
- **`freq:` (frequency of occurrence):** `freq:always`, `freq:often`, `freq:rarely`, `freq:never`

**JA** — 事象の反復回数や発生頻度も、動詞を修飾するスロットとしてフラットに配置する。

- **`iter:`（反復回数）：** `iter:1`, `iter:3`, `iter:many`
- **`freq:`（発生頻度）：** `freq:always`, `freq:often`, `freq:rarely`, `freq:never`

### 5.3 A Combined Example / 統合記述例

**EN** — "Yesterday John was cutting the bread with a knife, three times in a row (progressive, iterative)" — an event that in natural language becomes a complex past-progressive, iterative expression — is written plainly as a set of slots:

**JA** — 「ジョンは昨日、ナイフでパンを3回続けて切っていた（進行・反復）」という、自然言語であれば複雑な過去進行・反復表現になる事象は、以下のようにスロットの集合として明快に記述される。

```
FACT: Action: Cut agt:John tgt:Bread tool:Knife iter:3 asp:progressive tense:past
```

**EN** — The parser can store the attendant attribute flags immediately as keys of a dictionary object, without altering the verb `Cut` at all.

**JA** — パーサーは動詞 `Cut` を一切変形させることなく、付随する属性フラグを辞書オブジェクトのキーとして即座に格納できる。

## 6. The Sentence Frame (Prefix / Epistemic Status) / 文の大枠（Prefix / Epistemic Status）の定義

**EN** — The epistemic status of a whole sentence (what kind of claim it makes) is declared uniquely by a prefix at its head. The model can thus fix the interpretation mode of the text that follows (switching its reasoning circuit) the moment it reads the first token.

This language establishes the following **four frame prefixes.**

**JA** — 文全体の認識論的ステータス（その文がどのような性質の主張であるか）は、文頭のプリフィックス（Prefix）によって一意に宣言される。これにより、モデルは文の最初の1トークンを読んだ瞬間に、後続するテキストの解釈モード（推論回路の切り替え）を確定させることができる。

本言語では、以下の**4つの大枠プリフィックス**を制定する。

```
[PREFIX]: [Event_1] (Connector [Event_2] ...)
```

### 6.1 `RULE:` (Universal Law, General Rule) / `RULE:`（普遍的法則・一般規則）

- **Definition / 定義：**
  EN — Physical laws, causal laws and ontological definitions that hold universally, transcending time, place and particular individuals.
  JA — 時間、場所、特定の個体を超越して普遍的に成立する物理法則、因果律、オントロジーの定義。
- **Properties / 特性：**
  EN — Has no `tense:` and no individual instance ID (`#123`); written with universal quantification (`Every.`) or undefined general concepts.
  JA — `tense:` や個別のインスタンスID（`#123`）を持たず、全称量化（`Every.`）や未定義の一般概念で記述される。
- **Example / 例：**
  ```
  RULE: Action: Drop tgt:Every.Break-prone.Thing -> Break agt:It
  ```
  EN — (Every fragile thing breaks when dropped.)
  JA — （壊れやすいあらゆる物は、落とすと破損する）

### 6.2 `FACT:` (One-Off Event, Episodic Record) / `FACT:`（一度きりの出来事・エピソード記録）

- **Definition / 定義：**
  EN — A settled historical fact or observation log that actually occurred once, at a particular time and place.
  JA — 特定の時空において実際に発生した、1回限りの確定的な歴史的事実、観測ログ。
- **Properties / 特性：**
  EN — Often accompanied by particular instances, a concrete agent and a tense (`tense:past` etc.). Used to record an agent's episodic memory.
  JA — 特定のインスタンス、具体的な動作主、時制（`tense:past` など）を伴うことが多い。エージェントのエピソード記憶（Episodic Memory）の記録に用いられる。
- **Example / 例：**
  ```
  FACT: Action: Cut agt:John tgt:Bread#402 tool:Knife#1 -> Result: Become agt:It.Slice count:5
  ```
  EN — (John cut the particular loaf #402 with knife #1 into five slices.)
  JA — （ジョンが特定のパン#402をナイフ#1で切り、5枚のスライスにした）

### 6.3 `HYPO:` (Counterfactual Simulation, Hypothesis) / `HYPO:`（反事実的シミュレーション・仮定）

- **Definition / 定義：**
  EN — A hypothetical scenario or thought experiment ("what if") that has not occurred in reality but could occur if its preconditions were met.
  JA — 現実には生起していないが、前提条件が満たされた場合に生起し得る仮想的なシナリオ、思考実験（"What-if"）。
- **Properties / 特性：**
  EN — Accompanied by preconditions (`when:`); serves as the simulation space in which an agent formulates action plans.
  JA — 前提条件（`when:`）を伴い、エージェントが行動計画（Planning）を策定する際のシミュレーション空間として機能する。
- **Example / 例：**
  ```
  HYPO: when:(State tgt:Room is:Dark) Action: Walk agt:John dst:Door -> Result: Bump agt:John tgt:Wall
  ```
  EN — (If the room were dark and John walked to the door, he would bump into the wall.)
  JA — （もし部屋が暗ければ、ジョンがドアへ歩いた場合、壁に衝突するだろう）

### 6.4 `QUERY:` (Query, Request for Inference) / `QUERY:`（問い合わせ・推論要求）

- **Definition / 定義：**
  EN — A prompt form asking the model to predict or fill in missing slots or causal consequences.
  JA — モデルに対して欠落したスロットや因果の帰結を予測・補完させるためのプロンプト形式。
- **Properties / 特性：**
  EN — Unknown items are held by the placeholder `?` (question mark).
  JA — 未知の項目が `?`（クエスチョンマーク）でプレースホルダー化されている。
- **Example (inferring a result) / 例（結果の推論）：**
  ```
  QUERY: Action: Drop tgt:Glass.Cup src:Table dst:Stone.Floor -> Result: ?
  ```
  EN — (A glass cup was dropped onto a stone floor. What is the result? → The model outputs `Break agt:It` or the like.)
  JA — （ガラスのコップを石の床に落とした。結果はどうなるか？ → モデルは `Break agt:It` などを出力する）
- **Example (abductive inference, working back to the cause) / 例（アブダクション推論 / 原因の逆算）：**
  ```
  QUERY: Action: ? -> Result: Become agt:Apple.Half count:2
  ```
  EN — (The apple became two halves. What action was performed just before? → The model outputs `Cut tgt:Apple` or the like.)
  JA — （リンゴが2つの半分になった。直前に行われたアクションは何か？ → モデルは `Cut tgt:Apple` などを出力する）

## 7. Formal Definition of the Syntax (Simplified EBNF) / 構文の形式定義（簡易EBNF）

**EN** — To secure the rigour of the syntactic structure defined in this chapter, the formal grammar (in EBNF) that serves as the reference for parser development is specified below.

**JA** — 本章で定めた構文構造の厳密性を担保するため、パーサー開発の基準となる形式文法（EBNF記法）を以下に規定する。

```
Statement       ::= Prefix ":" EventSequence
Prefix          ::= "RULE" | "FACT" | "HYPO" | "QUERY"

EventSequence   ::= Event ( Connector Event )*
Connector       ::= "->" | "!>" | "&>"

Event           ::= Condition? PredicateClause
Condition       ::= "when:" "(" EventSequence ")"

PredicateClause ::= ( "Action:" | "Result:" | "State:" )? Verb ( Slot )*
Verb            ::= Identifier | "?"

Slot            ::= SlotKey ":" SlotValue
SlotKey         ::= "agt" | "tgt" | "tool" | "src" | "dst" | "loc"
                  | "tense" | "asp" | "mod" | "iter" | "freq"
                  | "goal" | "reason" | "count" | "is"

SlotValue       ::= ConceptExpression
                  | "(" EventSequence ")"
                  | "?"
```

**EN** — _(Note: the internal structure of `ConceptExpression` — dot notation and morphological modification — is detailed in the next chapter.)_

**JA** — _(※ `ConceptExpression` の内部構造、すなわちドット記法や形態素修飾の仕様については次章で詳述する)_

## 8. Summary of Chapter 2 / 第2章の総括

**EN** — This chapter defined the syntax and case system that form Framingo's skeleton.

1. **It dismantled subject-centred natural-language syntax and introduced a flat, predicate-centred Neo-Davidsonian case frame.**
2. **Case slots are order-invariant, and explicit tags (`agt:`, `tgt:` etc.) minimize the load on self-attention.**
3. **Event descriptions permit any slot to drop out, crossing seamlessly from concrete individual episodes to maximally abstracted universal physical laws.**
4. **TAM, repetition and frequency are treated not as verb inflection but as independent slots, eradicating irregular forms entirely.**
5. **Sentence-initial prefixes (`RULE`, `FACT`, `HYPO`, `QUERY`) uniquely control the model's reasoning mode (deduction, memory, planning, back-inference).**

The next chapter (chapter 3) proceeds to design the conceptual data poured into these case frames: "dot notation", which governs the preservation and destruction of attributes; the "functional suffix system", which prevents vocabulary explosion; and logical "determiners".

**JA** — 本章では、Framingoの骨格となる統語論と格システムを定義した。

1. **主語中心の自然言語統語論を解体し、述語を中心とするフラットなネオ・デイヴィドソン流格フレームを導入した。**
2. **格スロットは順序不変（Order-Invariant）であり、明示的なタグ（`agt:`, `tgt:` 等）によって自己注意機構の負荷を最小化する。**
3. **事象の記述は任意のスロット脱落を許容し、個別具体のエピソードから極限まで抽象化された物理普遍則までをシームレスに横断する。**
4. **TAMや回数・頻度も動詞の変形ではなく独立したスロットとして扱い、不規則変化を完全に撲滅した。**
5. **文頭プリフィックス（`RULE`, `FACT`, `HYPO`, `QUERY`）によって、モデルの推論モード（演繹、記憶、計画、逆算）を一意に制御する。**

次章（第3章）では、この格フレームの中に流し込まれる概念データそのものの設計――すなわち、属性の保存と破壊を司る「ドット記法」、語彙爆発を防ぐ「機能接尾辞システム」、そして論理的「限定詞」の仕様策定へと進む。

---

# Chapter 3: Concept Composition, Morphology and Ontology / 第3章：概念合成・形態論・オントロジー

*Framingo Design Specification and Development Charter / Framingo 設計仕様・開発憲章*

## 1. The Foundation of Concept Representation: Composition by Dot Notation / 概念表現の根幹：ドット記法（Dot Notation）による概念合成

**EN** — How the entities and concepts assigned to case frames (slots) are represented is a crucial factor that determines both the language's expressive power and the model's training efficiency. In natural language, a variety of complex syntactic rules — "pre-nominal adjectives", "post-modification by relative clauses", "compound noun formation" — coexist to express modification, and the boundaries of combination between words are extremely vague.

This language (Framingo) unifies all derivation and modification of entities and concepts into a single, uniform mechanism: dot notation.

**JA** — 格フレーム（スロット）に代入される実体や概念をどのように表現するかは、言語の表現力とモデルの学習効率を決定づける極めて重要な要素である。自然言語では、修飾関係を表現するために「形容詞の前置」「関係代名詞節による後置修飾」「複合名詞の形成」など多様かつ複雑な統語規則が混在し、単語間の結合境界が極めて曖昧である。

本言語（Framingo）では、すべての実体および概念の派生・修飾をドット記法（Dot Notation）という単一かつ統一的なメカニズムに統合する。

```
[Determiner].[Modifier...].[BaseEntity].[Part/Aspect]
```

### 1.1 Unifying Narrowing (Intersection) and Mereology / 概念の絞り込み（Intersection）と部分論（Mereology）の統合

**EN** — The dot `.` is an all-purpose composition operator combining the properties of property reference (member access) in programming languages, subtyping in type systems, and intersection in formal semantics.

- **Narrowing by attribute (filtering / subtyping):**
  - `Apple` (base concept: the set of apples)
  - `Red.Apple` (restricted by the attribute red: red apples)
  - `Sweet.Red.Apple` (stacking the further attribute sweet: sweet red apples)
- **Mereological derivation (part–whole):**
  - `Apple.Slice` (a thin piece cut from an apple)
  - `Apple.Half` (a piece of an apple divided in two)
  - `Apple.Core` (the core of an apple)
  - `Apple.Skin` (the skin of an apple)

These are expressed as chains of one and the same dot combination.

What in natural language becomes a complex noun phrase with a prepositional phrase, "a slice of sweet red apple", is completed in Framingo as the following single token sequence (chunk).

**JA** — ドット `.` は、プログラミング言語におけるオブジェクトのプロパティ参照（メンバアクセス）と、型システムにおける部分型（Subtyping）、そして形式意味論における交差（Intersection）の性質を兼ね備えた万能の合成演算子である。

- **属性による絞り込み（Filtering / Subtyping）：**
  - `Apple`（基底概念：リンゴの集合）
  - `Red.Apple`（赤という属性による制限：赤いリンゴ）
  - `Sweet.Red.Apple`（さらに甘いという属性をスタック：甘くて赤いリンゴ）
- **部分論的派生（Mereology / Part-Whole）：**
  - `Apple.Slice`（リンゴから切り出された薄片）
  - `Apple.Half`（リンゴを2等分した片）
  - `Apple.Core`（リンゴの芯）
  - `Apple.Skin`（リンゴの皮）

これらは同一のドット結合の鎖として表現される。

自然言語では「A slice of sweet red apple」という前置詞句を伴う複雑な名詞句になるものが、Framingoでは以下の単一のトークン列（チャンク）として完結する。

```
Sweet.Red.Apple.Slice
```

### 1.2 The Left-to-Right Rule of Concept Hierarchy / 概念階層の左から右への展開則

**EN** — The order of elements in dot notation follows, as its basic rule, the size of cognitive scope, flowing "from the outer context (broad) to the inner part (local)".

1. **Determiner:** where in the world, and over what range, the concept points (e.g. `Every`, `This`)
2. **Intrinsic and extrinsic attributes (modifiers):** colour, material, temperature, character (e.g. `Hot`, `Red`, `Break-prone`)
3. **Base entity:** the physical core object (e.g. `Apple`, `Glass`, `Door`)
4. **Derivation, part (part / aspect):** a region or shape cut out of the whole (e.g. `Piece`, `Slice`, `Handle`)

By this rule, the model's self-attention can perform very low-load sequential processing: fix the scope at the left end, read material and character in the middle, and identify the final physical entity and shape at the right end.

**JA** — ドット記法における要素の並び順は、認知的なスコープの大きさに従って「外側の文脈（広範囲）から内側の部分（局所）」へと流れる規則を基本とする。

1. **限定詞（Determiner）：** その概念が世界のどこをどの範囲で指しているか（例：`Every`, `This`）
2. **内在的・外在的属性（Modifiers）：** 色、材質、温度、性質（例：`Hot`, `Red`, `Break-prone`）
3. **基底実体（Base Entity）：** 物理的な核となるオブジェクト（例：`Apple`, `Glass`, `Door`）
4. **派生・部位（Part / Aspect）：** 全体から切り出された領域、形状（例：`Piece`, `Slice`, `Handle`）

この規則により、モデルの自己注意機構（Self-Attention）は、左端でスコープを特定し、中央で素材や性質を読み解き、右端で最終的な物理的実体・形状を同定するという、極めて負荷の低い順次処理を行うことができる。

## 2. Preservation of Attributes (Invariance) and Their Destruction (Decay) / 属性の保存則（Invariance）と破壊則（Decay）

**EN** — Dot notation shows its true worth most in "tracking physical attributes" across causal transitions (`Action` $\rightarrow$ `Result`).

When an event applies external force to an object, some properties are maintained and some are lost. Natural language must read this implicitly from context; in Framingo, the succession of dot-notation chains itself functions as a physics simulator.

**JA** — ドット記法の真価が最も発揮されるのは、因果遷移（`Action` $\rightarrow$ `Result`）における「物理的属性の追跡」である。

事象によって物体に外力が加わったとき、維持される性質と失われる性質が存在する。自然言語ではこれを文脈から暗黙に読み取らなければならないが、Framingoではドット記法の連鎖の変遷そのものが物理シミュレータとして機能する。

### 2.1 Preservation of Material and Intrinsic Attributes (Invariance) / 物質的・内在的属性の保存（Invariance）

**EN** — Even under physical operations such as cutting or moving, the object's "intrinsic properties" — its essential material, taste, colour, composition and so on — are preserved.

**JA** — 切断や移動などの物理的操作を受けても、対象の本質的な材質、味、色、組成などの「内在的プロパティ（Intrinsic Properties）」は保存される。

```
Action: Cut tgt:Sweet.Red.Apple tool:Knife
-> Result: Become agt:Sweet.Red.Apple.Slice
```

**EN** — In this sentence, the modifiers `Sweet` and `Red` are inherited unchanged by `Apple.Slice` on the result side (`Result`).

Across a large corpus, the model naturally learns the intuition of physical invariance — "for the action `Cut`, prefixes denoting `Color` or `Taste` are copied (preserved) to the right-hand side" — from string-level pattern matching and the continuity of vector space.

**JA** — この文において、`Sweet` と `Red` という修飾子は結果側（`Result`）の `Apple.Slice` にそのまま継承されている。

モデルは大量のコーパスを通じて、「`Cut` というアクションに対して、`Color` や `Taste` を表すプレフィックスはそのまま右辺へコピーされる（保存される）」という物理的不変性の直感を、文字列レベルのパターンマッチングとベクトル空間の連続性から自然に学習する。

### 2.2 Destruction and Mutation of Shape and Structural Attributes (Decay / Mutation) / 形状的・構造的属性の破壊・変容（Decay / Mutation）

**EN** — On the other hand, "structural properties" such as the object's overall size, outline and closedness are nullified or mutated by actions such as cutting and breaking.

**JA** — 一方で、物体の全体サイズ、外形、閉鎖性といった「構造的プロパティ（Extrinsic / Structural Properties）」は、切断や破壊などのアクションによって無効化または変異する。

- **Loss of shape / 形状の喪失：**
  ```
  // Cutting a Round apple: it is no longer round, so Round drops out
  // 丸い（Round）リンゴを切ると、もはや丸くはないため Round は脱落する
  Action: Cut tgt:Round.Apple tool:Knife
  -> Result: Become agt:Apple.Half
  ```
- **Reduction in size / サイズの縮減：**
  ```
  // Cutting a Big loaf yields Small slices
  // 大きな（Big）パンを切ると、小さな（Small）スライスになる
  Action: Cut tgt:Big.Bread tool:Knife
  -> Result: Become agt:Small.Bread.Slice count:Many
  ```
- **Breakdown of wholeness / 完全性の破綻：**
  ```
  // Breaking a Whole watermelon: Whole disappears entirely
  // まるごと（Whole）のスイカを割ると、Whole は完全に消失する
  Action: Break tgt:Whole.Watermelon
  -> Result: Become agt:Watermelon.Piece
  ```

**EN** — Humans need not write vast exception rules such as "cutting axiom: when an object is cut, its roundness is not retained." Simply by being shown, again and again in the corpus, instances where `Round` has dropped out after a `Round.Apple` is cut, the model's neural network automatically discriminates, as weights in latent space, "which attributes are fragile (non-conservative) under an action and which are robust (conservative)."

**JA** — 人間が「切断公理：対象が切断された場合、その真円度は保持されない」といった膨大な例外ルールを記述する必要はない。単にコーパスの中で `Round.Apple` が切られた後に `Round` が脱落している実例を見せ続けるだけで、モデルのニューラルネットワークは「どの属性がアクションに対して脆弱（Non-conservative）であり、どの属性が頑健（Conservative）であるか」を潜在空間の重みとして自動的に峻別する。

## 3. The Morphological System: Verb Roots and the "Three Functional Suffixes" / 形態論システム：動詞語根と「3大機能接尾辞」

**EN** — A fatal defect of natural language is the disorderly proliferation of vocabulary that accompanies differentiation into parts of speech. In English, for example, the three concepts "break", "fragile" and "broken" are etymologically and morphologically discontinuous, and a model must learn each as a separate embedding vector.

In Framingo, the core of a concept is unified **into the "verb" (an action that brings about an event or change)**, and to it the **regular "three functional suffixes"** are attached with a hyphen — generating adjectival and state expressions directly tied to causation while fully suppressing vocabulary explosion.

**JA** — 自然言語の致命的な欠陥は、品詞の分化に伴う語彙の無秩序な増殖である。例えば英語において、「壊す（Break）」「壊れやすい（Fragile）」「壊れた（Broken）」という3つの概念は、語源的・形態論的に不連続であり、モデルはそれぞれを別個の埋め込みベクトルとして学習しなければならない。

Framingoでは、概念の核を「動詞（事象・変化を引き起こすアクション）」**に一本化し、そこに規則的な**「3大機能接尾辞」をハイフン結合することで、語彙爆発を完全に抑え込みながら因果と直結した形容詞・状態表現を生成する。

```
[BaseVerb]-[FunctionalSuffix]
```

### 3.1 Definition of the Three Functional Suffixes / 3大機能接尾辞の定義

| **Suffix / 接尾辞** | **Function / 機能名** | **Physical and causal definition / 物理・因果的定義** | **Derived forms / 派生例** | **Natural language replaced / 置換される自然言語** |
| ------------ | ------------------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| **`-able`**  | Passive affordance / 受動可能（Passive Affordance） | The property of admitting that state or change under external force / 外力を受けてその状態・変化を許容し得る性質 | `Break-able`<br>`Eat-able`<br>`Move-able`<br>`Cut-able` | Fragile<br>Edible<br>Portable<br>Divisible |
| **`-prone`** | Propensity, vulnerability / 能動傾向・脆弱性（Propensity / Risk） | A physical bias toward undergoing that change spontaneously or easily, under stimulus or with time / 刺激や時間の経過によって、自発的または容易にその変化を起こしやすい物理的偏り | `Break-prone`<br>`Slip-prone`<br>`Rust-prone`<br>`Fall-prone` | Brittle<br>Slippery<br>Corrosive<br>Unstable |
| **`-ed`**    | Resultative state / 受動完了（Resultative State） | The action has been completed and its result state has settled / そのアクションが完了し、結果状態が定着していること | `Break-ed`<br>`Lock-ed`<br>`Cook-ed`<br>`Open-ed` | Broken<br>Locked<br>Cooked<br>Open |

### 3.2 The Physical Difference Between `-prone` and `-able` / `-prone` と `-able` の物理的差異

**EN** — "Possibility (`-able`)" and "propensity, vulnerability (`-prone`)", often confused in natural language, are cleanly separated.

- **`Break-able` (breakability):**
  A diamond is very hard, but it can be broken by applying strong force along the proper cleavage plane. That is, it is "possible to break (`Break-able`)".
- **`Break-prone` (vulnerability):**
  A thin glass cup shatters if dropped by the slightest slip of the hand. That is, it "has a strong tendency, a risk, of breaking (`Break-prone`)".

This distinction models sensitivity in simulations of the physical world with great accuracy.

**JA** — 自然言語では混同されがちな「可能性（`-able`）」と「傾向・脆弱性（`-prone`）」を明確に切り離す。

- **`Break-able`（可破壊性）：**
  ダイヤモンドは非常に硬いが、適切な劈開（へきかい）面に強い力を加えれば壊すことができる。すなわち「壊すことが可能（`Break-able`）」である。
- **`Break-prone`（脆弱性）：**
  薄いガラスのコップは、少し手元が狂って落としただけで粉々に割れる。すなわち「極めて壊れやすい傾向・リスクを持つ（`Break-prone`）」である。

この区別により、物理世界のシミュレーションにおける感度（Sensitivity）が極めて正確にモデル化される。

```
// A Break-prone thing becomes Break-ed even from a weak impact (Drop)
// 壊れやすい（Break-prone）物は、弱い衝撃（Drop）でも壊れた状態（Break-ed）になる
RULE: Action: Drop tgt:Break-prone.Thing -> Result: Become agt:Break-ed.Thing

// A Break-able thing becomes Break-ed only under a strong blow (Heavy.Hit)
// 壊すことが可能（Break-able）な物は、強い打撃（Heavy.Hit）によって初めて壊れた状態になる
RULE: Action: Heavy.Hit tgt:Break-able.Thing -> Result: Become agt:Break-ed.Thing
```

**EN** — With the root `Break` as the axis, "disposition (`-prone`)", "action (`Break`)" and "result (`-ed`)" form a beautiful threefold loop.

**JA** — 語根 `Break` を軸として、「素質（`-prone`）」「アクション（`Break`）」「結果（`-ed`）」が美しい三位一体のループを形成する。

### 3.3 The State-Inverting, Negating Prefix `!` / 状態の反転・否定プレフィックス `!`

**EN** — Inheriting the idea of Esperanto's prefix `mal-` (complete inversion), negation or cancellation of a state is expressed not by coining new words but by prefixing with the exclamation mark `!` (or `un-`).

- `!Lock-ed.Door` (a door that is not locked = unlocked)
- `!Eat-able.Mushroom` (a mushroom not fit to eat = inedible / poisonous)
- `!Clean.Floor` (a floor that is not clean = dirty)

This eliminates any need to memorize antonyms and secures the symmetry of the concept space.

**JA** — エスペラントの接頭辞 `mal-`（完全反転）の思想を継承し、状態の否定や取り消しは単語を新設せず、感嘆符 `!`（または `un-`）によるプレフィックス修飾で表現する。

- `!Lock-ed.Door`（施錠されていないドア ＝ Unlocked）
- `!Eat-able.Mushroom`（食用に適さないキノコ ＝ Inedible / Poisonous）
- `!Clean.Floor`（清潔ではない床 ＝ Dirty）

これにより、不要な対義語の暗記を一切排除し、概念空間の対称性を担保する。

## 4. The Determiner System (Determiners / Quantification) / 限定詞システム（Determiners / Quantification）

**EN** — Determiners, which fix the range of reference of a concept, stand at the leftmost end of the dot chain. Abolishing the context-dependent, phonological noise of English `a` and `the`, this specification defines **five determiners** with purely the functions of **logical quantification** and **discourse reference**.

**JA** — 概念の参照範囲を規定する限定詞は、ドット結合の最左端に位置する。英語の `a` や `the` といった文脈依存的で音韻的なノイズを全廃し、純粋に**論理的量化（Quantification）**と**談話参照（Reference）**の機能を持つ**5大限定詞**を規定する。

```
[Determiner].[ConceptExpression]
```

### 4.1 Definition of the Five Determiners / 5大限定詞の定義

| **Determiner / 限定詞** | **Logical symbol / 論理的記号** | **Function / 機能** | **Example / 構文例** | **Meaning / 意味** |
| ------------ | ------------------------- | -------------------------------- | ------------- | ---------------------------------- |
| **`Every.`** | $\forall$ (universal quantification / 全称量化) | The whole set, without exception / 例外なき全集合 | `Every.Glass` | All glass (used in universal laws) / すべてのガラス（普遍則で使用） |
| **`Any.`**   | Arbitrary / 任意 | One chosen arbitrarily from the set / 集合から任意に選ばれた1つ | `Any.Knife` | Some knife (any will do) / （どれでもよいから）何らかのナイフ |
| **`Some.`**  | $\exists$ (existential quantification / 存在量化) | An unspecified quantity or subset / 不特定の数量・部分集合 | `Some.Water` | Some water; an unspecified group of apples / いくらかの水、不特定のリンゴ群 |
| **`This.`**  | Deictic / 直指示 | A particular individual in the current time, place or context / 現在の時空・文脈における特定個体 | `This.Key` | This key (here, now) / （今ここにある）この鍵 |
| **`No.`**    | $\neg\exists$ (negative quantification / 否定量化) | The empty set (none at all) / 空集合（皆無） | `No.Human` | Not a single human exists / 1人も人間が存在しない |

### 4.2 Writing Laws (RULE) with Universal Quantification (Every) / 全称量化（Every）による法則（RULE）の記述

**EN** — Combining the `RULE:` prefix with the `Every.` determiner gives the model a strong signal: "this is not an individual case but a law of the universe that admits no exception."

**JA** — `RULE:` プリフィックスと `Every.` 限定詞を組み合わせることで、モデルに対して「これは個別事例ではなく、例外を認めない宇宙の法則である」という強いシグナルを与える。

```
RULE: Action: Drop tgt:Every.Break-prone.Thing -> Result: Become agt:It.Piece
```

**EN** — A variable bound by `Every.` on the left-hand side safely carries its binding over to the right-hand side through the anaphoric pronoun `It`, described below.

**JA** — 左辺で `Every.` によって束縛された変数は、後述する照応代名詞 `It` を通じて右辺へ安全に束縛を引き継ぐ。

## 5. The Anaphora System and Reference Resolution / 照応システムと参照解決（Anaphora & Reference）

**EN** — "Anaphoric pronouns", the greatest breeding ground of ambiguity in natural language, are redefined in Framingo as a very clear reference system.

**JA** — 自然言語における最大の曖昧性の温床である「照応代名詞（Pronouns）」を、Framingoでは極めて明快な参照システムとして再定義する。

### 5.1 `It` as the Default / 原則としての `It`

**EN** — To refer to the central object acted upon (`tgt:`) in context or in the immediately preceding event, the **unmarked `It`** is used as a rule.

**JA** — 文脈内、あるいは直前の事象において作用を受けた中心的な対象（`tgt:`）を参照する場合、原則として**無標の `It`** を用いる。

```
FACT: Action: Cut tgt:Apple tool:Knife -> Result: Become agt:It.Slice
```

**EN** — In a self-evident context where only one object exists, there is no need to write the noun twice. `It` functions as a pointer directly indicating the immediately preceding principal argument.

**JA** — 対象が1つしか存在しない自明な文脈において、名詞を重複記述する必要はない。`It` は直前の主要引数を直接指し示すポインタとして機能する。

**EN** — Where nothing has yet been made the topic and the preceding event has no `tgt:`, `It` names its `agt:` instead. An event that *does* have a target leaves the topic where it was, so `Cut … -> Become agt:It.Slice -> Deform tgt:It` still deforms the thing that was cut. The case that forces the fallback is a chain, where one result becomes the premise of the next:

```
RULE: Action: Become agt:Every.Piece.Thing -> Result: Become agt:It.Swept
```

A division is written `Become agt:It.Slice` (chapter 3 §2) and so carries no target at all. Without the fallback, a rule keyed on such an event has no way to name the thing it has just been told about, and results cannot be chained. What would otherwise say it — `It<X>.Swept` — the grammar cannot write, because a concept's index follows its whole dot chain and nothing may come after it.

**JA** — まだ何も主題になっておらず、かつ直前の事象が `tgt:` を持たない場合、`It` はその `agt:` を指す。`tgt:` を**持つ**事象は主題をそのままにするので、`Cut … -> Become agt:It.Slice -> Deform tgt:It` は依然として切られた物を変形させる。この退避を要求するのは**連鎖**の場合であり、一つの結果が次の前提になるときである。

```
RULE: Action: Become agt:Every.Piece.Thing -> Result: Become agt:It.Swept
```

分割は `Become agt:It.Slice` と書かれ（第3章 §2）、対象を一切持たない。この退避がなければ、そうした事象を前提とする規則は、たった今告げられたものを名指す手段を持たず、**結果を連鎖させられない。** それを言うはずの `It<X>.Swept` は文法が書けない。概念の添字は点連鎖全体の後に来るため、その後ろには何も置けないからである。

### 5.2 Crossing Multiple Objects and Indexed Pronouns / 複数対象の交錯とインデックス付き代名詞（Indexed Pronouns）

**EN** — When several objects appear at once and interact, natural language's "it" and "they" produce fatal collisions of referent (the Winograd Schema problem).

To solve this, Framingo introduces **index pointers in angle brackets: `<A>`, `<B>`, `<C>`...**

**JA** — 複数のオブジェクトが同時に登場し、相互に作用する場合、自然言語の「it」や「they」では致命的な指示対象の衝突（Winograd Schema問題）が発生する。

Framingoでは、この問題を解決するために**山括弧によるインデックスポインタ `<A>`, `<B>`, `<C>`...** を導入する。

```
// Put apple <B> into box <A>
// 箱<A>の中にリンゴ<B>を入れる
Action: Put tgt:Apple<B> dst:Box<A> -> State tgt:It<B> loc:Inside.It<A>
```

**EN** —

- `Apple<B>`, declared on the left-hand side, is strictly bound to `It<B>` on the right-hand side.
- `Box<A>`, declared on the left-hand side, is strictly bound to `It<A>` on the right-hand side.

**JA** —

- 左辺で宣言された `Apple<B>` は、右辺の `It<B>` と厳密に紐づく。
- 左辺で宣言された `Box<A>` は、右辺の `It<A>` と厳密に紐づく。

#### Engineering Benefits for the Attention Mechanism / アテンション機構における工学的メリット

**EN** — This index notation provides a powerful shortcut to the Transformer's attention layers.

The model need not guess probabilistically, from the meaning of the whole context, "which is being put in, and which is the container"; it can concentrate its attention heads' weight directly, 100%, on the identical token label `<B>`. This minimizes the computational cost of inference and brings mix-ups of referent to zero.

**JA** — このインデックス表記は、Transformerのアテンション層に対して強力なショートカットを提供する。

モデルは文脈全体の意味から「どちらが入れられ、どちらが入れる側か」を確率的に推測する必要がなく、`<B>` という同一のトークンラベルに対してアテンションヘッドの重みを直接100%集中させることができる。これにより、推論の計算コストを最小化し、指示対象の取り違え事故をゼロにする。

## 6. The Dual Representation of Results / 結果表現の二重性（Dual Representation of Results）

**EN** — Framingo does not force a single form of representation on the right-hand side of a causal relation (`Result:`). According to the level of abstraction at which an event is grasped, it lets **the following two styles of representation stand side by side as equivalent.**

**JA** — Framingoは、因果関係の右辺（`Result:`）において、単一の表現形式を強制しない。事象を捉える抽象度のレベルに応じて、以下の**2つの表現スタイルを等価なものとして両立・共存**させる。

### 6.1 The Event / Verb View (Phenomenological View) / イベント・動詞視点（Phenomenological View）

**EN** — A style that describes the physical phenomenon or action itself directly as a predicate.

**JA** — 物理的な現象・動作そのものを述語として直接記述するスタイル。

```
Action: Drop tgt:Glass -> Break agt:It
```

- **Advantages / 利点：**
  EN — Intuitive; captures directly what happened (the occurrence of the verb). Suited to action games and to event-driven robot architectures.
  JA — 直感的であり、何が起きたか（動詞の生起）をストレートに捉える。アクションゲームやロボットのイベント駆動型アーキテクチャに適している。

### 6.2 The State-Shift / Mereological View / 状態変化・部分論視点（Mereological / State Shift View）

**EN** — A style that uses the general meta-verb `Become` to track, precisely and in dot notation, transitions in an entity's shape and attributes.

**JA** — 汎用メタ動詞 `Become` を用い、実体の形状や属性の遷移をドット記法で精緻に追跡するスタイル。

```
Action: Drop tgt:Glass -> Result: Become agt:It.Piece count:Many
```

- **Advantages / 利点：**
  EN — Tracks object identity and conservation laws strictly. Suited to physics simulators, inventory management and crafting tasks.
  JA — オブジェクトの同一性（Identity）と保存則を厳密に追跡する。物理シミュレータや在庫管理、クラフト系タスクに適している。

### 6.3 Deepening Intelligence by Learning Both Representations in Parallel / 表現の並行学習による知性の深化

**EN** — When generating the dataset, both styles are mixed at a suitable ratio (e.g. 50% each) for the same causal relation.

**JA** — データセットを生成する際、同一の因果関係に対してこの両方のスタイルを適切な比率（例：50%ずつ）で混在させて学習させる。

$$\text{Action: Drop tgt:Glass} \implies \begin{cases} \text{Break agt:It} \\ \text{Result: Become agt:It.Piece} \end{cases}$$

**EN** — By experiencing this duality (paraphrase), in the model's internal representation "the event `Break(It)`" and "the state transition `Become(It.Piece)`" **come to overlap almost completely in high-dimensional space (cosine similarity $\to 1.0$).**

The model thereby acquires, without being bound by "the surface form of words", **a deeper, three-dimensional intuition of the world model that integrates "phenomenon" and "change of matter" from multiple angles.**

**JA** — この二重性（Paraphrase）を経験することで、モデルの内部表現では「`Break(It)` という事象」と「`Become(It.Piece)` という状態遷移」が**高次元空間上でほぼ完全に重なり合う（コサイン類似度 $\to 1.0$）**。

これにより、モデルは「言葉の表面的な形」に囚われることなく、**「現象」と「物質の変化」を多角的に統合した、より深く立体的な世界モデルの直感**を獲得する。

## 7. Summary of Chapter 3 / 第3章の総括

**EN** — This chapter established the ontological architecture governing Framingo's vocabulary and semantic representation.

1. **Dot notation (`Attr.Base.Part`) unifies intersective adjectival modification and mereological derivation in a single mechanism.**
2. **The "conservation laws (colour, taste etc.)" and "destruction laws (shape, wholeness etc.)" of attributes under physical action became intuitively expressible at the level of syntax.**
3. **Centring on verb roots, the three functional suffixes `-able` (possibility), `-prone` (propensity) and `-ed` (result state) fully suppress vocabulary explosion.**
4. **Five logical determiners — `Every`, `Any`, `Some`, `This`, `No` — were introduced, abolishing the junk of natural-language articles.**
5. **The anaphoric pronoun `It` and the indices `<A>`, `<B>` bring ambiguity of reference mathematically to zero.**
6. **The design admits a duality of "event view" and "state-transition view" in representing results, encouraging multi-angle conceptual understanding in the model.**

The next chapter (chapter 4) proceeds to specify the dynamic combination system — the last pieces of logic and physics: "causal connectives (`->` and `!>`)", "preconditions (`when:`)" and "counterfactual reasoning".

**JA** — 本章では、Framingoの語彙と意味表現を司るオントロジーのアーキテクチャを確立した。

1. **ドット記法（`Attr.Base.Part`）により、形容詞の交差修飾と部分論的派生を単一のメカニズムで統合した。**
2. **物理アクションに伴う属性の「保存則（色・味など）」と「破壊則（形状・完全性など）」を構文レベルで直感的に表現可能にした。**
3. **動詞語根を中心とし、`-able`（可能）、`-prone`（傾向）、`-ed`（結果状態）の3大機能接尾辞によって、語彙の爆発を完全に抑制した。**
4. **`Every`, `Any`, `Some`, `This`, `No` の5大論理限定詞を導入し、自然言語の冠詞のゴミを全廃した。**
5. **照応代名詞 `It` とインデックス `<A>`, `<B>` により、指示対象の曖昧性を数学的にゼロにした。**
6. **結果の表現として「イベント視点」と「状態遷移視点」の二重性を許容し、モデルに多角的な概念理解を促す設計とした。**

次章（第4章）では、論理と物理の最後のピースである「因果結合子（`->` と `!>`）」「前提条件（`when:`）」「反事実推論」の動的結合システムの仕様策定へと進む。

---

# Chapter 4: Causal Connection, Conditional Branching and the Dynamic Reasoning System / 第4章：因果結合・条件分岐・動的推論システム

*Framingo Design Specification and Development Charter / Framingo 設計仕様・開発憲章*

## 1. The Mechanics of the Connectives: Occurrence (`->`), Prevention (`!>`) and Simultaneity (`&>`) / 結合子の力学：生起（`->`）・阻止（`!>`）・同時（`&>`）

**EN** — Complex-sentence structures in natural language (because, therefore, so, but, although, etc.) intricately mix the speaker's emotional emphasis with logical relations, and bring very high polysemy to the task of extracting the direction of causation by machine. In the sentence "I pushed the door but it did not open", for example, natural language uses an adversative conjunction (but) to express the speaker's disappointment or surprise; yet the mechanical fact occurring in the physical world is an objective causal misfire: "although external force (Push) was applied, the state transition (Open) was prevented."

This language (Framingo) reduces the dynamic temporal development and mechanical linkage between events to just two orthogonal directed connectors.

**JA** — 自然言語における複文構造（Because, Therefore, So, But, Although など）は、発話者の感情的強調や論理的関係が複雑に交錯しており、機械が因果の方向性を抽出する上で極めて高い多義性をもたらす。例えば、「ドアを押したが開かなかった」という文において、自然言語は「逆接の接続詞（but）」を用いて話者の落胆や意外性を表現するが、物理世界で生起している力学的事実は「外力（Push）が加えられたにもかかわらず、状態遷移（Open）が阻止された」という客観的な因果の不発である。

本言語（Framingo）では、事象間の動的な時間発展および力学的結びつきを、2つの直交する有向結合子（Directed Connectors）のみに還元する。

```
[Cause_Event] -> [Effect_Event]   // Positive causation / 因果の生起（Positive Causation）
[Cause_Event] !> [Prevented_Event] // Negative causation, prevention / 因果の阻止・不発（Negative Causation / Prevention）
[Result_Event] &> [Result_Event]  // No causation: both hold at once / 因果なし。同時に成立（Simultaneity）
```

**EN** — The reduction to two stands: *causal* linkage between events is `->`
and `!>`, and there is no third direction for a cause to take. `&>` is not a
third causal connective. It is the case the two leave out — two events between
which there is no causal linkage at all — and it is neither directed nor
causal. Section 1.3 states why the language cannot do without it.

**JA** — 二つへの還元は保たれる。事象間の**因果的**な結びつきは `->` と `!>` で
あり、因果が取りうる第三の向きは存在しない。`&>` は第三の因果結合子ではない。
**二つが取りこぼしていた場合** —— 事象の間に因果的な結びつきが一切ない場合 ——
であり、有向でも因果的でもない。1.3節がなぜこれなしでは済まないかを述べる。

### 1.1 The Occurrence Connective (`->`): Necessity of State Transition / 生起結合子（`->`）：状態遷移の必然性

**EN** — The arrow `->` indicates that "the holding of the preceding event (left-hand side) directly brought about, temporally and mechanically, the following event (right-hand side)."

**JA** — 矢印 `->` は、「先行事象（左辺）の成立によって、後続事象（右辺）が時間的・力学的に直接引き起こされた」ことを示す。

```
Action: Drop tgt:Glass -> Break agt:It
```

**EN** — This connective does not mean mere temporal succession (A happened, and then B happened). It declares that the left-hand action is the direct mechanical driving force (causal mechanism) that brings about the right-hand result. By observing this connection in quantity, the model acquires the ability to distinguish temporal precedence (the post hoc ergo propter hoc fallacy) from true causation.

**JA** — この結合子は、単なる時間的継起（Aが起きて、その後にBが起きた）を意味しない。左辺のアクションが右辺の結果をもたらす直接の力学的推進力（Causal Mechanism）であることを宣言する。この結合を大量に観測することで、モデルは時間的な前後関係（Post hoc ergo propter hoc の誤謬）と真の因果関係を峻別する能力を獲得する。

### 1.2 The Prevention / Misfire Connective (`!>`): Modelling Counterfactual Prevention and Protection / 阻止・不発結合子（`!>`）：反事実的阻止と防護のモデリング

**EN** — The symbol `!>` expresses that "although the preceding event (left-hand side) occurred, the following event (right-hand side) that would normally have been brought about was completely prevented, or misfired, owing to some constraining condition or protective barrier."

**JA** — 記号 `!>` は、「先行事象（左辺）が発生したにもかかわらず、何らかの拘束条件や防護壁によって、通常であれば引き起こされるはずであった後続事象（右辺）が完全に阻止された、あるいは不発に終わった」ことを表す。

```
Action: Push agt:John tgt:Locked.Door !> Result: Become agt:Open.Door
```

**EN** — Introducing this symbol is decisive for building a world model.

In conventional symbolic AI and simple datasets, describing "what did not happen" was difficult. But for intelligence to survive and succeed at tasks in the physical world, it must learn explicitly "doing what prevents which result (protection, failure, interference)."

**JA** — この記号の導入は、世界モデルの構築において決定的な意味を持つ。

従来の記号AIや単純なデータセットでは、「起きなかったこと」を記述することは困難であった。しかし、知性が物理世界で生存し、作業を成功させるためには、「何を行うと、どの結果が阻まれるのか（防護、失敗、干渉）」を明示的に学習する必要がある。

- **Wearing a helmet / ヘルメットの着用：**
  ```
  Action: Fall tgt:Stone dst:Head.With.Helmet !> Hurt tgt:Human
  ```
- **Heat shielding by fire-proof material / 耐火素材の遮熱：**
  ```
  Action: Expose tgt:Fire-proof.Cloth tool:Fire !> Burn agt:It
  ```

**EN** — By introducing `!>`, the model can learn not only "the paths of successful causation" but also "the boundaries of blocked causation", as a clear contrast (contrastive learning).

**JA** — `!>` を導入することにより、モデルは「成功した因果のパス」だけでなく、「遮断された因果の境界線」を明確な対比（Contrastive Learning）として学習することが可能になる。

### 1.3 The Joint Connective (`&>`): Results That Hold at Once / 同時結合子（`&>`）：同時に成り立つ結果

**EN** — The symbol `&>` expresses that "both sides hold at one and the same
moment, and neither brought the other about."

```
Action: Carry agt:John tgt:Apple dst:Kitchen
  -> At tgt:Apple loc:Kitchen &> At tgt:John loc:Kitchen
```

John carried the apple to the kitchen. The apple is in the kitchen and John is
in the kitchen — one event seen from two sides. Neither arrival caused the
other.

Without this connective that sentence cannot be written down truthfully. `->`
is the only forward connective, and section 1.1 defines it as asserting that
the left event *directly brought about* the right one, so writing the pair with
`->` claims that the apple's arrival caused John's. **A generator with two
simultaneous consequences would have to state a falsehood.** That is not a
stylistic loss: a verifier that reads `->` as the specification defines it will
then enforce an order the world does not have, and reject a correct answer that
names the two arrivals the other way round.

The connective is **n-ary and unordered**: a chain joined by `&>` is one group
of events holding at once, and the order in which its members are written
carries nothing. A group is joined to what precedes it by the connective that
opens it, and every member of one group stands to every member of the next
exactly as that connective says.

Note what `&>` does *not* mean. It is not "and then", which is `->`; nor is it
mere conjunction of unrelated facts, which needs no connective because separate
statements already do it. It marks results of **one** cause that arrive
together.

> This is the reason chapter 2 makes slot order carry nothing within an event.
> The same freedom was missing *between* events, and a frame-based language
> cannot afford that asymmetry.

**JA** — 記号 `&>` は、「両辺が同一の瞬間に成り立ち、いずれも他方を引き起こして
いない」ことを表す。

```
Action: Carry agt:John tgt:Apple dst:Kitchen
  -> At tgt:Apple loc:Kitchen &> At tgt:John loc:Kitchen
```

ジョンはリンゴを台所へ運んだ。リンゴは台所にあり、ジョンも台所にいる —— 一つの
出来事を二つの側から見たものである。どちらの到着も他方を引き起こしていない。

この結合子なしには、この文を真として書き下せない。前向きの結合子は `->` しかなく、
1.1節はそれを「左辺が右辺を**直接引き起こした**」と定義している。したがってこの対を
`->` で書けば、「リンゴの到着がジョンの到着を引き起こした」と主張することになる。
**同時に生起する二つの帰結を持つ生成器は、偽を述べるほかなくなる。**

これは文体上の損失ではない。`->` を仕様通りに読む検証器は、そのとき**世界に存在
しない順序を強制し**、二つの到着を逆順に述べた正しい答えを却下する。

この結合子は **n 項かつ無順序**である。`&>` で連結された連鎖は、同時に成立する
事象の**一つの群**であり、その構成員をどの順に書くかは何も担わない。群は、それを
開いた結合子によって直前のものと結ばれ、ある群の各構成員は次の群の各構成員に
対して、その結合子が述べる通りの関係に立つ。

`&>` が意味**しない**ものを断っておく。「そして次に」ではない。それは `->` である。
無関係な事実の並置でもない。それには結合子は要らず、別々の文がすでにそれを行う。
これが標示するのは、**一つの**原因から同時に到達した結果である。

> 第2章が事象**内部**のスロット順序に何も担わせないのは、これと同じ理由による。
> 事象**間**にはその自由が欠けていた。フレームに基づく言語が、その非対称を
> 抱えたままでいることはできない。

---

## 2. Preconditions and Environmental Context: `when:` (Preconditions & Affordances) / 前提条件と環境コンテキスト：`when:`（Preconditions & Affordances）

**EN** — Causal relations do not fire unconditionally in a vacuum. For a physical law to act, there exist an environmental context filling the scene, a static state, or preconditions the object must meet.

In Framingo, the ground that holds prior to the left-hand side of an event is expressed with the **`when:(...)` construction.**

**JA** — 因果関係は、真空中において無条件で発火するものではない。物理法則が作用するためには、その場を満たす環境コンテキスト、静的な状態、あるいは対象が備えているべき前提条件（Preconditions）が存在する。

Framingoでは、事象の左辺に先行する成立基盤を **`when:(...)` 構文**によって表現する。

```
when:([State_Event]) [Action_Event] -> [Result_Event]
```

### 2.1 Strict Separation of Static State and Dynamic Action / 静的状態と動的アクションの厳密な分離

**EN** — Natural language tends to embed state and action in a single sentence, as in "walk through the open door". Framingo separates **"static environmental state (State)" from "dynamic external force (Action)"** clearly in its syntax.

**JA** — 自然言語では「開いているドアを通る」のように、状態とアクションが1つの文の中に埋め込まれがちである。Framingoでは、「静的な環境状態（State）」**と**「動的な外力（Action）」を構文上明確に分離する。

```
RULE: when:(State tgt:Door is:Open)
      Action: Pass agt:Human tgt:Door
      -> Result: At agt:Human dst:Room.Inside
```

**EN** —

- **Contents of `when:(...)`:** a slice of the invariant or quasi-static world just before the action begins (the precondition).
- **Contents of `Action:`:** the new force or motion the agent introduces into the world.

If the precondition is not met, the consequence of the action changes dramatically.

**JA** —

- **`when:(...)` の中身：** アクションが開始される直前の、不変または準静的な世界の切り出し（前提条件）。
- **`Action:` の中身：** 動作主が世界に対して投入した新たな力、運動。

もし前提条件が満たされていなければ、アクションの帰結は劇的に変化する。

```
RULE: when:(State tgt:Door is:Lock-ed)
      Action: Pass agt:Human tgt:Door
      !> Result: At agt:Human dst:Room.Inside
      -> Result: Bump agt:Human tgt:Door
```

**EN** — The difference in premise — "when the door is open" versus "when the door is locked" — decides the success or failure of the following action (passing through, or crashing into it). By repeatedly training on this branching structure, the model acquires an **intuition of affordance** that tightly links perception of the environment with action planning.

**JA** — 「ドアが開いているとき」と「ドアが施錠されているとき」という前提の差異が、続くアクションの成否（通過できるか、激突するか）を決定づける。この分岐構造を反復学習させることで、モデルは環境認識（Perception）と行動計画（Action）を緊密に連動させる**アフォーダンス（Affordance）の直感**を獲得する。

## 3. Compound Causal Chains and Multi-Step Reasoning / 複合因果連鎖（Causal Chaining）とマルチステップ推論

**EN** — Complex physical phenomena and task execution in the real world do not stop at simple one-to-one causation. Event A brings about event B, and event B in turn triggers event C, forming a causal chain.

Framingo, by linking the connectives `->` and `!>` one after another like a pipeline (a flattened pipeline), can describe deep causal chains without any nesting.

**JA** — 現実世界の複雑な物理現象やタスクの遂行は、1対1の単純因果にとどまらない。事象Aが事象Bを引き起こし、その事象Bがさらに事象Cのトリガーとなるという因果の連鎖（Causal Chain）を形成する。

Framingoは、結合子 `->` および `!>` をパイプラインのように数珠つなぎに連結（Flattened Pipeline）することで、深い因果連鎖を一切のネストなしに記述できる。

```
[Event_1] -> [Event_2] -> [Event_3] -> [Event_4]
```

### 3.1 Describing a Domino-Like Physical Chain / ドミノ倒し的物理連鎖の記述

**EN** — The following example describes a physical domino sequence: "the vase is pushed, falls, strikes the floor and becomes fragments."

**JA** — 以下は、「花瓶が押され、落下し、床に衝突して破片になる」という一連の物理的ドミノ倒しを記述した例である。

```
FACT:
  Action: Push agt:Cat tgt:Vase
  -> Move tgt:Vase src:On.Table dst:Air
  -> Fall tgt:Vase dst:Floor
  -> Hit tgt:Vase dst:Floor
  -> Result: Become agt:Vase.Piece count:Many
```

**EN** — At each step, the result of the preceding event (`Vase` pushed out into the air) becomes the starting point of the next physical event (falling under gravity), converging at last on shattering.

**JA** — 各ステップにおいて、直前の事象の結果（`Vase` が空中に押し出される）が、次の物理事象（重力による落下）の起点となり、最終的な破砕へと収束していく。

#### The Structural Benefits This Chain Brings to LLMs / この連鎖がLLMにもたらす構造的メリット

**EN** —

1. **Preventing skipped thinking (hallucination):**

   If trained in natural language on "The cat pushed the vase. The vase broke.", the model tends to form a direct shortcut "push $\to$ break". By training the intermediate states (falling, impact) explicitly as a chain, **the indispensable intermediate physical steps** of spatial movement and impact can be forcibly embedded in the model's reasoning path (CoT: chain of thought).

2. **Robustness to queries (QUERY) about intermediate steps:**

   For advanced spatial reasoning such as "after the vase was pushed, and before it broke, where was it?", the model becomes able to answer accurately by referring to the intermediate tokens of the chain (`Move dst:Air`, `Fall dst:Floor`).

**JA** —

1. **思考のスキップ（ハルシネーション）の防止：**

   自然言語で「猫が花瓶を押した。花瓶は割れた。」と学習させると、モデルは「押す $\to$ 割れる」という直接のショートカットを結んでしまいがちである。中間状態（落下・衝突）を明示的にチェーンとして学習させることで、空間的な移動と衝撃という**不可欠な物理の中間媒介ステップ**をモデルの推論経路（CoT: Chain of Thought）に強制的に埋め込むことができる。

2. **中間ステップの問い合わせ（QUERY）への耐性：**

   「花瓶が押された後、割れる前にどこにあったか？」という高度な空間推論に対して、モデルは連鎖の中間トークン（`Move dst:Air`, `Fall dst:Floor`）を参照して正確に回答できるようになる。

## 4. The Topology of Failure and Exception: The Mechanics of the `reason:` Slot / 失敗と例外のトポロジー：`reason:` スロットの力学

**EN** — When an attempt in the physical world ends in failure, merely recording "it failed (Fail)" does not let a reasoning engine learn what to improve next (a retry strategy). Every failure has a direct physical or logical cause (failure mechanism).

In Framingo, for the deviant result that follows a causal misfire (`!>`), the **`reason:` slot** identifies the direct reason for the breakdown.

**JA** — 物理世界における試みが失敗に終わった際、単に「失敗した（Fail）」と記録するだけでは、推論エンジンは次に何を改善すべきか（リトライ戦略）を学習できない。失敗には必ず物理的・論理的な直接の原因（Failure Mechanism）が存在する。

Framingoでは、因果の不発（`!>`）に続いて発生した逸脱結果に対し、**`reason:` スロット**を用いて直接の破綻理由を特定する。

### 4.1 Failure from an Unsuitable Tool / 道具の不適合による失敗

```
FACT:
  Action: Cut agt:John tgt:Bread tool:Ruler
  !> Result: Become agt:Bread.Slice
  -> Result: Deform tgt:Bread reason:Inappropriate.Tool
```

**EN** — (John tried to cut the bread with a ruler, but it did not become slices; because the tool was unsuitable, the bread was squashed.)

**JA** — （定規でパンを切ろうとしたが、スライスにはならず、不適切な道具のためにパンが潰れた）

### 4.2 Failure from Friction and Mechanical Instability / 摩擦と力学的不安定性による失敗

```
FACT:
  when:(State tgt:Floor is:Wet)
  Action: Run agt:John dst:Exit
  !> Result: At agt:John dst:Exit
  -> Result: Fall agt:John reason:Low.Friction
```

**EN** — (Because the floor was wet, John ran toward the exit but did not reach it, and fell owing to low friction.)

With this notation the model internalizes, very efficiently, a causal sensitivity analysis: "when an action failed, which variable in the world was the bottleneck?"

**JA** — （床が濡れていたため、ジョンは出口へ走ったが到達できず、摩擦の低さゆえに転倒した）

この記法により、モデルは「あるアクションが失敗したとき、世界のどの変数がボトルネックになっていたのか」という因果の感度分析（Sensitivity Analysis）を極めて効率的に内面化する。

## 5. Counterfactual Reasoning and Hypothetical Thinking (`HYPO:`) / 反事実推論（Counterfactuals）と仮定思考（`HYPO:`）

**EN** — One of the abilities at the summit of intelligence is counterfactual thinking: simulating in the mind "it did not actually happen, but had things been so at that moment, what would the world have become?" It underlies value-function updates in reinforcement learning and risk assessment in safety-critical systems.

In Framingo, combining the sentence-initial **`HYPO:` prefix** with the **`when:(...)` construction** unfolds counterfactual world-lines safely.

**JA** — 知性の頂点に位置する能力の一つは、「実際には起きなかったが、もしあの時こうであったならば、世界はどうなっていたか？」を脳内で仮想シミュレーションする反事実推論（Counterfactual Thinking）である。これは強化学習における価値関数の更新や、安全クリティカルなシステムにおけるリスク評価の根底をなす。

Framingoでは、文頭の **`HYPO:` プリフィックス**と **`when:(...)` 構文**を組み合わせることで、反事実の世界線を安全に展開する。

```
HYPO: when:([Counterfactual_State]) [Simulated_Action] -> [Projected_Result]
```

### 5.1 Strict Contrast Between "Actual Fact (FACT)" and "Counterfactual (HYPO)" / 「現実の事実（FACT）」と「反事実（HYPO）」の厳密な対比

**EN** — By placing, in the training dataset, contrasting pairs of `FACT` and `HYPO` that branch from the same context, the model is made to recognize clearly the boundary between "tracking reality" and "thought experiment".

**JA** — 学習データセットにおいて、同一の文脈から分岐する `FACT` と `HYPO` のペアを対比的に配置することで、モデルに「現実の追跡」と「思考実験」の境界を明瞭に認識させる。

- **Log of reality (FACT) / 現実のログ（FACT）：**
  ```
  FACT:
    when:(State tgt:Knife is:Sharp)
    Action: Cut agt:Chef tgt:Tomato tool:Knife
    -> Result: Become agt:Tomato.Slice
  ```
- **Counterfactual simulation of the same scene (HYPO) / 同一場面における反事実シミュレーション（HYPO）：**
  ```
  HYPO:
    when:(State tgt:Knife is:Dull)
    Action: Cut agt:Chef tgt:Tomato tool:Knife
    !> Result: Become agt:Tomato.Slice
    -> Result: Crush tgt:Tomato reason:Dull.Blade
  ```

**EN** — The model learns how, merely by the precondition `Sharp` flipping to `Dull`, the right-hand physical process branches from "cutting (`Slice`)" to "crushing (`Crush`)". Having acquired this simulation ability, an AI agent becomes able, before taking an action, to perform spontaneously **proactive hazard-avoidance reasoning**: "what would happen if this tool were broken?"

**JA** — モデルは、前提条件の `Sharp`（鋭利）が `Dull`（鈍ら）に反転しただけで、右辺の物理プロセスが「切断（`Slice`）」から「圧壊（`Crush`）」へと分岐する様を学習する。このシミュレーション能力が身につくことで、AIエージェントはアクションを起こす前に「もしこの道具が壊れていたらどうなるか？」という**プロアクティブな危険回避推論**を自発的に実行できるようになる。

## 6. The Dynamics of Intention and Purpose (`goal:`) and Trial-and-Error (Planning) / 意図・目的（`goal:`）と試行錯誤（Planning）のダイナミクス

**EN** — When running autonomous agents (robots or software agents), behaviour is always driven by some "goal (a state one wishes to achieve)".

The **`goal:(...)` slot** built into the event frame, combined with the causal connectives, describes a complete planning loop: "intention $\to$ action $\to$ evaluation $\to$ retry".

**JA** — 自律型エージェント（ロボットやソフトウェアエージェント）を動かす際、行動は常に何らかの「目的（達成したい状態）」によって駆動される。

事象フレームに組み込まれた **`goal:(...)` スロット**は、因果結合子と組み合わさることで、「意図 $\to$ 行動 $\to$ 評価 $\to$ 再試行」という完全なプランニングループを記述する。

### 6.1 Evaluating the Consistency of Intention and Result / 意図と結果の整合性評価

**EN** — By comparing the content of the `goal:` in an action with the actual result (`Result:`) appearing on the right of the arrow, an agent can evaluate for itself whether its action succeeded.

**JA** — アクションに含まれる `goal:` の内容と、矢印の右辺に現れた実際の結果（`Result:`）を比較することで、エージェントは自らの行動が成功したか否かを自己評価できる。

#### (1) Plan Success (Goal Accomplished) / 計画の成功（Goal Accomplished）

```
FACT:
  Action: Push agt:Robot tgt:Switch goal:(State tgt:Light is:On)
  -> Result: State tgt:Light is:On
```

**EN** — The state specified by `goal:` (`Light is:On`) matches the actual result exactly, so the task is judged complete.

**JA** — `goal:` で指定された状態（`Light is:On`）と、実際の結果が完全一致しているため、タスクは完了と判定される。

#### (2) Plan Failure and Transition to Another Approach (Planning Revision) / 計画の失敗と別アプローチへの遷移（Planning Revision）

```
FACT:
  // Step 1: tries to push it open, but it is a pull door, so it fails
  // ステップ1：押して開けようとするが、引くドアだったため失敗
  Action: Push agt:Robot tgt:Door goal:(State tgt:Door is:Open)
  !> Result: State tgt:Door is:Open
  -> Result: No.Change tgt:Door reason:Wrong.Direction

  // Step 2: learns from the failure, switches to pulling, and succeeds
  // ステップ2：失敗を学習し、引くアクションへ切り替えて成功
  -> Action: Pull agt:Robot tgt:Door goal:(State tgt:Door is:Open)
  -> Result: State tgt:Door is:Open
```

**EN** — This two-step chain beautifully condenses **the whole process of adaptive trial-and-error**: an agent "learned from failure, chose a different action, and achieved its goal."

An LLM exposed to large amounts of data in this pattern does not merely know static causation; it naturally acquires autonomous behaviour-correction ability (self-correction): "when I fail, which alternative action should I try?"

**JA** — この2ステップの連鎖文は、エージェントが「失敗から学習して別のアクションを選択し、目的を達成した」という**適応的試行錯誤（Adaptive Trial-and-Error）の全プロセス**を美しく凝縮している。

このパターンのデータを大量に浴びたLLMは、単に静的な因果を知っているだけでなく、「失敗したときにどの代替アクションを試みるべきか」という自律的な行動修正能力（Self-Correction）を自然に獲得する。

## 7. Formal Definition of the Syntax (Updated: Integrating Chapter 4) / 構文の形式定義（更新版：第4章統合）

**EN** — Presented here is the complete grammar, integrating into the EBNF defined in chapter 2 all the rules specified in this chapter: causal connectives, preconditions, failure constructions and counterfactual reasoning.

**JA** — 第2章で定義したEBNFに、本章で規定した因果結合子、前提条件、失敗構文、反事実推論の全規則を統合した完全版文法仕様を提示する。

```
Statement           ::= EpistemicBlock

EpistemicBlock      ::= Prefix ":" ( ConditionClause )? Pipeline
Prefix              ::= "RULE" | "FACT" | "HYPO" | "QUERY"

ConditionClause     ::= "when:" "(" StateExpression ")"

Pipeline            ::= Event ( Connector Event )*
Connector           ::= "->" | "!>" | "&>"

Event               ::= ActionClause | ResultClause | StateExpression

ActionClause        ::= ( "Action:" )? Verb ( Slot )*
ResultClause        ::= ( "Result:" )? Verb ( Slot )*
StateExpression     ::= ( "State:" )? "tgt:" Concept ( "is:" Concept )? ( Slot )*

Slot                ::= SlotKey ":" SlotValue
SlotKey             ::= "agt" | "tgt" | "tool" | "src" | "dst" | "loc"
                      | "tense" | "asp" | "mod" | "iter" | "freq"
                      | "goal" | "reason" | "count" | "is"

SlotValue           ::= Concept
                      | "(" EpistemicBlock ")"
                      | "?"

Concept             ::= ( Determiner "." )? ( Modifier "." )* BaseEntity ( "." Part )? ( "<" Index ">" )?
BaseEntity          ::= ( "'" )? Identifier      // "'" marks a word outside the instinct vocabulary
Determiner          ::= "Every" | "Any" | "Some" | "This" | "No"
Index               ::= [A-Z0-9]+
```

## 8. Summary of Chapter 4 / 第4章の総括

**EN** — With this chapter, the dynamic architecture by which Framingo describes the physical mechanics of the world and the reasoning of agents is fully complete.

1. **Binarizing into the occurrence connective (`->`) and the prevention connective (`!>`) made the boundary between mechanical success and failure mathematically clear.**
2. **The `when:(...)` construction strictly separates the static premise environment from dynamic intervention by external force, making affordances learnable.**
3. **Flat pipeline linking (chains of `->`) makes multi-stage physical chains and the intermediate processes of spatial movement visible without nesting.**
4. **The `reason:` slot structures "the physical mechanism of breakdown", going beyond mere failure.**
5. **Counterfactual simulation with the `HYPO:` prefix lays the footing for hazard avoidance and what-if reasoning.**
6. **Fusing the `goal:` slot with causal chains completes the description of agents' intention-driven behaviour and autonomous trial-and-error (planning).**

The next chapter (chapter 5, the final chapter) proceeds to hand this language specification over to AI agents and automatic generation scripts, and to formulate the concrete implementation protocol and validation procedure for actually carrying out "Phase 1: generation of a 30,000-item synthetic dataset" and "training and verification with a minimal Transformer model".

**JA** — 本章の策定をもって、Framingoが世界の物理力学とエージェントの推論を記述するための動的アーキテクチャが完全に完成した。

1. **生起結合子（`->`）と阻止結合子（`!>`）の2値化により、力学的な成功と失敗の境界線を数学的に明瞭にした。**
2. **`when:(...)` 構文によって、静的な前提環境と動的な外力介入を厳密に分離し、アフォーダンスの学習を可能にした。**
3. **フラットなパイプライン連結（`->` の数珠つなぎ）により、多段階の物理連鎖と空間移動の中間媒介プロセスをネストなしで可視化した。**
4. **`reason:` スロットを導入し、単なる失敗にとどまらない「破綻の物理的メカニズム」を構造化した。**
5. **`HYPO:` プリフィックスを用いた反事実シミュレーションにより、危険回避や What-if 推論の足場を固めた。**
6. **`goal:` スロットと因果連鎖の融合により、エージェントの意図駆動型行動と自律的試行錯誤（Planning）の記述を完結させた。**

次章（第5章：最終章）では、本言語仕様をAIエージェントおよび自動生成スクリプトに引き渡し、実際に「Phase 1：3万件の合成データセット生成」および「最小構成Transformerモデルによる学習と検証」を完遂するための、具体的な実装プロトコルとバリデーション手順の策定へと進む。
