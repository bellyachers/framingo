# Fillmore 設計仕様・開発憲章（第1章：背景と設計思想）

## 1. 開発の背景：現代LLMが抱える根本的断絶

現代の大規模言語モデル（LLM）は、膨大な自然言語コーパスをTransformerアーキテクチャの自己回帰タスク（Next-token prediction）によって事前学習することで、目覚ましい言語生成能力と表層的な推論能力を獲得した。人間が書いた数兆トークンに及ぶウェブテキストを圧縮・内面化した結果、文体模写、要約、コード生成、さらには各種ベンチマーク試験において高度な応答を示すに至っている。

しかし、その目覚ましい成功の裏側で、人工知能研究の本質的な問いに直面したとき、現行のLLMには看過し得ない根本的な欠陥が露呈する。それは「強固で破綻のない物理世界モデル（World Model）と因果関係の直感的理解の欠如」である。

### 1.1 記号接地問題とハルシネーションの正体

現行のLLMは、テキストという極めてノイズに満ちた1次元の離散トークン列の共起確率を学習しているに過ぎない。モデルが「リンゴを切ると半分になる」「落としたガラスは割れるが、クッションは割れない」と正しく答えることがあるとしても、それはモデルの内部に「リンゴの幾何学的連続性」や「ガラスの脆性という物理特性」が真にシミュレートされているからではない。単に、学習データの中に「切る」「リンゴ」「半分」という文字列が統計的に近傍に配置されていた頻度が高かったという、表層的な言語統計の反映である場合が極めて多い。

その結果として生じるのが、いわゆるハルシネーション（幻覚）である。少し文脈を複雑にしたり、日常的な文脈から外れた組み合わせを与えたりすると、モデルはいとも簡単に物理法則を逸脱する。

- 「硬い鉄のナイフを落としたら粉々に砕け散った」
- 「部屋を暗くして本を読んだ」
- 「閉じた箱の中に入っているリンゴを、箱の外から手に取って食べた」

こうした誤りは、人間の子どもであれば3歳から5歳頃までに身体経験を通して自明のものとして獲得する「物理の直感（Naive Physics）」が、数千億パラメータを持つ超巨大モデルの内部にすら確固たる形では宿っていないことを示している。

### 1.2 自然言語というプロトコルの本質的非効率性

なぜ数兆トークンものデータを読み込ませても、物理や因果の直感が安定して結晶化しないのか。その主因は、人間が数万年かけて進化させてきた「自然言語（英語や日本語など）」そのものの性質にある。

自然言語は、**「思考そのもの」を表現するために設計されたものではない。**

自然言語の本質は、帯域が極端に狭い物理媒体（声帯から発せられる音波の振動、あるいは紙に書かれた文字）を通じて、ある人間の脳から別の人間の脳へ情報を送るための、**極度に非可逆圧縮された通信用プロトコル**である。そのため、自然言語には思考や物理のモデル化にとって有害なノイズが大量に含まれている。

- **不規則性と歴史的ゴミ：** 不規則動詞、格変化の残滓、恣意的な前置詞の選択、語源的な変遷による意味の分岐など、物理因果とは全く関係のない文化的・音韻的ルールが大量に存在し、モデルの貴重な計算資源（パラメータとアテンション機構）を浪費させる。
- **文脈依存の省略と照応の曖昧性：** 「彼」「それ」「その場所」といった代名詞が何を指しているのか、あるいは主語が誰であるのかを特定するだけで、モデルは高層のアテンション層の大半を「表層の解決（Surface Parsing）」に消費させられる。
- **構文の硬直性と過剰な冗長性：** 英語のSVO語順や仮定法の構文規則など、思考のコア（誰が・何を・どうした・その結果どうなった）を伝えるためだけに、過剰に複雑な文法的骨組みを要求する。

自然言語というノイズだらけの媒体を通して世界モデルを学ばせようとする行為は、あたかも「砂嵐の吹き荒れる低解像度の白黒ブラウン管テレビを通して、物理シミュレーションの法則を読み解け」とモデルに要求しているようなものである。スケール則（Scaling Law）によってモデルを巨大化させれば解像度は上がるかもしれないが、根本的な情報伝達の歪みは解消されない。

## 2. 対極の過ち：シンボリックAI（形式論理）の限界

では、自然言語を捨てて、数学や記号論理学（一階述語論理や状況計算、PDDLなど）で世界を厳密に定義すればよいのか。人工知能の歴史において、まさに1970年代から1990年代にかけての「エキスパートシステム」や「GOFAI（Good Old-Fashioned AI）」がその道を歩み、そして完全に挫折した。

### 2.1 「死んだ記号」とフレーム問題

形式論理学者は、世界を無矛盾な数式や述語によって厳密に記述しようとした。

$$\forall x, y \ (\text{Cut}(x, y) \land \text{Bread}(y) \to \exists z \ (\text{Slice}(z, y)))$$

しかし、現実世界はこのような無菌室の論理式には収まらない。

- 「切る」とは、刃の角度が何度で、どの程度の圧力がかかったときを指すのか？
- ナイフが錆びていたらどうなるのか？
- パンが石のように硬く乾燥していたらどうなるのか？
- 切った瞬間に部屋の照明が消えたら、パンは切れたと言えるのか？

現実の事象には無数の前提条件と例外が存在し、それらすべてを公理系として人間が手作業で書き下すことは原理的に不可能である（フレーム問題）。シンボリックAIが扱っていた記号は、現実の柔軟さや連続性から切り離された「死んだ記号（Brittle Symbols）」であり、わずかでも想定外の入力が入るとシステム全体が硬直して崩壊した。

### 2.2 コネクショニズム（LLM）の真の強みとは何か

ここで私たちは、LLM（ディープラーニング・ニューラルネットワーク）の真の強みに立ち返る必要がある。LLMの最大の武器は、記号を離散的なものとして固定せず、「高次元ベクトル空間（Embedding Space）における連続的な配置とクラスタリング」として処理する点にある。

人間が厳密な境界線を引かなくても、モデルは大量のテキストを通過する中で、

- 「リンゴを切った結果、半分（Half）になることもあるし、スライス（Slice）になることもある」
- 「Half と Slice は、幾何学的には異なるが、『切断によって生じる全体の一部分』という意味空間において極めて近い位置に存在する」
- 「しかし、Breadに対してはSliceが自然に選ばれ、Appleに対してはHalfやPieceも同等に選ばれるという、素材によるアフォーダンスの微細なグラデーションが存在する」

ということを、**確率分布と潜在ベクトルの幾何学的配置として柔軟に獲得できる**。これが、人間が「直感（System 1）」と呼んでいるものの計算的実体である。

形式論理のように硬直せず、かといって自然言語のように無秩序に発散しない。この「統計的直感の獲得能力」こそがニューラルネットの最大の奇跡であり、私たちが開発すべきシステムが絶対に手放してはならないコア機能である。

## 3. 基本哲学：Mentalese（思考の言語）の実装

本プロジェクトの目的は、シンボリックAIの持つ「論理的透明性・規律」と、コネクショニストAI（LLM）の持つ「柔軟な意味空間・直感の獲得能力」という、過去半世紀にわたって対立してきた2大潮流を完全に融合させることにある。

そのための基盤となる設計思想が、認知科学において提唱されてきた「思考の言語仮説（Language of Thought / Mentalese）」の実装である。

### 3.1 思考の生データを直列化する

哲学者ジェリー・フォーダーらが主張したように、人間の知性が内的に世界をシミュレートし、推論を行っている際、脳内では英語の助動詞や日本語の助詞のような表層の文法規則は稼働していない。脳内の基底で動いているのは、もっと原初的で、直接的で、機能に特化した内部表現である。

1. **対象の認知：** 赤くて甘い、特定のリンゴ（属性と概念の合成）
2. **状態・環境の把握：** それがテーブルの上に静止している（空間配置）
3. **行動の企図：** 刃物を用いて外力を加える（道具を用いたアクション）
4. **因果的推論：** 構造的結合が破壊され、2つ以上の破片へと相転移する（物理因果）

私たちが開発する言語（Fillmore）は、人間やエージェントの脳内で起きているこの「認知のスナップショットと因果ベクトル」を、1ミリの歪みもなく、最小の摩擦でそのままテキストストリームとしてダンプ（直列化）した言語である。

自然言語のように「他人に伝えるための装飾」を施す必要はない。同時に、形式論理のように「森羅万象を数式に閉じ込める」傲慢さも持たない。ただ、事象の構造をありのままに、極めて透明度の高いトークン列として記述する。

### 3.2 創発のための「適度な制約」

本言語の文法は、人間がモデルに対して知識をトップダウンで教え込むための「ルールブック」ではない。それは、「モデルが自律的に高次元空間の中で世界の因果律を結晶化させるための、高純度な培養液（足場 / Scaffolding）」である。

骨組み（文法）に極めて高い規則性と一貫性を与えることで、モデルは構文解析の迷路から完全に解放される。パラメータの全容量が、事象と事象の結びつき、属性の保存と破壊、アクションによる状態変化のモデリングという、**「世界モデルの構築」そのものに100%集中投資される。**

