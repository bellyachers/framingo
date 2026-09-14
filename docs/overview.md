> **Status of this document / 本文書の位置づけ**
>
> **EN** — This is the original draft, kept for the record. Its chapters 2–4, the language specification, have moved to `language-spec.md`. Chapter 1 (background) and chapter 5 (implementation protocol) remain here and are superseded by the charter, `core-thesis.md`; see its Appendix B.
>
> **JA** — 本ファイルは記録として残す初期草稿である。第2〜4章（言語仕様）は `language-spec.md` に移した。ここに残る第1章（背景）と第5章（実装プロトコル）は、憲章 `core-thesis.md` によって置き換えられている。同書の付録Bを参照。

---

# Framingo 設計仕様・開発憲章（第1章：背景と設計思想）

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

私たちが開発する言語（Framingo）は、人間やエージェントの脳内で起きているこの「認知のスナップショットと因果ベクトル」を、1ミリの歪みもなく、最小の摩擦でそのままテキストストリームとしてダンプ（直列化）した言語である。

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

Framingoは、「AIエージェント自身が世界をシミュレートし、計画を練り、思考ログを保存するためのネイティブコード」として機能する。

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

> *Chapters 2–4 → [`language-spec.md`](language-spec.md) / 第2〜4章 → [`language-spec.md`](language-spec.md)*

---

# Framingo 設計仕様・開発憲章（第5章：実装プロトコル・データ生成・検証計画）

## 1. 全体実装ロードマップと開発フェーズ

本章は、前4章で定式化されたFramingoの理論仕様を、自律型AIエージェントおよび開発スクリプト群によって実動システムへと落とし込むための**最終工学プロトコル**である。

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
    print(f"Generated {len(corpus)} Framingo statements.")
```

## 4. 学習アーキテクチャ：最小構成Transformer（Framingo-GPT）

本実験の目的は、巨大モデルの力技ではなく、「構造の純度によって極小パラメータで知性を立ち上がらせる」ことにある。したがって、モデルはあえて数百万パラメータ規模の軽量Decoder-only Transformerを設計する。

### 4.1 モデル仕様

- **アーキテクチャ：** GPT-style Decoder-only Transformer
- **パラメータ数：** 約 350 万（3.5M params）
- **埋め込み次元（$d_{\text{model}}$）：** 256
- **レイヤー数（$N$）：** 6
- **アテンションヘッド数（$h$）：** 8
- **コンテキスト長（Context Window）：** 128 トークン（Framingoの1文は20〜40トークン程度）
- **トークナイザー：** 文字単位（Char-level）または Framingo専用の形態素BPE（語彙数 $\approx$ 500〜1,000）

### 4.2 PyTorch 学習スクリプト要約

Python

```
# train_fillmore_model.py
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

class FramingoTransformer(nn.Module):
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

全5章にわたる仕様策定により、Framingoの設計はその哲学的背景から具体的なコードベースの実行計画に至るまで、完全に一本の線で結ばれた。

1. **言語哲学（第1章）：** 自然言語の表層ノイズと記号論理の硬直性を共に打破し、Mentalese（思考の言語）を直列化する。
2. **構文論（第2章）：** ネオ・デイヴィドソン流のフラットな格フレームを採用し、スロットの順序不変性と任意性によって抽象度のグラデーションを獲得する。
3. **意味論・形態論（第3章）：** ドット記法による属性の保存・破壊の追跡、動詞語根と3大機能接尾辞（`-able`, `-prone`, `-ed`）による語彙圧縮、そしてインデックス付き照応代名詞（`It<A>`）を実現する。
4. **動的推論系（第4章）：** `->`（生起）と `!>`（阻止）、`when:`（前提条件）、`goal:`（意図）によって、マルチステップの物理連鎖と反事実的試行錯誤を形式化する。
5. **工学実装（第5章）：** 3万件の高品質シードコーパス生成、3.5Mパラメータの軽量Transformerによる学習、そして3大創発テストによる因果知性の客観的証明。

この憲章は、単なるプログラミング言語やデータフォーマットの提案書ではない。これは、「高次元潜在空間の中に、真に強固な物理世界モデルと因果の直感を芽生えさせるための最小・最強の足場」のブループリントである。
