# Working conventions / 作業規約

## Language / 言語

Conversation with the maintainer is in **Japanese**. All documents are
**bilingual EN/JA** — bilingual headings, EN block then JA block per section,
bilingual table cells (`Core completeness / 核の完全性`). Diagrams and Framingo
code samples stay single, being language-neutral.

The Japanese text is the primary source; the English is the door. Describing an
English-lexified formal language *in* English makes it impossible to separate
design intuitions from English leakage.

## Fixed terminology / 訳語の固定

| 日本語 | English |
|---|---|
| 接地制約 | Grounding Constraint |
| 論理コア / 翻訳境界 / 知識供給層 | Logic Core / Translation Boundary / Knowledge Layer |
| 最小核 | minimal core |
| 検証器 | verifier |
| 可読な再帰 | legible recursion |
| 言語的自己拡張 | linguistic self-extension |
| 表現被覆率 / 導出受理率 / 接地率 | expressive coverage / derivation acceptance rate / grounding rate |
| 二信号の要請 | the two-signal requirement |

## Documents / 文書の階層

| File | Status |
|---|---|
| `docs/core-thesis.md` | **Current charter.** Ch.1–11 plus appendices |
| `docs/version-names.md` | Version codename roster and the rule for assigning names |
| `docs/language-spec.md` | Language specification, Gisaburo v1. Ch.2–4 of the original draft, moved unchanged and numbered as before; Japanese only so far |
| `docs/overview.md` | Original draft, kept for the record. Only ch.1 and ch.5 remain, both superseded by `core-thesis.md` |

Chapter 7 of the charter demotes the language specification to *means, not
claim*. Keep that hierarchy: the claim is the separation of logic from
knowledge; the language is how it is carried.

## Commits / コミット

Written in English, with a body that explains **why**, not only what. A reader
should be able to reconstruct the reasoning without the conversation. Rejected
alternatives and the argument that decided against them belong in the body.

Sign off with:

    Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>

## After cloning / clone 後に必須

```sh
git config core.hooksPath .githooks
```

`.githooks/pre-commit` refuses any commit whose `user.email` is not a
`@users.noreply.github.com` address. This repository is public; a commit email is
permanent, exposed through the `.patch` URL and the REST API, and harvested.
Nothing can be removed after the first push. Git cannot force hooks from the
repository side, so this must be set per clone.

これは憲章の手口をリポジトリ自身に適用したものである。「気をつける」のではなく、
誤りを機械的に犯せなくする。

## Naming / 命名

Versions are codenamed for linguists whose thesis that version embodies, assigned
**after** the version's content is settled. See `docs/version-names.md`. Proposals
are welcome from anyone, human or otherwise, provided the match is stated.