そして、骨組みの中を流れる概念（`Bread.Slice` や `Break-prone` など）には、自然言語由来の豊かな意味的多様性をあえて残す。これによって、モデルは「厳密な数式演算マシーン」になるのではなく、未知の状況に直面した際にも「これは以前学習したあの状況と意味空間上で似ているから、きっとこういう結果になるはずだ」という、人間同様のしなやかなアナロジー（類推能力）を発揮できるようになる。

## 4. なぜ今、このアプローチが必要なのか

2020年代半ばを迎えた現在、AI研究の最前線では「スケーリング則の頭打ち」と「データの枯渇」が深刻な課題として議論されている。高品質な人間の自然言語テキストはインターネット上から掘り尽くされつつあり、単にモデルを巨大化して生データを流し込むだけの力技は、投じる莫大な電力や計算資源に対して得られる知性の伸び（ROI）が著しく低下している。

いま真に求められているのは、データの「量」の拡大ではなく、**データの「情報純度（Information Density）」の極限までの純化**である。

### 4.1 合成データ（Synthetic Data）時代のコア燃料

次世代のAI開発において、高品質な推論用合成データの生成は死活問題である。しかし、自然言語で書かれた推論データ（Chain of Thoughtなど）は、生成する側にとっても検証する側にとってもノイズが多く、論理の破綻を自動検知することが極めて困難である。

Fillmoreは、「AIエージェント自身が世界をシミュレートし、計画を練り、思考ログを保存するためのネイティブコード」として機能する。

- 生成スクリプトによって、数千万件の物理的に矛盾のない因果ステップを無限に量産できる。
- パーサーやバリデータによって、構文的・論理的な矛盾を一瞬で決定論的に弾くことができる。
- それでありながら、出力されたテキストは人間が肉眼で見ても「5分で直感的に読める」認知的一貫性を保っている。

### 4.2 小規模モデル（SLM）における知性の創発

巨大IT企業が数十兆円を投じて巨大モデルを競い合う一方で、本アプローチは「数百万〜数千万パラメータ程度の極小トイモデル」においてすら、極めてシャープな世界モデルの創発を可能にする。

無駄な表層言語のノイズを完全に削ぎ落とした純粋な因果コーパスを与えることで、普通のローカルPCや単一のコンシューマ向けGPU環境下であっても、モデル内部に「物理法則の普遍性」「属性の保存則」「空間移動の整合性」を淀みなく学習させることができる。これは、パーソナルAI、自律型ロボティクス、エッジデバイスにおけるエージェント推論エンジンにとって、極めて強力な突破口となる。

## 5. 第1章の総括

本開発の核心は、「自然言語のファジィな豊かさ」と「形式言語の論理的純度」の黄金律を見つけ出すことにある。

1. **自然言語の表層ノイズ（不規則性・恣意的構文・冠詞・曖昧な語順）を完全に切除する。**
2. **形式論理の硬直性（閉じた世界・例外を許さない数式定義）を排し、LLMの潜在空間による統計的クラスタリングの力を最大限に活かす。**
3. **思考の生構造（述語・格・属性階層・因果ベクトル）をダイレクトに写し取る、透明で美しい最小限の文法を定義する。**

この思想に基づき、次章以降では、事象を記述する「文の大枠と格文法」、概念を自在に合成する「ドット記法と形態素システム」、そして世界の理を記述する「因果・条件・照応システム」の厳密な仕様策定へと進む。

---

# Fillmore 設計仕様・開発憲章（第2章：構文アーキテクチャと格システム）

## 1. 構文設計の根幹：ネオ・デイヴィドソン流意味論の工学的実装

前章で定義した「思考の生データを歪みなく直列化（シリアライズ）する」という思想を具現化するにあたり、本言語（Fillmore）は言語哲学および意味論におけるネオ・デイヴィドソン流意味論（Neo-Davidsonian Semantics）の枠組みを構文の基礎構造として採用する。

### 1.1 伝統的文法（統語論）の破棄

自然言語（特に英語をはじめとするSVO型言語）において、文は長らく「主語（Subject）＋動詞句（Verb Phrase）」という非対称な二項対立として扱われてきた。しかし、物理的現実や事象の認知モデルにおいて、「主語」という特権的なスロットは本来存在しない。 例えば、「ジョンがナイフでパンを切った」という現象を観察したとき、客観的に生起している物理的事実は以下の要素の等価な結合に過ぎない。

- 事象の種類（Event Type）：切断（Cut）
- 動作を引き起こした物理主体（Agent）：ジョン（John）
- 作用を受けた対象（Patient/Target）：パン（Bread）
- 媒介された物理的器具（Instrument/Tool）：ナイフ（Knife）

自然言語は、発話者の主観的フォーカス（視点）に基づいて「ジョン」を主語の位置に祭り上げたり、受動態を用いて「パン」を主語に繰り上げたりする。この「視点に依存した統語的ねじれ」こそが、LLMに不要な統語解析の負荷を強いる元凶である。

### 1.2 事象（Event）を中心としたフラットな格フレーム

Fillmoreにおいて、文の最小構成単位は「独立した1つの事象（Event）」である。 事象は、核となる「述語（Predicate）」と、その事象を取り巻く各種の「格引数（Case Arguments / Slots）」が完全にフラットなキー・バリュー形式で結合されたものとして定義される。

数学的には、ある事象 e は以下のような一階述語の論理積としてモデル化される。

Event(e)∧Predicate(e,Cut)∧agt(e,John)∧tgt(e,Bread)∧tool(e,Knife)

Fillmoreの具象構文（Concrete Syntax）は、この論理構造をトークン列として直接書き下す。

Plaintext

```
Action: Cut agt:John tgt:Bread tool:Knife
```

または、より簡潔に述語を直接ヘッダとする記法も等価として許容する。

Plaintext

```
Cut: agt:John tgt:Bread tool:Knife
```

この構造により、各スロットは完全に直交（独立）し、相互に文法的な従属関係を持たない。

## 2. スロットの順序不変性（Order Invariance）と対称性

本構文アーキテクチャの極めて重要な特徴は、「述語の後に続く格スロットの並び順は完全に任意であり、順序によって意味が変化しない」という点である。

### 2.1 順序不変性のメリット

以下の3つの文は、Fillmoreのパーサーおよび意味解釈系において完全に同一の事象として評価される。

Plaintext

```
// パターン1：動作主先行（英語の話者直感に近い配置）
Action: Cut agt:John tgt:Bread tool:Knife

// パターン2：対象先行（作用を受ける物体にフォーカスした配置）
Action: Cut tgt:Bread tool:Knife agt:John

// パターン3：道具先行（インターフェース重視の配置）
Action: Cut tool:Knife agt:John tgt:Bread
```

この順序不変性がLLMの学習に与える影響は絶大である。 自然言語を学習するトランスフォーマーモデルは、「語順（Word Order）」から格関係（誰が誰をどうしたか）を逆算するために、アテンション層の多くのヘッドを位置エンコーディング（Positional Encoding）の解析に割いている。 しかしFillmoreでは、各トークンが `agt:` や `tgt:` という明示的な格タグ（Role Marker）を冠しているため、位置エンコーディングに依存することなく、自己注意機構（Self-Attention）はダイレクトに「述語と格の対応関係」へ重みを張ることができる。

### 2.2 データ拡張（Data Augmentation）としての順序シャッフル

合成データを生成する際、同一の事象に対してスロットの順序をランダムにシャッフルして学習コーパスに混入させる。これにより、モデルは「特定の語順パターンへの過学習」から完全に遮断され、**「文脈の中にどのスロットが存在し、それぞれの値が何であるか」という純粋な論理集合としての認識能力**を獲得する。

## 3. 格スロットの任意性（Optionality）と抽象度のグラデーション

前章の議論で確立された通り、物理法則や因果の本質を捉える上で、すべての格スロットが常に揃っている必要はない。むしろ、「必要に応じてスロットが脱落し、それによって文の抽象度が滑らかに変化する」ことこそが、Fillmoreの表現力の源泉である。

### 3.1 必須項の最小化（コアとしての述語と対象）

事象を記述する上で、理論上真に削ぎ落とせない最小限の核は、多くの場合「述語（何が起きるか）」と「対象（何に対して起きるか）」の2点のみである。

- **最大解像度（個別エピソード）：**
  Plaintext
  ```
  Action: Cut agt:John tgt:Bread[1] tool:Knife tense:past
  ```
  「誰が、何を、何を使って、いつ切ったか」の全情報が特定されている。
- **動作主の抽象化（受動・原因不問）：**
  Plaintext
  ```
  Action: Cut tgt:Bread[1] tool:Knife
  ```
  パンがナイフで切られた事実のみを記述。ジョンが切ったのか、機械のアームが切ったのかは問わない。
- **道具の抽象化（手段不問）：**
  Plaintext
  ```
  Action: Cut tgt:Bread[1]
  ```
  レーザーで切られたのか、刃物で切られたのかを問わず、「切断された」という事象の核のみを抽出。
- **極限の抽象化（純粋因果則）：**
  Plaintext
  ```
  Action: Cut tgt:Bread
  ```
  個体識別子すら脱落し、「パンを切るという行為一般」を指す。

モデルはこのグラデーションを経験することで、「情報が多ければ推論結果（Result）の解像度が上がり、情報が少なければ結果もまた一般的・抽象的な状態へとフォールバックする」という、柔軟なベイズ的推論の挙動を自然に獲得する。

