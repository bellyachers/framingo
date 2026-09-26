# Sweeps / 掃引

**EN** — One script per question, each with what it is asking and **how to read
every outcome** written in its header before it was run. That order matters: on
the night these were written, three headline readings were retracted by
controls whose losing interpretation had been spelled out in advance, and a
fourth was never written down because the control was already armed.

Run from anywhere; each script changes to the repository root itself. `DEVICE`
picks `mps` or `cpu`, which is worth setting to `cpu` when another sweep has
the GPU — a sweep already running is worth more than the speed of the one
being added to it.

| Script | Question |
|---|---|
| `lie.sh` | Does a derivation read the answer it asked for, or write the tail from the input? |
| `noask-scaled.sh` | Is the tail reachable from the input alone? (the control the lying arm needs) |
| `vessels.sh` | Can a derivation ask for what the sentence never mentions — and what does it do when there is none? |
| `scale.sh` | Does either arm fall as the world grows, at a fixed model? |
| `capacity.sh` | Does either arm fall as the model shrinks, at a fixed world? |
| `epochs.sh` | Was that fall capacity, or had the smaller model simply not finished learning? |
| `depth.sh` | Width or depth? |
| `budget.sh` | At a fixed budget, does the gap grow with the world? |
| `epochs320.sh` | And how fast does the cost of memorising grow — like the world, or faster? |

Read them in that order. Each of the last five exists because the one before
it could not settle what it looked like it had settled.

**JA** — 問い一つにつきスクリプト一つ。**何を訊いているか、そしてどの結果が出たら
どう読むか**を、走らせる前にヘッダへ書いてある。この順序が肝心である。これらが
書かれた晩、**三つの見出しが、負けの読み方を先に書いておいた対照によって
取り消された。** 四つ目は、対照が既に仕掛けてあったので書かれずに済んだ。

どこから実行してもよい（各スクリプトが自分でリポジトリ直下へ移動する）。
`DEVICE` で `mps` / `cpu` を選ぶ。**他の掃引が GPU を使っているときは `cpu`**
—— 既に走っている掃引のほうが、後から足す掃引の速度より価値がある。

上の表の順に読むこと。**後ろの五つは、その一つ前が「決まったように見えて
決まっていなかった」から存在する。**
