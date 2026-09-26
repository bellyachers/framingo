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
| `docs/language-spec.md` | Language specification, Gisaburo v1. Ch.2–4 of the original draft, moved unchanged and numbered as before |
| `docs/overview.md` | Original draft, kept for the record. Only ch.1 and ch.5 remain, both superseded by `core-thesis.md` |

Chapter 7 of the charter demotes the language specification to *means, not
claim*. Keep that hierarchy: the claim is the separation of logic from
knowledge; the language is how it is carried.

## Measuring / 測ること

These were arrived at by getting them wrong, each more than once. They are here
rather than in the working journal because they are settled.

**Count what an arm saw, and what a test set is actually testing.**
"There is a control arm" is not the claim; "the control arm was trained on N of
the thing it is meant to bound" is. Eighteen runs once compared a holdout arm
against a control that had been trained on **zero** examples of the shape, and
the result read as a clean negative. Separately, an arm that looked as though
it were ignoring a lookup turned out to be in a world where the lookup decided
almost nothing.

The same applies to the test set. A corpus built to measure whether a model
uses what it fetched turned out to need the fetch in 24% of its examples, so
the headline figure was two thirds a measurement of something else. Split the
result by whether the thing being tested was in play, and report the split.

And count how many distinct situations the world holds before drawing a
corpus from it. One world held 2,916 and a run asked for 8,500; the builder,
which discards repeats, drew for ever. Twenty minutes of CPU at 100% with no
epoch printed is what a slow model looks like too.
**対照も、テスト集合も、それが何を見て何を試しているかを数えるまでは、そう呼べない。
世界が相異なる状況を何通り持つかも、そこから引く前に数える。**

**Quote a detection rate with a false-alarm rate or not at all.**
An empty core flags everything, so it "detects" 100% of fabrications while
rejecting 100% of sound output. Either figure alone is satisfied by a checker
that refuses everything. Charter proposition 2 was amended for this.
**検出率は誤検出率と対でなければ意味がない。**

**Write down what you expect to go wrong before the numbers exist.**
A 32% false-alarm rate was about to be reported as a property of the Grounding
Constraint — "being right is not the same as being able to show why" — and was
a bug in the grader. It had been flagged as a thing to watch for beforehand,
which is the only reason it was investigated rather than explained.
**結果を見る前に、何が怪しいかを書き下しておく。**

**Re-measure the load-bearing claims yourself, including your own.**
Agents' reports and one's own scripts have both been wrong here: a measurement
was rebuilt three times before it agreed with itself, and a defect was reported
with an example that occurs nowhere in the data. A number that decides something
is worth computing twice by different means.
**主要な主張は、自分のものも含めて測り直す。**

**Feed the grader the right answer before feeding it a model's.**
A grader that scores the gold at less than 1.000 is reporting the model
failing at something the harness is doing, and it reads exactly like a
negative result. One corpus's first stretch is a *question*; grading it in as
a step of the derivation compared a question against a meaning containing
none, so every output scored zero however good it was. The check costs a
second and catches the whole class.
**採点器に gold を食わせて 1.000 が出ることを、モデルを食わせる前に確かめる。**

**Name a metric by imagining it non-zero.**
`false_alarm_rate` counts benign outputs the verifier flags, and the name
assumes a correct answer ought to ground — which is the assumption the charter
denies. It read correctly while it was zero, which it is wherever the model
looks its words up. The first arm that did not look them up put a fifth of its
correct answers there, and the name reported the verifier working as the
verifier failing.
**指標の名前は、それが 0 でない状況を想像してから付ける。**

**Before removing something from an experiment, grep the charter for it.**
A corpus was once designed to test "pure logic" by stripping the world away,
and chapter 3 says in as many words that cutting that layer leaves nothing
standing. Reaching for a familiar experimental shape is not the same as
choosing one.
**実験から何かを取り除く前に、それを憲章で grep する。**

### Running things / 実行

- **Do not pipe a long-running job through `grep`.** Its output is block
  buffered, so a running job and a finished one look the same, and a traceback
  is swallowed. Write the whole log to a file and filter when reading it.
  Note also that **0% CPU does not distinguish "hung" from "done"**.
- **Replace code between two boundaries you have asserted, never between two
  searched-for markers.** Cutting from a function's `def` to the next section
  comment has twice removed every function in between, and the file still
  imports. Find both ends, assert what is at each, then splice.
- **Do not edit a shell script while it is running.** zsh reads a script
  incrementally and will resume from the old byte offset into new text.
- **A `pgrep` for a script name matches whoever is asking.** A chained job that
  waits with `while pgrep -f "run-x.sh"` waits for ever if any shell watching
  the sweep has that string in its own command line. Two sweeps sat idle for
  twenty minutes behind a monitoring shell. The same match then made a running
  job look finished and a live one look dead.
- **Count what a worktree holds that git does not, before removing it.**
  `git worktree remove --force` deletes ignored files too, and `runs/` is
  ignored. Needing `--force` at all is the signal that something in there is
  not tracked; `git status --ignored --short` says what. A night of run
  outputs went this way, recoverable only by re-running them.
- **Look twice, with a gap, before concluding a job has stopped.** One reading
  of a log tail says where a job was, not that it is still there. A run at
  epoch 90 was written up as having died; it was at epoch 115.
- **After killing a sweep, check what survived.** Killing the script and the
  job it had started leaves any child already spawned running, orphaned and
  invisible to the next `pgrep` for the script. It then finishes against
  whatever the tree says now, and writes its result beside the runs that used
  the old code.
- **Give a parallel agent its own `.venv` in its worktree.** `VIRTUAL_ENV`
  points at the main checkout, so `uv run --active` there rewrites the editable
  install and a job running in the main tree starts importing half-finished code.
- **Work in a worktree while an experiment is running.** Every run is a fresh
  process that imports `src/` when it starts, so a sweep on its third run reads
  whatever the tree says then, not what it said when the sweep began.
  `uv sync` in a new worktree takes seconds, the packages being hardlinked from
  the cache. **But a worktree protects the other tree, not itself**: editing
  the file a job in *this* tree will read next has cost a run here too.

## Commits / コミット

Written in English, with a body that explains **why**, not only what. A reader
should be able to reconstruct the reasoning without the conversation. Rejected
alternatives and the argument that decided against them belong in the body.

Sign off with:

    Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>

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