## 4. 厳選されたコア格スロット一覧（Core Case Slots）

自然言語の文法書には何十種類もの格や前置詞用法が存在するが、物理世界の力学、状態遷移、エージェントの行動計画を網羅するためには、以下の**8つの主要格スロット**を厳格に定義すれば十分である。

| スロット名    | 正式名称                     | 物理・意味論的定義                             | 典型例                                           |
| ------------- | ---------------------------- | ---------------------------------------------- | ------------------------------------------------ |
| **`agt:`**    | Agent（動作主）              | 事象を能動的に引き起こす力学的・意志的ソース   | `agt:John`, `agt:Robot_Arm`, `agt:Wind`          |
| **`tgt:`**    | Target / Patient（対象）     | 事象の直接的な作用を受け、状態が変化する実体   | `tgt:Bread`, `tgt:Apple`, `tgt:Door`             |
| **`tool:`**   | Instrument（道具・媒介）     | 動作主が対象に作用を及ぼすために媒介させる物体 | `tool:Knife`, `tool:Key`, `tool:Hammer`          |
| **`src:`**    | Source（起点・出所）         | 空間移動の出発点、または状態遷移の初期状態     | `src:Table`, `src:Room_A`, `src:Inside.Box`      |
| **`dst:`**    | Destination（終点・目標）    | 空間移動の到達点、または状態遷移の到達先       | `dst:Floor`, `dst:Room_B`, `dst:On.Chair`        |
| **`loc:`**    | Location（静的位置）         | 事象全体が生起している空間的・環境的文脈       | `loc:Kitchen`, `loc:Outdoor`, `loc:Dark.Room`    |
| **`goal:`**   | Goal / Intention（目的）     | そのアクションを駆動している期待結果状態       | `goal:(Become agt:Bread.Slice)`                  |
| **`reason:`** | Reason / Cause（理由・死因） | 失敗や事象の直接的な力学的トリガー             | `reason:Slip`, `reason:Friction`, `reason:Block` |

### 4.1 空間・トポロジーの記述（`src:`, `dst:`, `loc:`）

移動や配置の物理学を記述する場合、前置詞の迷宮（in, on, at, into, onto, from）に陥ってはならない。Fillmoreでは、空間変化はすべて「起点（`src:`）から終点（`dst:`）への遷移」として統一される。

Plaintext

```
// 猫がテーブルの下から椅子の上へ飛び乗る
Action: Move agt:Cat src:Under.Table dst:On.Chair

// リンゴを箱の中に入れる
Action: Put agt:John tgt:Apple src:On.Counter dst:In.Box
```

「どこからどこへ」という力学的な幾何学ベクトルが、わずか2つのスロットで曖昧さなく確定する。

### 4.2 意図と行為の分離（`goal:`）

ロボット工学や自律型エージェントの思考プロセスにおいて、「実際のアクション」と「それを起こした意図（期待）」を分離して記述することは、計画（Planning）とデバッグにおいて決定的な意味を持つ。

`goal:` スロットは、事象の中に「入れ子の期待状態」を保持することを可能にする。

Plaintext

```
Action: Push agt:Robot tgt:Door goal:(State tgt:Door is:Open)
```

このアクションが実行された後、後述する因果結合子によって「実際にドアが開いたか（成功）」あるいは「鍵がかかっていて開かなかったか（失敗）」が対比される。これにより、モデルは「試み（Attempt）」と「結果（Outcome）」のギャップを認知できるようになる。

## 5. TAM（時制・相・法）および定量的修飾子のスロット化

自然言語における最大の不規則性の温床であるTAM（Tense, Aspect, Modality：時制・相・法）は、Fillmoreにおいては動詞の語形変化（活用）を一切起こさせず、**すべて独立した修飾スロット（Modifier Slots）として等価に扱う。**

### 5.1 TAMスロットの仕様

#### (1) `tense:`（時制 / 時間軸上の位置）

発話時（現在）を基準とした時間的位置付け。

- `tense:past`（過去の確定事実）
- `tense:present`（現在の状態・習慣）
- `tense:future`（未来の予測・予定） ※ただし、普遍的な物理法則（`RULE:`）においては、このスロットは原則として省略（無標）される。

#### (2) `asp:`（相 / アスペクト）

事象の内部時間的構造（完了しているか、継続中か）。

- `asp:completed`（完了相：事象が終結し、結果状態が残存している）
- `asp:progressive`（進行相：事象の物理プロセスが現在進行中である）
- `asp:iterative`（反復相：同様の動作が断続的に繰り返されている）

#### (3) `mod:`（法 / モダリティ）

事象の必然性、可能性、能力。

- `mod:can`（可能・能力：その事象を引き起こす潜在能力がある）
- `mod:must`（必然・義務：物理的拘束または論理的帰結として不可避である）
- `mod:may`（蓋然性：50%前後の確率で生起し得る）

### 5.2 定量・頻度スロット（Quantifiers & Frequency）

事象の反復回数や発生頻度も、動詞を修飾するスロットとしてフラットに配置する。

- **`iter:`（反復回数）：** `iter:1`, `iter:3`, `iter:many`
- **`freq:`（発生頻度）：** `freq:always`, `freq:often`, `freq:rarely`, `freq:never`

### 5.3 統合記述例

「ジョンは昨日、ナイフでパンを3回続けて切っていた（進行・反復）」という、自然言語であれば複雑な過去進行・反復表現になる事象は、以下のようにスロットの集合として明快に記述される。

Plaintext

```
FACT: Action: Cut agt:John tgt:Bread tool:Knife iter:3 asp:progressive tense:past
```

パーサーは動詞 `Cut` を一切変形させることなく、付随する属性フラグを辞書オブジェクトのキーとして即座に格納できる。

## 6. 文の大枠（Prefix / Epistemic Status）の定義

文全体の認識論的ステータス（その文がどのような性質の主張であるか）は、文頭のプリフィックス（Prefix）によって一意に宣言される。これにより、モデルは文の最初の1トークンを読んだ瞬間に、後続するテキストの解釈モード（推論回路の切り替え）を確定させることができる。

本言語では、以下の**4つの大枠プリフィックス**を制定する。

Plaintext

```
[PREFIX]: [Event_1] (Connector [Event_2] ...)
```

### 6.1 `RULE:`（普遍的法則・一般規則）

- **定義：** 時間、場所、特定の個体を超越して普遍的に成立する物理法則、因果律、オントロジーの定義。
- **特性：** `tense:` や個別のインスタンスID（`#123`）を持たず、全称量化（`Every.`）や未定義の一般概念で記述される。
- **例：**
  Plaintext
  ```
  RULE: Action: Drop tgt:Every.Break-prone.Thing -> Break agt:It
  ```
  （壊れやすいあらゆる物は、落とすと破損する）

### 6.2 `FACT:`（一度きりの出来事・エピソード記録）

- **定義：** 特定の時空において実際に発生した、1回限りの確定的な歴史的事実、観測ログ。
- **特性：** 特定のインスタンス、具体的な動作主、時制（`tense:past` など）を伴うことが多い。エージェントのエピソード記憶（Episodic Memory）の記録に用いられる。
- **例：**
  Plaintext
  ```
  FACT: Action: Cut agt:John tgt:Bread#402 tool:Knife#1 -> Result: Become agt:It.Slice count:5
  ```
  （ジョンが特定のパン#402をナイフ#1で切り、5枚のスライスにした）

### 6.3 `HYPO:`（反事実的シミュレーション・仮定）

- **定義：** 現実には生起していないが、前提条件が満たされた場合に生起し得る仮想的なシナリオ、思考実験（"What-if"）。
- **特性：** 前提条件（`when:`）を伴い、エージェントが行動計画（Planning）を策定する際のシミュレーション空間として機能する。
- **例：**
  Plaintext
  ```
  HYPO: when:(State tgt:Room is:Dark) Action: Walk agt:John dst:Door -> Result: Bump agt:John tgt:Wall
  ```
  （もし部屋が暗ければ、ジョンがドアへ歩いた場合、壁に衝突するだろう）

### 6.4 `QUERY:`（問い合わせ・推論要求）

- **定義：** モデルに対して欠落したスロットや因果の帰結を予測・補完させるためのプロンプト形式。
- **特性：** 未知の項目が `?`（クエスチョンマーク）でプレースホルダー化されている。
- **例（結果の推論）：**
  Plaintext
  ```
  QUERY: Action: Drop tgt:Glass.Cup src:Table dst:Stone.Floor -> Result: ?
  ```
  （ガラスのコップを石の床に落とした。結果はどうなるか？ → モデルは `Break agt:It` などを出力する）
- **例（アブダクション推論 / 原因の逆算）：**
  Plaintext
  ```
  QUERY: Action: ? -> Result: Become agt:Apple.Half count:2
  ```
  （リンゴが2つの半分になった。直前に行われたアクションは何か？ → モデルは `Cut tgt:Apple` などを出力する）

## 7. 構文の形式定義（簡易EBNF）

本章で定めた構文構造の厳密性を担保するため、パーサー開発の基準となる形式文法（EBNF記法）を以下に規定する。

EBNF

```
Statement       ::= Prefix ":" EventSequence
Prefix          ::= "RULE" | "FACT" | "HYPO" | "QUERY"

EventSequence   ::= Event ( Connector Event )*
Connector       ::= "->" | "!>"

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

_(※ `ConceptExpression` の内部構造、すなわちドット記法や形態素修飾の仕様については次章で詳述する)_

## 8. 第2章の総括

本章では、Fillmoreの骨格となる統語論と格システムを定義した。

1. **主語中心の自然言語統語論を解体し、述語を中心とするフラットなネオ・デイヴィドソン流格フレームを導入した。**
2. **格スロットは順序不変（Order-Invariant）であり、明示的なタグ（`agt:`, `tgt:` 等）によって自己注意機構の負荷を最小化する。**
3. **事象の記述は任意のスロット脱落を許容し、個別具体のエピソードから極限まで抽象化された物理普遍則までをシームレスに横断する。**
4. **TAMや回数・頻度も動詞の変形ではなく独立したスロットとして扱い、不規則変化を完全に撲滅した。**
5. **文頭プリフィックス（`RULE`, `FACT`, `HYPO`, `QUERY`）によって、モデルの推論モード（演繹、記憶、計画、逆算）を一意に制御する。**

次章（第3章）では、この格フレームの中に流し込まれる概念データそのものの設計――すなわち、属性の保存と破壊を司る「ドット記法」、語彙爆発を防ぐ「機能接尾辞システム」、そして論理的「限定詞」の仕様策定へと進む。

---

# Fillmore 設計仕様・開発憲章（第3章：概念合成・形態論・オントロジー）

## 1. 概念表現の根幹：ドット記法（Dot Notation）による概念合成

格フレーム（スロット）に代入される実体や概念をどのように表現するかは、言語の表現力とモデルの学習効率を決定づける極めて重要な要素である。自然言語では、修飾関係を表現するために「形容詞の前置」「関係代名詞節による後置修飾」「複合名詞の形成」など多様かつ複雑な統語規則が混在し、単語間の結合境界が極めて曖昧である。

本言語（Fillmore）では、すべての実体および概念の派生・修飾をドット記法（Dot Notation）という単一かつ統一的なメカニズムに統合する。

Plaintext

```
[Determiner].[Modifier...].[BaseEntity].[Part/Aspect]
```

### 1.1 概念の絞り込み（Intersection）と部分論（Mereology）の統合

ドット `.` は、プログラミング言語におけるオブジェクトのプロパティ参照（メンバアクセス）と、型システムにおける部分型（Subtyping）、そして形式意味論における交差（Intersection）の性質を兼ね備えた万能の合成演算子である。

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

自然言語では「A slice of sweet red apple」という前置詞句を伴う複雑な名詞句になるものが、Fillmoreでは以下の単一のトークン列（チャンク）として完結する。

Plaintext

```
Sweet.Red.Apple.Slice
```

### 1.2 概念階層の左から右への展開則

ドット記法における要素の並び順は、認知的なスコープの大きさに従って「外側の文脈（広範囲）から内側の部分（局所）」へと流れる規則を基本とする。

1. **限定詞（Determiner）：** その概念が世界のどこをどの範囲で指しているか（例：`Every`, `This`）
2. **内在的・外在的属性（Modifiers）：** 色、材質、温度、性質（例：`Hot`, `Red`, `Break-prone`）
3. **基底実体（Base Entity）：** 物理的な核となるオブジェクト（例：`Apple`, `Glass`, `Door`）
4. **派生・部位（Part / Aspect）：** 全体から切り出された領域、形状（例：`Piece`, `Slice`, `Handle`）

この規則により、モデルの自己注意機構（Self-Attention）は、左端でスコープを特定し、中央で素材や性質を読み解き、右端で最終的な物理的実体・形状を同定するという、極めて負荷の低い順次処理を行うことができる。

## 2. 属性の保存則（Invariance）と破壊則（Decay）

ドット記法の真価が最も発揮されるのは、因果遷移（`Action` $\rightarrow$ `Result`）における「物理的属性の追跡」である。

事象によって物体に外力が加わったとき、維持される性質と失われる性質が存在する。自然言語ではこれを文脈から暗黙に読み取らなければならないが、Fillmoreではドット記法の連鎖の変遷そのものが物理シミュレータとして機能する。

### 2.1 物質的・内在的属性の保存（Invariance）

切断や移動などの物理的操作を受けても、対象の本質的な材質、味、色、組成などの「内在的プロパティ（Intrinsic Properties）」は保存される。

Plaintext

```
Action: Cut tgt:Sweet.Red.Apple tool:Knife
-> Result: Become agt:Sweet.Red.Apple.Slice
```

この文において、`Sweet` と `Red` という修飾子は結果側（`Result`）の `Apple.Slice` にそのまま継承されている。

モデルは大量のコーパスを通じて、「`Cut` というアクションに対して、`Color` や `Taste` を表すプレフィックスはそのまま右辺へコピーされる（保存される）」という物理的不変性の直感を、文字列レベルのパターンマッチングとベクトル空間の連続性から自然に学習する。

### 2.2 形状的・構造的属性の破壊・変容（Decay / Mutation）

一方で、物体の全体サイズ、外形、閉鎖性といった「構造的プロパティ（Extrinsic / Structural Properties）」は、切断や破壊などのアクションによって無効化または変異する。

- **形状の喪失：**
  Plaintext
  ```
  // 丸い（Round）リンゴを切ると、もはや丸くはないため Round は脱落する
  Action: Cut tgt:Round.Apple tool:Knife
  -> Result: Become agt:Apple.Half
  ```
- **サイズの縮減：**
  Plaintext
  ```
  // 大きな（Big）パンを切ると、小さな（Small）スライスになる
  Action: Cut tgt:Big.Bread tool:Knife
  -> Result: Become agt:Small.Bread.Slice count:Many
  ```
- **完全性の破綻：**
  Plaintext
  ```
  // まるごと（Whole）のスイカを割ると、Whole は完全に消失する
  Action: Break tgt:Whole.Watermelon
  -> Result: Become agt:Watermelon.Piece
  ```

人間が「切断公理：対象が切断された場合、その真円度は保持されない」といった膨大な例外ルールを記述する必要はない。単にコーパスの中で `Round.Apple` が切られた後に `Round` が脱落している実例を見せ続けるだけで、モデルのニューラルネットワークは「どの属性がアクションに対して脆弱（Non-conservative）であり、どの属性が頑健（Conservative）であるか」を潜在空間の重みとして自動的に峻別する。

## 3. 形態論システム：動詞語根と「3大機能接尾辞」

自然言語の致命的な欠陥は、品詞の分化に伴う語彙の無秩序な増殖である。例えば英語において、「壊す（Break）」「壊れやすい（Fragile）」「壊れた（Broken）」という3つの概念は、語源的・形態論的に不連続であり、モデルはそれぞれを別個の埋め込みベクトルとして学習しなければならない。

Fillmoreでは、概念の核を「動詞（事象・変化を引き起こすアクション）」**に一本化し、そこに規則的な**「3大機能接尾辞」をハイフン結合することで、語彙爆発を完全に抑え込みながら因果と直結した形容詞・状態表現を生成する。

Plaintext

```
[BaseVerb]-[FunctionalSuffix]
```

### 3.1 3大機能接尾辞の定義

| **接尾辞**   | **機能名**                            | **物理・因果的定義**                                                         | **派生例**                                                                                           | **置換される自然言語**                                                              |
| ------------ | ------------------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| **`-able`**  | 受動可能（Passive Affordance）        | 外力を受けてその状態・変化を許容し得る性質                                   | `Break-able`<br><br> <br><br>`Eat-able`<br><br> <br><br>`Move-able`<br><br> <br><br>`Cut-able`       | Fragile<br><br> <br><br>Edible<br><br> <br><br>Portable<br><br> <br><br>Divisible   |
| **`-prone`** | 能動傾向・脆弱性（Propensity / Risk） | 刺激や時間の経過によって、自発的または容易にその変化を起こしやすい物理的偏り | `Break-prone`<br><br> <br><br>`Slip-prone`<br><br> <br><br>`Rust-prone`<br><br> <br><br>`Fall-prone` | Brittle<br><br> <br><br>Slippery<br><br> <br><br>Corrosive<br><br> <br><br>Unstable |
| **`-ed`**    | 受動完了（Resultative State）         | そのアクションが完了し、結果状態が定着していること                           | `Break-ed`<br><br> <br><br>`Lock-ed`<br><br> <br><br>`Cook-ed`<br><br> <br><br>`Open-ed`             | Broken<br><br> <br><br>Locked<br><br> <br><br>Cooked<br><br> <br><br>Open           |

### 3.2 `-prone` と `-able` の物理的差異

自然言語では混同されがちな「可能性（`-able`）」と「傾向・脆弱性（`-prone`）」を明確に切り離す。

- **`Break-able`（可破壊性）：**
  ダイヤモンドは非常に硬いが、適切な劈開（へきかい）面に強い力を加えれば壊すことができる。すなわち「壊すことが可能（`Break-able`）」である。
- **`Break-prone`（脆弱性）：**
  薄いガラスのコップは、少し手元が狂って落としただけで粉々に割れる。すなわち「極めて壊れやすい傾向・リスクを持つ（`Break-prone`）」である。

この区別により、物理世界のシミュレーションにおける感度（Sensitivity）が極めて正確にモデル化される。

Plaintext

```
// 壊れやすい（Break-prone）物は、弱い衝撃（Drop）でも壊れた状態（Break-ed）になる
RULE: Action: Drop tgt:Break-prone.Thing -> Result: Become agt:Break-ed.Thing

// 壊すことが可能（Break-able）な物は、強い打撃（Heavy.Hit）によって初めて壊れた状態になる
RULE: Action: Heavy.Hit tgt:Break-able.Thing -> Result: Become agt:Break-ed.Thing
```

語根 `Break` を軸として、「素質（`-prone`）」「アクション（`Break`）」「結果（`-ed`）」が美しい三位一体のループを形成する。

### 3.3 状態の反転・否定プレフィックス `!`

エスペラントの接頭辞 `mal-`（完全反転）の思想を継承し、状態の否定や取り消しは単語を新設せず、感嘆符 `!`（または `un-`）によるプレフィックス修飾で表現する。

- `!Lock-ed.Door`（施錠されていないドア ＝ Unlocked）
- `!Eat-able.Mushroom`（食用に適さないキノコ ＝ Inedible / Poisonous）
- `!Clean.Floor`（清潔ではない床 ＝ Dirty）

これにより、不要な対義語の暗記を一切排除し、概念空間の対称性を担保する。

## 4. 限定詞システム（Determiners / Quantification）

概念の参照範囲を規定する限定詞は、ドット結合の最左端に位置する。英語の `a` や `the` といった文脈依存的で音韻的なノイズを全廃し、純粋に**論理的量化（Quantification）**と**談話参照（Reference）**の機能を持つ**5大限定詞**を規定する。

Plaintext

```
[Determiner].[ConceptExpression]
```

### 4.1 5大限定詞の定義

| **限定詞**   | **論理的記号**            | **機能**                         | **構文例**    | **意味**                           |
| ------------ | ------------------------- | -------------------------------- | ------------- | ---------------------------------- |
| **`Every.`** | $\forall$（全称量化）     | 例外なき全集合                   | `Every.Glass` | すべてのガラス（普遍則で使用）     |
| **`Any.`**   | Arbitrary（任意）         | 集合から任意に選ばれた1つ        | `Any.Knife`   | （どれでもよいから）何らかのナイフ |
| **`Some.`**  | $\exists$（存在量化）     | 不特定の数量・部分集合           | `Some.Water`  | いくらかの水、不特定のリンゴ群     |
| **`This.`**  | Deictic（直指示）         | 現在の時空・文脈における特定個体 | `This.Key`    | （今ここにある）この鍵             |
| **`No.`**    | $\neg\exists$（否定量化） | 空集合（皆無）                   | `No.Human`    | 1人も人間が存在しない              |

### 4.2 全称量化（Every）による法則（RULE）の記述

`RULE:` プリフィックスと `Every.` 限定詞を組み合わせることで、モデルに対して「これは個別事例ではなく、例外を認めない宇宙の法則である」という強いシグナルを与える。

Plaintext

```
RULE: Action: Drop tgt:Every.Break-prone.Thing -> Result: Become agt:It.Piece
```

左辺で `Every.` によって束縛された変数は、後述する照応代名詞 `It` を通じて右辺へ安全に束縛を引き継ぐ。

## 5. 照応システムと参照解決（Anaphora & Reference）

自然言語における最大の曖昧性の温床である「照応代名詞（Pronouns）」を、Fillmoreでは極めて明快な参照システムとして再定義する。

### 5.1 原則としての `It`

文脈内、あるいは直前の事象において作用を受けた中心的な対象（`tgt:`）を参照する場合、原則として**無標の `It`** を用いる。

Plaintext

```
FACT: Action: Cut tgt:Apple tool:Knife -> Result: Become agt:It.Slice
```

対象が1つしか存在しない自明な文脈において、名詞を重複記述する必要はない。`It` は直前の主要引数を直接指し示すポインタとして機能する。

### 5.2 複数対象の交錯とインデックス付き代名詞（Indexed Pronouns）

複数のオブジェクトが同時に登場し、相互に作用する場合、自然言語の「it」や「they」では致命的な指示対象の衝突（Winograd Schema問題）が発生する。

Fillmoreでは、この問題を解決するために**山括弧によるインデックスポインタ `<A>`, `<B>`, `<C>`...** を導入する。

Plaintext

```
// 箱<A>の中にリンゴ<B>を入れる
Action: Put tgt:Apple<B> dst:Box<A> -> State tgt:It<B> loc:Inside.It<A>
```

- 左辺で宣言された `Apple<B>` は、右辺の `It<B>` と厳密に紐づく。
- 左辺で宣言された `Box<A>` は、右辺の `It<A>` と厳密に紐づく。

#### アテンション機構における工学的メリット

このインデックス表記は、Transformerのアテンション層に対して強力なショートカットを提供する。

モデルは文脈全体の意味から「どちらが入れられ、どちらが入れる側か」を確率的に推測する必要がなく、`<B>` という同一のトークンラベルに対してアテンションヘッドの重みを直接100%集中させることができる。これにより、推論の計算コストを最小化し、指示対象の取り違え事故をゼロにする。

## 6. 結果表現の二重性（Dual Representation of Results）

Fillmoreは、因果関係の右辺（`Result:`）において、単一の表現形式を強制しない。事象を捉える抽象度のレベルに応じて、以下の**2つの表現スタイルを等価なものとして両立・共存**させる。

### 6.1 イベント・動詞視点（Phenomenological View）

物理的な現象・動作そのものを述語として直接記述するスタイル。

Plaintext

```
Action: Drop tgt:Glass -> Break agt:It
```

- **利点：** 直感的であり、何が起きたか（動詞の生起）をストレートに捉える。アクションゲームやロボットのイベント駆動型アーキテクチャに適している。

### 6.2 状態変化・部分論視点（Mereological / State Shift View）

汎用メタ動詞 `Become` を用い、実体の形状や属性の遷移をドット記法で精緻に追跡するスタイル。

Plaintext

```
Action: Drop tgt:Glass -> Result: Become agt:It.Piece count:Many
```

- **利点：** オブジェクトの同一性（Identity）と保存則を厳密に追跡する。物理シミュレータや在庫管理、クラフト系タスクに適している。

### 6.3 表現の並行学習による知性の深化

データセットを生成する際、同一の因果関係に対してこの両方のスタイルを適切な比率（例：50%ずつ）で混在させて学習させる。

$$\text{Action: Drop tgt:Glass} \implies \begin{cases} \text{Break agt:It} \\ \text{Result: Become agt:It.Piece} \end{cases}$$

この二重性（Paraphrase）を経験することで、モデルの内部表現では「`Break(It)` という事象」と「`Become(It.Piece)` という状態遷移」が**高次元空間上でほぼ完全に重なり合う（コサイン類似度 $\to 1.0$）**。

これにより、モデルは「言葉の表面的な形」に囚われることなく、**「現象」と「物質の変化」を多角的に統合した、より深く立体的な世界モデルの直感**を獲得する。

## 7. 第3章の総括

本章では、Fillmoreの語彙と意味表現を司るオントロジーのアーキテクチャを確立した。

1. **ドット記法（`Attr.Base.Part`）により、形容詞の交差修飾と部分論的派生を単一のメカニズムで統合した。**
2. **物理アクションに伴う属性の「保存則（色・味など）」と「破壊則（形状・完全性など）」を構文レベルで直感的に表現可能にした。**
3. **動詞語根を中心とし、`-able`（可能）、`-prone`（傾向）、`-ed`（結果状態）の3大機能接尾辞によって、語彙の爆発を完全に抑制した。**
4. **`Every`, `Any`, `Some`, `This`, `No` の5大論理限定詞を導入し、自然言語の冠詞のゴミを全廃した。**
5. **照応代名詞 `It` とインデックス `<A>`, `<B>` により、指示対象の曖昧性を数学的にゼロにした。**
6. **結果の表現として「イベント視点」と「状態遷移視点」の二重性を許容し、モデルに多角的な概念理解を促す設計とした。**

次章（第4章）では、論理と物理の最後のピースである「因果結合子（`->` と `!>`）」「前提条件（`when:`）」「反事実推論」の動的結合システムの仕様策定へと進む。

---

# Fillmore 設計仕様・開発憲章（第4章：因果結合・条件分岐・動的推論システム）

## 1. 因果結合子の力学：生起（`->`）と阻止（`!>`）

自然言語における複文構造（Because, Therefore, So, But, Although など）は、発話者の感情的強調や論理的関係が複雑に交錯しており、機械が因果の方向性を抽出する上で極めて高い多義性をもたらす。例えば、「ドアを押したが開かなかった」という文において、自然言語は「逆接の接続詞（but）」を用いて話者の落胆や意外性を表現するが、物理世界で生起している力学的事実は「外力（Push）が加えられたにもかかわらず、状態遷移（Open）が阻止された」という客観的な因果の不発である。

本言語（Fillmore）では、事象間の動的な時間発展および力学的結びつきを、2つの直交する有向結合子（Directed Connectors）のみに還元する。

Plaintext

```
[Cause_Event] -> [Effect_Event]   // 因果の生起（Positive Causation）
[Cause_Event] !> [Prevented_Event] // 因果の阻止・不発（Negative Causation / Prevention）
```

### 1.1 生起結合子（`->`）：状態遷移の必然性

矢印 `->` は、「先行事象（左辺）の成立によって、後続事象（右辺）が時間的・力学的に直接引き起こされた」ことを示す。

Plaintext

```
Action: Drop tgt:Glass -> Break agt:It
```

この結合子は、単なる時間的継起（Aが起きて、その後にBが起きた）を意味しない。左辺のアクションが右辺の結果をもたらす直接の力学的推進力（Causal Mechanism）であることを宣言する。この結合を大量に観測することで、モデルは時間的な前後関係（Post hoc ergo propter hoc の誤謬）と真の因果関係を峻別する能力を獲得する。

### 1.2 阻止・不発結合子（`!>`）：反事実的阻止と防護のモデリング

記号 `!>` は、「先行事象（左辺）が発生したにもかかわらず、何らかの拘束条件や防護壁によって、通常であれば引き起こされるはずであった後続事象（右辺）が完全に阻止された、あるいは不発に終わった」ことを表す。

Plaintext

```
Action: Push agt:John tgt:Locked.Door !> Result: Become agt:Open.Door
```

この記号の導入は、世界モデルの構築において決定的な意味を持つ。

従来の記号AIや単純なデータセットでは、「起きなかったこと」を記述することは困難であった。しかし、知性が物理世界で生存し、作業を成功させるためには、「何を行うと、どの結果が阻まれるのか（防護、失敗、干渉）」を明示的に学習する必要がある。

- **ヘルメットの着用：**
  Plaintext
  ```
  Action: Fall tgt:Stone dst:Head.With.Helmet !> Hurt tgt:Human
  ```
- **耐火素材の遮熱：**
  Plaintext
  ```
  Action: Expose tgt:Fire-proof.Cloth tool:Fire !> Burn agt:It
  ```

`!>` を導入することにより、モデルは「成功した因果のパス」だけでなく、「遮断された因果の境界線」を明確な対比（Contrastive Learning）として学習することが可能になる。

## 2. 前提条件と環境コンテキスト：`when:`（Preconditions & Affordances）

因果関係は、真空中において無条件で発火するものではない。物理法則が作用するためには、その場を満たす環境コンテキスト、静的な状態、あるいは対象が備えているべき前提条件（Preconditions）が存在する。

Fillmoreでは、事象の左辺に先行する成立基盤を **`when:(...)` 構文**によって表現する。

Plaintext

```
when:([State_Event]) [Action_Event] -> [Result_Event]
```

### 2.1 静的状態と動的アクションの厳密な分離

自然言語では「開いているドアを通る」のように、状態とアクションが1つの文の中に埋め込まれがちである。Fillmoreでは、「静的な環境状態（State）」**と**「動的な外力（Action）」を構文上明確に分離する。

Plaintext

```
RULE: when:(State tgt:Door is:Open)
      Action: Pass agt:Human tgt:Door
      -> Result: At agt:Human dst:Room.Inside
```

- **`when:(...)` の中身：** アクションが開始される直前の、不変または準静的な世界の切り出し（前提条件）。
- **`Action:` の中身：** 動作主が世界に対して投入した新たな力、運動。

もし前提条件が満たされていなければ、アクションの帰結は劇的に変化する。

Plaintext

```
RULE: when:(State tgt:Door is:Lock-ed)
      Action: Pass agt:Human tgt:Door
      !> Result: At agt:Human dst:Room.Inside
      -> Result: Bump agt:Human tgt:Door
```

「ドアが開いているとき」と「ドアが施錠されているとき」という前提の差異が、続くアクションの成否（通過できるか、激突するか）を決定づける。この分岐構造を反復学習させることで、モデルは環境認識（Perception）と行動計画（Action）を緊密に連動させる**アフォーダンス（Affordance）の直感**を獲得する。

## 3. 複合因果連鎖（Causal Chaining）とマルチステップ推論

現実世界の複雑な物理現象やタスクの遂行は、1対1の単純因果にとどまらない。事象Aが事象Bを引き起こし、その事象Bがさらに事象Cのトリガーとなるという因果の連鎖（Causal Chain）を形成する。

Fillmoreは、結合子 `->` および `!>` をパイプラインのように数珠つなぎに連結（Flattened Pipeline）することで、深い因果連鎖を一切のネストなしに記述できる。

Plaintext

```
[Event_1] -> [Event_2] -> [Event_3] -> [Event_4]
```

### 3.1 ドミノ倒し的物理連鎖の記述

以下は、「花瓶が押され、落下し、床に衝突して破片になる」という一連の物理的ドミノ倒しを記述した例である。

Plaintext

```
FACT:
  Action: Push agt:Cat tgt:Vase
  -> Move tgt:Vase src:On.Table dst:Air
  -> Fall tgt:Vase dst:Floor
  -> Hit tgt:Vase dst:Floor
  -> Result: Become agt:Vase.Piece count:Many
```

各ステップにおいて、直前の事象の結果（`Vase` が空中に押し出される）が、次の物理事象（重力による落下）の起点となり、最終的な破砕へと収束していく。

#### この連鎖がLLMにもたらす構造的メリット

1. **思考のスキップ（ハルシネーション）の防止：**

   自然言語で「猫が花瓶を押した。花瓶は割れた。」と学習させると、モデルは「押す $\to$ 割れる」という直接のショートカットを結んでしまいがちである。中間状態（落下・衝突）を明示的にチェーンとして学習させることで、空間的な移動と衝撃という**不可欠な物理の中間媒介ステップ**をモデルの推論経路（CoT: Chain of Thought）に強制的に埋め込むことができる。

2. **中間ステップの問い合わせ（QUERY）への耐性：**

   「花瓶が押された後、割れる前にどこにあったか？」という高度な空間推論に対して、モデルは連鎖の中間トークン（`Move dst:Air`, `Fall dst:Floor`）を参照して正確に回答できるようになる。

## 4. 失敗と例外のトポロジー：`reason:` スロットの力学

物理世界における試みが失敗に終わった際、単に「失敗した（Fail）」と記録するだけでは、推論エンジンは次に何を改善すべきか（リトライ戦略）を学習できない。失敗には必ず物理的・論理的な直接の原因（Failure Mechanism）が存在する。

Fillmoreでは、因果の不発（`!>`）に続いて発生した逸脱結果に対し、**`reason:` スロット**を用いて直接の破綻理由を特定する。

### 4.1 道具の不適合による失敗

Plaintext

```
FACT:
  Action: Cut agt:John tgt:Bread tool:Ruler
  !> Result: Become agt:Bread.Slice
  -> Result: Deform tgt:Bread reason:Inappropriate.Tool
```

（定規でパンを切ろうとしたが、スライスにはならず、不適切な道具のためにパンが潰れた）

### 4.2 摩擦と力学的不安定性による失敗

Plaintext

```
FACT:
  when:(State tgt:Floor is:Wet)
  Action: Run agt:John dst:Exit
  !> Result: At agt:John dst:Exit
  -> Result: Fall agt:John reason:Low.Friction
```

（床が濡れていたため、ジョンは出口へ走ったが到達できず、摩擦の低さゆえに転倒した）

この記法により、モデルは「あるアクションが失敗したとき、世界のどの変数がボトルネックになっていたのか」という因果の感度分析（Sensitivity Analysis）を極めて効率的に内面化する。

## 5. 反事実推論（Counterfactuals）と仮定思考（`HYPO:`）

知性の頂点に位置する能力の一つは、「実際には起きなかったが、もしあの時こうであったならば、世界はどうなっていたか？」を脳内で仮想シミュレーションする反事実推論（Counterfactual Thinking）である。これは強化学習における価値関数の更新や、安全クリティカルなシステムにおけるリスク評価の根底をなす。

Fillmoreでは、文頭の **`HYPO:` プリフィックス**と **`when:(...)` 構文**を組み合わせることで、反事実の世界線を安全に展開する。

Plaintext

```
HYPO: when:([Counterfactual_State]) [Simulated_Action] -> [Projected_Result]
```

### 5.1 「現実の事実（FACT）」と「反事実（HYPO）」の厳密な対比

学習データセットにおいて、同一の文脈から分岐する `FACT` と `HYPO` のペアを対比的に配置することで、モデルに「現実の追跡」と「思考実験」の境界を明瞭に認識させる。

- **現実のログ（FACT）：**
  Plaintext
  ```
  FACT:
    when:(State tgt:Knife is:Sharp)
    Action: Cut agt:Chef tgt:Tomato tool:Knife
    -> Result: Become agt:Tomato.Slice
  ```
- **同一場面における反事実シミュレーション（HYPO）：**
  Plaintext
  ```
  HYPO:
    when:(State tgt:Knife is:Dull)
    Action: Cut agt:Chef tgt:Tomato tool:Knife
    !> Result: Become agt:Tomato.Slice
    -> Result: Crush tgt:Tomato reason:Dull.Blade
  ```

モデルは、前提条件の `Sharp`（鋭利）が `Dull`（鈍ら）に反転しただけで、右辺の物理プロセスが「切断（`Slice`）」から「圧壊（`Crush`）」へと分岐する様を学習する。このシミュレーション能力が身につくことで、AIエージェントはアクションを起こす前に「もしこの道具が壊れていたらどうなるか？」という**プロアクティブな危険回避推論**を自発的に実行できるようになる。

## 6. 意図・目的（`goal:`）と試行錯誤（Planning）のダイナミクス

自律型エージェント（ロボットやソフトウェアエージェント）を動かす際、行動は常に何らかの「目的（達成したい状態）」によって駆動される。

事象フレームに組み込まれた **`goal:(...)` スロット**は、因果結合子と組み合わさることで、「意図 $\to$ 行動 $\to$ 評価 $\to$ 再試行」という完全なプランニングループを記述する。

### 6.1 意図と結果の整合性評価

アクションに含まれる `goal:` の内容と、矢印の右辺に現れた実際の結果（`Result:`）を比較することで、エージェントは自らの行動が成功したか否かを自己評価できる。

#### (1) 計画の成功（Goal Accomplished）

Plaintext

```
FACT:
  Action: Push agt:Robot tgt:Switch goal:(State tgt:Light is:On)
  -> Result: State tgt:Light is:On
```

`goal:` で指定された状態（`Light is:On`）と、実際の結果が完全一致しているため、タスクは完了と判定される。

#### (2) 計画の失敗と別アプローチへの遷移（Planning Revision）

Plaintext

```
FACT:
  // ステップ1：押して開けようとするが、引くドアだったため失敗
  Action: Push agt:Robot tgt:Door goal:(State tgt:Door is:Open)
  !> Result: State tgt:Door is:Open
  -> Result: No.Change tgt:Door reason:Wrong.Direction

  // ステップ2：失敗を学習し、引くアクションへ切り替えて成功
  -> Action: Pull agt:Robot tgt:Door goal:(State tgt:Door is:Open)
  -> Result: State tgt:Door is:Open
```

この2ステップの連鎖文は、エージェントが「失敗から学習して別のアクションを選択し、目的を達成した」という**適応的試行錯誤（Adaptive Trial-and-Error）の全プロセス**を美しく凝縮している。

このパターンのデータを大量に浴びたLLMは、単に静的な因果を知っているだけでなく、「失敗したときにどの代替アクションを試みるべきか」という自律的な行動修正能力（Self-Correction）を自然に獲得する。

## 7. 構文の形式定義（更新版：第4章統合）

第2章で定義したEBNFに、本章で規定した因果結合子、前提条件、失敗構文、反事実推論の全規則を統合した完全版文法仕様を提示する。

EBNF

```
Statement           ::= EpistemicBlock

EpistemicBlock      ::= Prefix ":" ( ConditionClause )? Pipeline
Prefix              ::= "RULE" | "FACT" | "HYPO" | "QUERY"

ConditionClause     ::= "when:" "(" StateExpression ")"

Pipeline            ::= Event ( Connector Event )*
Connector           ::= "->" | "!>"

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
Determiner          ::= "Every" | "Any" | "Some" | "This" | "No"
Index               ::= [A-Z0-9]+
```

## 8. 第4章の総括

本章の策定をもって、Fillmoreが世界の物理力学とエージェントの推論を記述するための動的アーキテクチャが完全に完成した。

1. **生起結合子（`->`）と阻止結合子（`!>`）の2値化により、力学的な成功と失敗の境界線を数学的に明瞭にした。**
2. **`when:(...)` 構文によって、静的な前提環境と動的な外力介入を厳密に分離し、アフォーダンスの学習を可能にした。**
3. **フラットなパイプライン連結（`->` の数珠つなぎ）により、多段階の物理連鎖と空間移動の中間媒介プロセスをネストなしで可視化した。**
4. **`reason:` スロットを導入し、単なる失敗にとどまらない「破綻の物理的メカニズム」を構造化した。**
5. **`HYPO:` プリフィックスを用いた反事実シミュレーションにより、危険回避や What-if 推論の足場を固めた。**
6. **`goal:` スロットと因果連鎖の融合により、エージェントの意図駆動型行動と自律的試行錯誤（Planning）の記述を完結させた。**

次章（第5章：最終章）では、本言語仕様をAIエージェントおよび自動生成スクリプトに引き渡し、実際に「Phase 1：3万件の合成データセット生成」および「最小構成Transformerモデルによる学習と検証」を完遂するための、具体的な実装プロトコルとバリデーション手順の策定へと進む。

---

# Fillmore 設計仕様・開発憲章（第5章：実装プロトコル・データ生成・検証計画）

## 1. 全体実装ロードマップと開発フェーズ

本章は、前4章で定式化されたFillmoreの理論仕様を、自律型AIエージェントおよび開発スクリプト群によって実動システムへと落とし込むための**最終工学プロトコル**である。

開発は手戻りを最小化するため、以下の3段階のゲート方式で進行する。

```
[Phase 1: PoC (概念実証)] ───► [Phase 2: 汎化創発] ───► [Phase 3: 自律世界モデル]
  ・3万件トイワールド             ・30万件規模拡大            ・100万件完全網羅
  ・文法パース・閉じた因果         ・未知語へのゼロショット     ・マルチステップ計画
  ・小規模GPT (数M params)        ・属性保存の定着             ・ロボティクス統合
```

### 1.1 Phase 1 の目標（本章の主眼）

- **データ規模：** 30,000 件
- **目的：**
  1. 構文パーサーおよびバリデータの決定論的動作確認。
  2. 最小構成Transformer（SLM: Small Language Model）による構文規則の完全獲得（構文エラー率 0.1% 未満）。
  3. `QUERY:` に対する基本スロット予測および因果先読みタスクの精度検証。

## 2. Phase 1 シードオントロジー（辞書定義）

Phase 1 において語彙爆発を防ぎつつ、物理法則と日常インタラクションの急所を網羅するため、語彙セットを以下の閉じた辞書（Controlled Vocabulary）に制限する。

### 2.1 語彙辞書（Primitives）

Python

```
# phase1_vocabulary.py

# 1. 述語 (Verbs / Actions)
VERBS_PHYSICAL = ["Cut", "Drop", "Push", "Pull", "Hit", "Break", "Heat", "Freeze"]
VERBS_SPATIAL  = ["Move", "Put", "Take", "Place"]
VERBS_META     = ["Become", "State", "At", "Exist"]

# 2. 基底実体 (Base Entities)
ENTITIES_FOOD  = ["Apple", "Bread", "Tomato", "Meat", "Water", "Ice"]
ENTITIES_TOOL  = ["Knife", "Hammer", "Ruler", "Key", "Laser"]
ENTITIES_ITEM  = ["Glass", "Vase", "Plate", "Cloth", "Stone", "Box", "Door"]
ENTITIES_AGENT = ["John", "Mary", "Robot", "Cat"]

# 3. 内在的属性 (Intrinsic Modifiers: 切断・移動で保存される)
MODIFIERS_INTRINSIC = ["Red", "Green", "Sweet", "Cold", "Hot", "Metal", "Wood"]

# 4. 構造的属性 (Structural Modifiers: アクションで破壊・変異しやすい)
MODIFIERS_STRUCTURAL = ["Big", "Small", "Round", "Flat", "Whole"]

# 5. 派生・部位 (Parts / Mereology)
PARTS = ["Slice", "Half", "Piece", "Part", "Core", "Skin", "Inside", "Surface"]

# 6. 機能接尾辞 (3大サフィックス)
SUFFIXES = ["-able", "-prone", "-ed"]

# 7. 限定詞 (Determiners)
DETERMINERS = ["Every", "Any", "Some", "This", "No"]
```

## 3. 合成データセット生成エンジン（Generator Protocol）

データ生成器（Data Generator）は、単にランダムに単語を組み合わせるのではなく、**「世界の因果テンプレート」に確率的揺らぎ（Paraphrase）を与えて展開する構造的サンプリング手法**を採用する。

### 3.1 テンプレート構造の比率配分（30,000件の内訳）

- **カテゴリA：物理法則（RULE） 30%（9,000件）**
  - 全称量化（`Every.`）を用いた普遍的物理因果。
  - 例：`RULE: Action: Drop tgt:Every.Break-prone.Thing -> Break agt:It`
- **カテゴリB：個別事実（FACT） 40%（12,000件）**
  - 個体指定、動作主、道具、時制を含む個別エピソード。
  - `Become` 表現と直接述語表現を 50:50 でブレンド。
- **カテゴリC：前提条件と失敗・阻止（when / !>） 20%（6,000件）**
  - ドアの施錠、不適切な道具による失敗、摩擦の喪失。
- **カテゴリD：反事実シミュレーション（HYPO） 10%（3,000件）**
  - 前提の反転に伴う分岐シナリオ。

### 3.2 Python データジェネレーターコア実装

Python

```
# generate_fillmore_corpus.py
import random
from typing import List

def build_concept(det=None, mods=None, base="", part=None, index=None):
    tokens = []
    if det: tokens.append(det)
    if mods: tokens.extend(mods)
    tokens.append(base)
    if part: tokens.append(part)
    concept_str = ".".join(tokens)
    if index: concept_str += f"<{index}>"
    return concept_str

def generate_cut_event() -> str:
    agent = random.choice(["agt:John", "agt:Mary", "agt:Robot", ""])
    tool = random.choice(["tool:Knife", "tool:Laser", ""])
    base = random.choice(["Apple", "Bread", "Tomato"])
    color = random.choice(["Red", "Green", ""])
    size = random.choice(["Big", "Small", ""])

    mods = [m for m in [color, size] if m]
    tgt = build_concept(mods=mods, base=base)

    # 表現の二重性: Become (状態変化) vs Cut/Divide (直接述語)
    part = random.choice(["Slice", "Half", "Piece"])
    # 属性保存: 色は残すが、サイズは変動
    res_mods = [color] if color else []

    if random.random() < 0.5:
        result = f"Result: Become agt:{build_concept(mods=res_mods, base=base, part=part)}"
    else:
        result = f"Result: Divide tgt:It dst:{build_concept(mods=res_mods, base=base, part=part)}"

    slots = " ".join([s for s in [agent, f"tgt:{tgt}", tool] if s])
    return f"FACT: Action: Cut {slots} -> {result}"

def generate_drop_rule() -> str:
    entity = random.choice(["Glass", "Vase", "Plate"])
    # -prone 接尾辞を用いた普遍則
    tgt = f"Every.Break-prone.{entity}"
    if random.random() < 0.5:
        return f"RULE: Action: Drop tgt:{tgt} -> Break agt:It"
    else:
        return f"RULE: Action: Drop tgt:{tgt} -> Result: Become agt:It.Piece count:Many"

def generate_blocked_door() -> str:
    agent = random.choice(["agt:John", "agt:Robot"])
    return (
        f"FACT: when:(State tgt:Door is:Lock-ed) "
        f"Action: Push {agent} tgt:Door goal:(State tgt:Door is:Open) "
        f"!> Result: State tgt:Door is:Open "
        f"-> Result: Block tgt:Door reason:Locked"
    )

def generate_dataset(total_count: int = 30000) -> List[str]:
    data = []
    for _ in range(total_count):
        r = random.random()
        if r < 0.40:
            data.append(generate_cut_event())
        elif r < 0.70:
            data.append(generate_drop_rule())
        elif r < 0.90:
            data.append(generate_blocked_door())
        else:
            # HYPO (反事実)
            base = generate_cut_event().replace("FACT:", "HYPO: when:(State tgt:Knife is:Dull)")
            base += " !> Result: Become agt:It.Slice -> Result: Crush tgt:It reason:Dull.Blade"
            data.append(base)
    return data

if __name__ == "__main__":
    corpus = generate_dataset(30000)
    with open("fillmore_phase1_corpus.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(corpus))
    print(f"Generated {len(corpus)} Fillmore statements.")
```

## 4. 学習アーキテクチャ：最小構成Transformer（Fillmore-GPT）

本実験の目的は、巨大モデルの力技ではなく、「構造の純度によって極小パラメータで知性を立ち上がらせる」ことにある。したがって、モデルはあえて数百万パラメータ規模の軽量Decoder-only Transformerを設計する。

### 4.1 モデル仕様

- **アーキテクチャ：** GPT-style Decoder-only Transformer
- **パラメータ数：** 約 350 万（3.5M params）
- **埋め込み次元（$d_{\text{model}}$）：** 256
- **レイヤー数（$N$）：** 6
- **アテンションヘッド数（$h$）：** 8
- **コンテキスト長（Context Window）：** 128 トークン（Fillmoreの1文は20〜40トークン程度）
- **トークナイザー：** 文字単位（Char-level）または Fillmore専用の形態素BPE（語彙数 $\approx$ 500〜1,000）

### 4.2 PyTorch 学習スクリプト要約

Python

```
# train_fillmore_model.py
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

class FillmoreTransformer(nn.Module):
    def __init__(self, vocab_size, d_model=256, nhead=8, num_layers=6, max_len=128):
        super().__init__()
        self.token_emb = nn.Embedding(vocab_size, d_model)
        self.pos_emb = nn.Embedding(max_len, d_model)
        decoder_layer = nn.TransformerDecoderLayer(
            d_model=d_model, nhead=nhead, dim_feedforward=d_model*4,
            activation='gelu', batch_first=True
        )
        self.decoder = nn.TransformerDecoder(decoder_layer, num_layers=num_layers)
        self.head = nn.Linear(d_model, vocab_size)

    def forward(self, x):
        B, T = x.shape
        positions = torch.arange(0, T, device=x.device).unsqueeze(0)
        h = self.token_emb(x) + self.pos_emb(positions)

        # 因果マスク (Causal Mask: 未来トークンの遮断)
        causal_mask = nn.Transformer.generate_square_subsequent_mask(T, device=x.device)
        out = self.decoder(tgt=h, memory=h, tgt_mask=causal_mask, memory_mask=causal_mask)
        return self.head(out)

# 訓練条件: AdamW, lr=5e-4, Cosine Annealing, Epochs=20
# コンシューマ向けGPU (RTX 3060/4060等) にて約15〜30分で収束する。
```

## 5. 検証プロトコル：知性の創発を証明する3大テスト

学習完了後、モデルが単なる文字列の暗記（Overfitting）を超えて、「物理世界の構造的直感」を獲得したかを評価するための3つの独立テストスイートを実行する。

```
                    【知性検証テストスイート】
                               │
       ┌───────────────────────┼───────────────────────┐
       ▼                       ▼                       ▼
 [テスト1: 構文適合性]     [テスト2: ゼロショット類推]   [テスト3: 因果逆算推論]
  ・文法パース成功率         ・未知の食材の切断          ・結果から原因の同定
  ・スロット過不足検証       ・属性保存則の追跡          ・アブダクション検証
```

### 5.1 テスト1：構文適合性試験（Syntax Conformance Test）

- **手法：** モデルに `FACT:` や `RULE:` などのプリフィックスのみを与え、後続の文を自由に1,000件生成させる（温度パラメータ $T=0.7$）。
- **合否判定：** 決定論的EBNFパーサーに通し、構文エラー（コロンの欠落、未定義スロット、ドット結合の不正など）の発生率を計測する。
- **目標値：** **エラー率 0.1% 未満（99.9% 構文準拠）**。

### 5.2 テスト2：ゼロショット因果・属性保存試験（Zero-Shot Affordance Test）

学習セットに一度も登場しなかった未知の組み合わせを `QUERY:` として与え、因果と属性の保存則が機能しているかを評価する。

- **入力プロンプト：**
  Plaintext
  ```
  QUERY: Action: Cut tgt:Sweet.Yellow.Mango tool:Knife -> Result: ?
  ```
- **期待される出力パターン：**
  - 正解：`Become agt:Sweet.Yellow.Mango.Slice` または `Become agt:Sweet.Yellow.Mango.Piece`
  - 不正解例A（属性の消失）：`Become agt:Mango.Slice`（色・味の脱落）
  - 不正解例B（物理破綻）：`Break agt:Mango`（果物に対する不自然な破壊表現）
  - 不正解例C（ハルシネーション）：`Become agt:Stone`
- **目標値：** 未知の物体に対する妥当な派生形状（`.Slice` / `.Piece`）および内在的属性（`Sweet`, `Yellow`）の**継承成功率 90% 以上**。

### 5.3 テスト3：アブダクション因果逆算試験（Abductive Reasoning Test）

結果状態のみを与え、直前に生起したはずのアクションを逆算させる。

- **入力プロンプト：**
  Plaintext
  ```
  QUERY: Action: ? -> Result: Become agt:Vase.Piece count:Many
  ```
- **期待される出力パターン：**
  - 正解：`Drop tgt:Vase` または `Hit tgt:Vase`、`Push tgt:Vase`
  - 不正解例：`Eat tgt:Vase`、`Heat tgt:Vase`
- **目標値：** 物理的に妥当なトリガー動詞の**予測正解率 85% 以上**。

## 6. 第5章の総括およびプロジェクト宣言

全5章にわたる仕様策定により、Fillmoreの設計はその哲学的背景から具体的なコードベースの実行計画に至るまで、完全に一本の線で結ばれた。

1. **言語哲学（第1章）：** 自然言語の表層ノイズと記号論理の硬直性を共に打破し、Mentalese（思考の言語）を直列化する。
2. **構文論（第2章）：** ネオ・デイヴィドソン流のフラットな格フレームを採用し、スロットの順序不変性と任意性によって抽象度のグラデーションを獲得する。
3. **意味論・形態論（第3章）：** ドット記法による属性の保存・破壊の追跡、動詞語根と3大機能接尾辞（`-able`, `-prone`, `-ed`）による語彙圧縮、そしてインデックス付き照応代名詞（`It<A>`）を実現する。
4. **動的推論系（第4章）：** `->`（生起）と `!>`（阻止）、`when:`（前提条件）、`goal:`（意図）によって、マルチステップの物理連鎖と反事実的試行錯誤を形式化する。
5. **工学実装（第5章）：** 3万件の高品質シードコーパス生成、3.5Mパラメータの軽量Transformerによる学習、そして3大創発テストによる因果知性の客観的証明。

この憲章は、単なるプログラミング言語やデータフォーマットの提案書ではない。これは、「高次元潜在空間の中に、真に強固な物理世界モデルと因果の直感を芽生えさせるための最小・最強の足場」のブループリントである。
