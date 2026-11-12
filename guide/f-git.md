# 付録F. git と GitHub の使い方

## この付録でわかること

- git と GitHub のしくみと、よく出てくる言葉
- 最初に1回だけする設定
- SSH キーを作って GitHub に登録し、パスワードなしでクローン・プッシュする方法
- 新しくリポジトリを作って、GitHub に置く方法
- ふだんの記録（コミット・プッシュ・プル）と、前の状態に戻す方法
- ブランチで試す方法と、両方で変えてしまったときの直し方
- ラズパイ・Jetson・別の PC からクローンできるようにする方法（GitHub を通す・通さない）
- よくあるエラーと直し方

ふだんのコミットとプッシュは、VS Code のソース管理のボタンでもできます（3章・4章）。この付録では、同じことをコマンドで行う方法と、ボタンだけではわかりにくい設定（SSH キーなど）をまとめます。
コマンドの中の単語（`git` や `ssh-keygen` など）をクリックすると、その意味が吹き出しで出ます。

## git と GitHub

| もの | 何か | どこにある |
| --- | --- | --- |
| **git** | ファイルの変更を記録するソフト。いつ・何を変えたかを残し、前の状態に戻せる | 自分の PC |
| **GitHub** | git の記録を置いておく、インターネット上の場所。別の PC や、ほかの人と共有する | github.com |
| **gh**（GitHub CLI） | ターミナルから GitHub を操作するコマンド。ログインする・リポジトリを作る | 自分の PC |

git だけでも、PC の中で記録をとれます。GitHub に置くと、PC が壊れてもコードが残り、別の PC やラズパイから同じコードを取ってこられます。

### よく出てくる言葉

| 言葉 | 意味 |
| --- | --- |
| リポジトリ（repository、略して repo） | 記録をとる単位。1つのフォルダと、その中の変更の歴史の全部。このガイドでは、1つのプロジェクト = 1つのリポジトリ |
| コミット（commit） | 1回分の記録。「その時点のファイルの状態」と「何をしたかの説明」のセット。あとでこの状態に戻せる |
| ステージ（stage） | 次のコミットに入れる変更を、選んでおく場所。`git add` で入れる |
| リモート（remote） | 手元のリポジトリの、別の場所にあるコピー。ふつうは GitHub。名前は **origin** にするのが決まり |
| プッシュ（push） | 手元のコミットを、リモートに送る |
| プル（pull） | リモートの新しいコミットを、手元に取り込む |
| クローン（clone） | リモートのリポジトリを、まるごと手元にコピーする。最初の1回だけ |
| ブランチ（branch） | コミットの流れの枝。中心の枝は **main**。試しに変えるときに枝を分ける |
| タグ（tag） | コミットに付ける名前の印。`v1.0.0` など（17章） |
| `.gitignore` | git で記録しないファイルを書いておくファイル |

### ファイルが通る場所

![git でファイルが通る場所](images/git-areas.svg)

1. 作業フォルダで、ファイルを書き換える
2. `git add` で、次のコミットに入れる変更を選ぶ（ステージに入れる）
3. `git commit` で、手元の記録に残す。ここまでは PC の中だけで、インターネットは要らない
4. `git push` で、GitHub に送る

別の PC では、最初に `git clone` で GitHub から全部をコピーし、そのあとは `git pull` で新しい分だけを取り込みます。

- 記録は、プロジェクトのフォルダの中の `.git` という隠しフォルダに入っています。**`.git` を消すと、記録が全部消えます**
- VS Code のソース管理の **＋**（Stage Changes）が `git add`、**Commit** が `git commit`、**Sync Changes** が `git pull` と `git push` です

## 最初に1回だけする設定

### git と gh を入れる

```bash
sudo apt install git gh
git --version
```

`git version 2.…` と出れば入っています。

### 名前とメールアドレスを登録する

コミットには、誰が記録したかとして、名前とメールアドレスが入ります。PC ごとに、最初に1回だけ設定します。

```bash
git config --global user.name "Taro Yamada"
git config --global user.email "12345678+ユーザー名@users.noreply.github.com"
git config --global init.defaultBranch main
git config --global pull.rebase false
git config --global core.editor nano
git config --global --list
```

| 設定 | 意味 |
| --- | --- |
| `user.name` | コミットに入る名前。GitHub のユーザー名でも、本名でもよい |
| `user.email` | コミットに入るメールアドレス。GitHub に置くと、コミットを見た人に見える |
| `init.defaultBranch main` | 新しく作るリポジトリの最初のブランチを `main` にする（GitHub と合わせる） |
| `pull.rebase false` | `git pull` のとき、両方で変えていたら「マージ」でまとめる（下の「両方で変えていたとき」） |
| `core.editor nano` | コミットの説明を書くときなどに開くエディタを、nano にする |

- メールアドレスを人に見せたくないときは、GitHub の **Settings → Emails** の「Keep my email addresses private」に ☑ を入れ、そこに出ている `数字+ユーザー名@users.noreply.github.com` を使います
- 最後の `git config --global --list` で、設定した内容が出ます。設定は `~/.gitconfig` に入ります
- `--global` は「この PC の、このユーザーの全部のリポジトリ」という意味です

### GitHub のアカウント

[github.com](https://github.com) でアカウントを作ります（無料）。非公開のリポジトリも無料で作れます。
**2段階認証**（ログインのときに、スマホのアプリなどでもう1つ確かめる）も設定しておきます。GitHub の **Settings → Password and authentication** にあります。

## GitHub とつなぐ方法を選ぶ

非公開のリポジトリをクローンしたり、プッシュしたりするには、PC が「自分である」ことを GitHub に示す必要があります。**GitHub のパスワードは使えません**（打っても断られます）。方法は2つあります。

| 方法 | リポジトリの URL | 準備 | 向いているとき |
| --- | --- | --- | --- |
| **SSH キー**（おすすめ） | `git@github.com:ユーザー名/collar.git` | 鍵を作って GitHub に登録する（下） | ふだんの開発。ラズパイ・Jetson など、ブラウザがない機械 |
| HTTPS と gh | `https://github.com/ユーザー名/collar.git` | `gh auth login` で、ブラウザからログインする | 手早く始めたいとき。VS Code の Publish to GitHub もこちら |

どちらでも、できることは同じです。1つの PC で両方を使ってもかまいません。この付録では SSH キーを使います。

## SSH キーを作って GitHub に登録する

![SSH キーで GitHub とつなぐ](images/git-ssh-keys.svg)

SSH キーは、**秘密鍵**と**公開鍵**の2つで1組のファイルです。

| ファイル | 中身 | 扱い |
| --- | --- | --- |
| `~/.ssh/id_ed25519` | 秘密鍵 | **誰にも渡さない。** ほかの機械にコピーしない、GitHub にも上げない |
| `~/.ssh/id_ed25519.pub` | 公開鍵（`.pub` は public の略） | 渡してよい。GitHub に登録する |

GitHub は、登録された公開鍵と組になる秘密鍵を持っている機械だけを、自分として通します。
鍵は**機械ごとに1組**作ります（PC・ノート PC・ラズパイ・Jetson でそれぞれ）。どれかをなくしたら、GitHub の一覧からその鍵だけを消せば、ほかの機械はそのまま使えます。

### 1. 鍵があるか確かめる

```bash
ls ~/.ssh
```

`id_ed25519` と `id_ed25519.pub` があれば、もう作ってあります。「3. GitHub に公開鍵を登録する」に進みます。
`No such file or directory` と出たり、`known_hosts` や `authorized_keys` しかなかったりすれば、次で作ります。

### 2. 鍵を作る

```bash
ssh-keygen -t ed25519 -C "main-pc"
```

次のように聞かれます。

| 聞かれること | 答え方 |
| --- | --- |
| `Enter file in which to save the key (/home/ユーザー名/.ssh/id_ed25519):` | そのまま Enter（決まった場所に作る） |
| `Enter passphrase (empty for no passphrase):` | パスフレーズ（鍵のパスワード）を打つ。画面には何も出ない。PC を盗まれても、鍵を使われないようにするため |
| `Enter same passphrase again:` | もう一度、同じものを打つ |

`The key's randomart image is:` のあとに、四角い模様が出れば完了です。

- `-t ed25519` は鍵の種類です。いまのおすすめの種類で、短くて安全です
- `-C` は鍵に付けるメモです。どの機械の鍵かがわかる名前にします（GitHub の一覧で見分けるため）
- 画面のないラズパイなどで、自動で `git pull` させたいときは、パスフレーズを空（Enter だけ）にします。その代わり、その鍵は「読むだけ」で登録します（下の「別の機械からクローンできるようにする」）

### 3. GitHub に公開鍵を登録する

公開鍵の中身を表示します。

```bash
cat ~/.ssh/id_ed25519.pub
```

`ssh-ed25519 AAAAC3Nza…（長い文字）… main-pc` のような1行が出ます。これを全部コピーします（ターミナルでは Ctrl + Shift + C）。

1. GitHub の右上の自分のアイコン → **Settings** → 左の **SSH and GPG keys** を開く
2. **New SSH key** を押す
3. **Title** に、どの機械の鍵かを書く（例: `main-pc`）。**Key type** は **Authentication Key** のまま
4. **Key** に、コピーした1行を貼り付ける
5. **Add SSH key** を押す（パスワードや2段階認証を聞かれたら答える）

> **`.pub` が付いていないほう（秘密鍵）を貼らないでください。** 秘密鍵は `-----BEGIN OPENSSH PRIVATE KEY-----` で始まります。
> もし貼ってしまったら、GitHub からその鍵を消し、2. からやり直して新しい鍵を作ります。

#### gh でまとめて登録する

gh を使うなら、ログインのときに SSH を選ぶと、鍵の登録（鍵がなければ作成も）までまとめてできます。

```bash
gh auth login
```

| 聞かれること | 選ぶもの |
| --- | --- |
| どこの GitHub か | **GitHub.com** |
| git の操作に使う方法（protocol） | **SSH** |
| 公開鍵を上げるか（鍵がなければ、作るか） | `~/.ssh/id_ed25519.pub` を選ぶ（作るときは、パスフレーズと Title を聞かれる） |
| ログインの方法 | **Login with a web browser** → 出てきた8文字のコードを、開いたブラウザに入れる |

- `gh auth status` で、ログインできているかと、使う方法（`Git operations protocol: ssh`）が出ます
- すでに HTTPS でログインしていて、SSH に変えたいときは `gh config set git_protocol ssh` を打ちます。このあと gh で作る・クローンするリポジトリが、SSH の URL になります

### 4. つながるか確かめる

```bash
ssh -T git@github.com
```

初めてのときは、次のように聞かれます。

```text
The authenticity of host 'github.com (…)' can't be established.
ED25519 key fingerprint is SHA256:+DiY3wvvV6TuJJhbpZisF/zLDA0zPMSvHdkr4UvCOqU.
Are you sure you want to continue connecting (yes/no/[fingerprint])?
```

`SHA256:` のあとが GitHub の [SSH key fingerprints](https://docs.github.com/ja/authentication/keeping-your-account-and-data-secure/githubs-ssh-key-fingerprints) のページに載っているものと同じなら、`yes` と打ちます。
相手が本物の GitHub かを確かめるためのもので、聞かれるのは最初の1回だけです（`~/.ssh/known_hosts` に覚えます）。パスフレーズを聞かれたら、2. で決めたものを打ちます。

```text
Hi ユーザー名! You've successfully authenticated, but GitHub does not provide shell access.
```

と出れば成功です。後ろの「shell access は使えない」は、GitHub にログインしてコマンドを打つことはできない、という意味で、git は使えます。
`Permission denied (publickey).` と出たら、下の「よくあるエラー」を見ます。

### 5. パスフレーズを毎回聞かれないようにする

Ubuntu のデスクトップでは、鍵を覚えておく係（ssh-agent）が動いています。毎回パスフレーズを聞かれるときは、`~/.ssh/config` に次の2行を書きます（`nano ~/.ssh/config`）。

```text
Host *
    AddKeysToAgent yes
```

最初の1回だけパスフレーズを打てば、ログアウトするまでは聞かれなくなります。`ssh-add -l` で、覚えている鍵が出ます。

### HTTPS で使っていたリポジトリを SSH に切り替える

`git clone https://…` でクローンしたリポジトリや、VS Code の Publish to GitHub で置いたリポジトリは、HTTPS の URL になっています。SSH に変えるときは、次のようにします。

```bash
cd ~/apps/collar
git remote -v
git remote set-url origin git@github.com:ユーザー名/collar.git
git remote -v
```

`git remote -v` で、`origin` の URL が `git@github.com:…` に変わったことを確かめます。

## 新しくリポジトリを作る

流れは「手元でリポジトリにして、最初のコミットをする → GitHub に置き場を作って、送る」です。置き場の作り方は3つあり、どれでも同じものができます。

| 方法 | すること | 向いているとき |
| --- | --- | --- |
| VS Code の **Publish to GitHub** | ボタンを押す（3章の「GitHub に置く」） | VS Code で作ったプロジェクトを、そのまま置く |
| **gh repo create** | コマンド1行 | ターミナルで作業しているとき |
| **GitHub の画面で作ってつなぐ** | ブラウザで作り、`git remote add` でつなぐ | gh を入れていない PC。git だけでできる |

VS Code の拡張機能「Raspberry Pi Pico」で作ったプロジェクトは、まだ git のリポジトリになっていません（`.gitignore` だけはできています）。

### 1. 手元でリポジトリにする

```bash
cd ~/apps/collar
git init
```

`Initialized empty Git repository in /home/ユーザー名/apps/collar/.git/` と出ます。

`.gitignore` がなければ作ります（`nano .gitignore`）。C++ のプロジェクトなら、次のようにします。

```text
# ビルドしてできたもの
build/
# パスワードなど（下の「上げてはいけないもの」）
secrets.h
# PC の Python（14章）で使うもの
__pycache__/
.venv/
```

### 2. 最初のコミットをする

```bash
git add .
git status
git commit -m "最初のバージョン"
```

`git status` で、`Changes to be committed:` の一覧を見ます。`build/` や、パスワードの入ったファイルがないことを確かめてから、コミットします。

### 3. GitHub に置く

次の A か B の、どちらかでします（VS Code の Publish to GitHub を押してもかまいません）。

#### A. gh で作る

```bash
gh repo create collar --private --source=. --push
```

GitHub に `collar` という非公開のリポジトリを作り、`origin` として登録し、最初のコミットまで送ります。

#### B. GitHub の画面で作ってつなぐ

1. GitHub の右上の **＋** → **New repository** を押す
2. **Repository name** に `collar` と書き、**Private** を選ぶ
3. README・.gitignore・license は**付けない**（空のリポジトリにする。手元のものと食い違わないように）
4. **Create repository** を押す
5. 出てきた画面で **SSH** を選び、`git@github.com:ユーザー名/collar.git` をコピーする

```bash
git remote add origin git@github.com:ユーザー名/collar.git
git push -u origin main
```

- `git remote add origin URL` で、GitHub のリポジトリを `origin` という名前で登録します
- `-u` は「この先は、`git push` と `git pull` だけで、origin の main とやり取りする」と覚えさせます。最初の1回だけ付けます

### 4. 置けたか確かめる

ブラウザで `https://github.com/ユーザー名/collar` を開き、ファイルが並んでいれば完了です（`gh repo view --web` でも開けます）。
README.md を置いておくと、このページの下に表示されます。何のプログラムか・どのボードか・ビルドのしかたを書いておくと、あとで自分が助かります。

### GitHub にあるリポジトリから始める（クローン）

別の PC で続きを開発するときや、ほかの人のリポジトリを使うときです。

```bash
cd ~/apps
git clone git@github.com:ユーザー名/collar.git
cd collar
code .
```

- `gh repo clone collar` でも同じです（自分のリポジトリなら、ユーザー名を省けます）
- 公開されているリポジトリ（pico-examples など）は、ログインしなくても HTTPS の URL でクローンできます（付録A の SDK のダウンロード）
- フォルダの名前は、リポジトリの名前（`collar`）になります

## ふだんの記録

作業を始めるときと、終わったときに、次の順に打ちます。

```bash
git pull
git status
git diff
git add .
git commit -m "I2C の読み取りを足した"
git push
```

| コマンド | すること |
| --- | --- |
| `git pull` | GitHub の新しい分を取り込む。別の PC でも作業しているなら、始める前に必ず |
| `git status` | 変えたファイルと、ステージに入れたファイルの一覧。**迷ったら、まずこれ** |
| `git diff` | ステージに入れていない変更を、行ごとに見る（`-` が消した行、`+` が足した行） |
| `git diff --staged` | ステージに入れた変更を見る（コミットする前の最後の確認） |
| `git add ファイル名` | そのファイルだけをステージに入れる |
| `git add .` | 変えたファイルを全部、ステージに入れる |
| `git commit -m "説明"` | 記録する |
| `git push` | GitHub に送る |
| `git log --oneline` | コミットの一覧（新しいものが上） |
| `git log -p ファイル名` | そのファイルの、変更の歴史 |
| `git show コミットの番号` | そのコミットで、何を変えたか |

`git status` は、次のように出ます。

```text
On branch main
Your branch is up to date with 'origin/main'.

Changes to be committed:
        modified:   collar.cpp

Changes not staged for commit:
        modified:   CMakeLists.txt

Untracked files:
        mpu6050.h
```

| 見出し | 意味 |
| --- | --- |
| `Changes to be committed` | ステージに入っている。次のコミットに入る |
| `Changes not staged for commit` | 変えたが、まだステージに入れていない |
| `Untracked files` | git がまだ知らない、新しいファイル。`git add` するまで記録されない |
| `Your branch is ahead of 'origin/main' by 2 commits` | まだ GitHub に送っていないコミットが2つある。`git push` する |

- `git log` や `git diff` の表示が長いと、`:` が出て止まります。矢印キーで動かし、`q` で終わります
- **コミットの番号**は、`3d3b5db` のような英数字です。`git log --oneline` の左の列に出ます。コマンドでは、最初の7文字ほどを書けば通じます
- 1つのコミットには、1つのこと（「I2C の読み取りを足した」「LED のピンを変えた」）を入れます。あとで探すときや、戻すときに楽です

### 上げてはいけないもの

| もの | どうするか |
| --- | --- |
| WiFi のパスワード・サーバーのパスワード・API キー | 別のファイルに分けて、`.gitignore` に入れる（下） |
| ビルドしてできたもの（`build/`、`.uf2`） | `.gitignore` に入れる。ソースからいつでも作り直せる |
| 大きなデータ（何十 MB もの CSV、動画） | `.gitignore` に入れる。GitHub は 100MB を超えるファイルを受け付けない |

Pico W で WiFi を使うときは、パスワードを `secrets.h` に書いて `.gitignore` に入れ、中身を空にした見本（`secrets.example.h`）だけを上げます。

```cpp
// secrets.h（git に上げない。secrets.example.h をコピーして作る）
#pragma once
#define WIFI_SSID     "my-wifi"
#define WIFI_PASSWORD "ここにパスワード"
```

- **一度プッシュしたものは、あとで消しても歴史に残ります。** パスワードを上げてしまったら、パスワードのほうを変えます
- すでに記録してしまったファイルを、記録から外すには `git rm --cached secrets.h`（PC のファイルは消えない）→ `.gitignore` に書く → コミット、とします。フォルダなら `git rm -r --cached build` です

## 前の状態に戻す

| やりたいこと | コマンド | 注意 |
| --- | --- | --- |
| コミットしていない変更を捨てる | `git restore ファイル名` | 捨てた変更は戻せない |
| ステージから出す（変更は残す） | `git restore --staged ファイル名` | |
| 直前のコミットの説明を直す | `git commit --amend -m "新しい説明"` | **プッシュする前だけ** |
| 直前のコミットに、入れ忘れたファイルを足す | `git add ファイル名` → `git commit --amend --no-edit` | **プッシュする前だけ** |
| プッシュしたコミットを取り消す | `git revert コミットの番号` → `git push` | 「取り消す」コミットが新しくできる。歴史は消えない |
| 前のコミットのファイルを1つ取り出す | `git restore --source コミットの番号 ファイル名` | 今のファイルが置き換わる（コミットすれば記録に残る） |
| 前のコミットの状態を、見るだけ | `git switch --detach コミットの番号` → 戻るときは `git switch main` | 見ている間に変えたものは、main に戻るときに捨てる |
| 作業中の変更を、一時的によける | `git stash` → あとで `git stash pop` | pull やブランチの切り替えができないとき |
| 出荷したバージョンを作り直す | `git switch --detach v1.0.0` → ビルド → `git switch main` | 17章のタグ |

> 調べると出てくる `git reset --hard` や `git push --force` は、**記録を消すコマンドです。** 意味がわかるまでは使いません。
> 困ったときは、まず `git status` を打ち、何が起きているかを確かめます。

## ブランチで試す

動いている main を壊さずに、大きな変更（省電力の工夫を入れる、センサーを替える、など）を試したいときは、ブランチを分けます。
1人で開発していて、小さな変更をこまめにコミットするだけなら、main だけでもかまいません。

```bash
git switch -c try-sleep
git add .
git commit -m "スリープを試す"
git push -u origin try-sleep
```

`try-sleep` という枝を作って移り、そこでコミットします。main はそのまま残っています。

うまくいったら、main に取り込みます。

```bash
git switch main
git merge try-sleep
git push
git branch -d try-sleep
git push origin --delete try-sleep
```

やめるときは、main に戻って枝を消します（`-D` は取り込んでいない枝も消す）。

```bash
git switch main
git branch -D try-sleep
```

| コマンド | 意味 |
| --- | --- |
| `git branch` | ブランチの一覧。`*` が付いているのが、今いるブランチ |
| `git switch -c 名前` | 新しいブランチを作って、そこに移る |
| `git switch 名前` | そのブランチに移る。作業フォルダのファイルが、そのブランチの状態に変わる |
| `git merge 名前` | 今いるブランチに、そのブランチの変更を取り込む |
| `git branch -d 名前` | 取り込み済みのブランチを消す |

- VS Code では、左下に今のブランチの名前が出ています。押すと、切り替えと作成ができます
- ブランチを移る前に、変更をコミットするか、`git stash` でよけておきます
- GitHub では、ブランチから **Pull Request** を作り、変更を見比べてから main に取り込むこともできます（何人かで開発するとき）

### 両方で変えていたとき（コンフリクト）

2台の PC で同じファイルの同じ所を変えてから `git pull` や `git merge` をすると、どちらを残すか git が決められず、次のように出ます。

```text
CONFLICT (content): Merge conflict in collar.cpp
Automatic merge failed; fix conflicts and then commit the result.
```

ファイルの中に、両方の内容が印付きで入っています。

```text
<<<<<<< HEAD
const int SAMPLE_HZ = 50;
=======
const int SAMPLE_HZ = 100;
>>>>>>> 9f8e7d6
```

`<<<<<<<` から `=======` までが手元、`=======` から `>>>>>>>` までが取り込もうとした側です。

1. VS Code でファイルを開くと、印の上に **Accept Current Change**（手元を残す）・**Accept Incoming Change**（取り込む側を残す）・**Accept Both Changes**（両方）が出る。押すか、手で書き直して、印の3行を消す
2. ビルドして、動くか確かめる
3. `git add collar.cpp` → `git commit` → `git push`

- `git commit` で nano が開いたら、説明はそのままで、Ctrl + O → Enter（保存）→ Ctrl + X（閉じる）
- やめて、取り込む前に戻すときは `git merge --abort`
- 違う所を変えていただけなら、git が自動でまとめます（そのときも、まとめた記録の説明を書くために nano が開くので、同じように保存して閉じます）
- 防ぐには、作業を始める前に `git pull`、終わったら `git push` をくせにします

## 別の機械からクローンできるようにする

ラズパイ・Jetson・別の PC で、GitHub の**非公開**のリポジトリを取ってくるには、その機械も GitHub に「自分である」ことを示す必要があります。使い方に合わせて選びます。

| 方法 | できること | 向いているとき |
| --- | --- | --- |
| **その機械で鍵を作って、アカウントに登録** | 自分の全部のリポジトリを、クローン・プッシュできる | 別の PC で開発する |
| **デプロイキー**（そのリポジトリだけに登録） | 1つのリポジトリだけ。ふつうは読むだけ | ラズパイ・Jetson で、決まったプログラムを取ってきて動かすだけ |
| **ssh -A で、PC の鍵を貸す** | ssh でログインしている間だけ、PC の鍵を使う | ラズパイで一時的にクローンしたい。機械に鍵を置きたくない |
| **GitHub を通さず、PC から直接** | 同じ LAN の中で、PC のリポジトリをクローンする | GitHub に置きたくない・インターネットがない |

### 別の PC で開発する

その PC で、上の「SSH キーを作って GitHub に登録する」の 1.〜4. をします。`-C` と Title には、その PC がわかる名前（例: `laptop`）を付けます。
そのあと、「GitHub にあるリポジトリから始める（クローン）」のとおりにクローンします。2台目の PC でも、「最初に1回だけする設定」の名前とメールアドレスを忘れずにします。

### ラズパイ・Jetson に読むだけの鍵を置く（デプロイキー）

ラズパイや Jetson では、コードを取ってきて動かすだけで、そこから GitHub に送ることはふつうありません。
そのときは、そのリポジトリだけに使える、読むだけの鍵（デプロイキー）にします。鍵を盗まれても、ほかのリポジトリや書き込みには使われません。

まず、ラズパイにログインして、鍵を作ります。

```bash
ssh pi@raspberrypi.local
ssh-keygen -t ed25519 -C "raspi-collar" -f ~/.ssh/collar_deploy -N ""
cat ~/.ssh/collar_deploy.pub
```

- `-f` は鍵のファイルの名前です。リポジトリごとに鍵を分けるので、決まった名前（`id_ed25519`）ではなく、わかる名前にします
- `-N ""` は、パスフレーズを空にします。自動で `git pull` できるようにするためです

出てきた1行を、GitHub に登録します。

1. GitHub で、リポジトリ（`collar`）のページの **Settings** → 左の **Deploy keys** を開く
2. **Add deploy key** を押す
3. **Title** に `raspi`、**Key** に1行を貼り付ける
4. **Allow write access は ☐ のまま**（読むだけ）にして、**Add key** を押す

次に、ラズパイの `~/.ssh/config` に、この鍵を使う「あだ名」を書きます（`nano ~/.ssh/config`）。

```text
Host github-collar
    HostName github.com
    User git
    IdentityFile ~/.ssh/collar_deploy
    IdentitiesOnly yes
```

あだ名を使って確かめて、クローンします。

```bash
ssh -T git@github-collar
git clone git@github-collar:ユーザー名/collar.git ~/collar
```

`ssh -T` で `Hi ユーザー名/collar! You've successfully authenticated…` と出れば、つながっています（デプロイキーでは、リポジトリの名前が出ます）。
新しいコードを取ってくるときは、`cd ~/collar` で移って `git pull` です。

- `github-collar` は「github.com に、`collar_deploy` の鍵でつなぐ」という意味のあだ名です。`git@github.com:` の代わりに `git@github-collar:` と書きます
- 1つのデプロイキーは、1つのリポジトリにしか登録できません。2つ目のリポジトリには、別の鍵（例: `logger_deploy`）と別のあだ名（例: `github-logger`）を作ります
- 鍵をもう使わないときは、GitHub の Deploy keys から消します

### ssh -A で PC の鍵を貸す

PC からラズパイに ssh でログインするときに `-A` を付けると、ログインしている間だけ、PC の鍵で GitHub につながります。秘密鍵は、ラズパイにはコピーされません。

```bash
ssh -A pi@raspberrypi.local
ssh -T git@github.com
git clone git@github.com:ユーザー名/collar.git
```

- 1行目は PC で、2行目からはラズパイの中で打ちます
- PC の鍵が ssh-agent に入っている必要があります（PC で `ssh-add -l` を打つと、鍵が出る）
- 自分だけが管理している機械で使います。ほかの人も管理者になれる機械では、その人に鍵を使われるおそれがあるので使いません

### GitHub を通さずに、PC から直接クローンする

同じ LAN の中なら、GitHub に置かなくても、PC のリポジトリを ssh で直接クローンできます。PC を、ssh でログインできる機械にします。

1. PC に、ssh のサーバーを入れる（入れると、自動で動き始める）

```bash
sudo apt install openssh-server
hostname
```

`hostname` で出た名前に `.local` を付けたもの（例: `main-pc.local`）で、同じ LAN のほかの機械からつながります。つながらないときは、`hostname -I` で出た IP アドレス（例: `192.168.1.20`）を使います。

2. ラズパイなど、クローンしたい機械で鍵を作り、PC に登録する

```bash
ssh-keygen -t ed25519 -C "raspi"
ssh-copy-id ユーザー名@main-pc.local
ssh ユーザー名@main-pc.local
```

`ssh-copy-id` で、PC のログインのパスワードを1回だけ聞かれます。公開鍵が、PC の `~/.ssh/authorized_keys` に足されます。
3行目でパスワードなしにログインできれば成功です。`exit` で戻ります。

3. クローンする

```bash
git clone ユーザー名@main-pc.local:apps/collar
```

`:` のあとは、PC のホームフォルダからの場所です。取ってきたあとは、`git pull` で PC の新しいコミットを取り込めます。

#### ラズパイからも送りたいとき

PC の作業フォルダ（`~/apps/collar`）には、ほかの機械から直接プッシュできません（`refusing to update checked out branch` と出ます）。両方から送りたいときは、PC に「置き場だけのリポジトリ」（bare リポジトリ）を作り、GitHub の代わりにします。

```bash
git clone --bare ~/apps/collar ~/git/collar.git
cd ~/apps/collar
git remote add lan ~/git/collar.git
```

- PC では `git push lan main` で置き場に送り、`git pull lan main` で取り込みます
- ほかの機械では `git clone ユーザー名@main-pc.local:git/collar.git` でクローンし、ふつうに `git push`・`git pull` します
- `--bare` は、作業フォルダのない、記録だけのリポジトリです（GitHub の中にあるのと同じ形）

> この方法は、PC の電源が入っていて、同じ LAN にいるときだけ使えます。ふだんは GitHub を使うほうが簡単です。
> PC に ssh でログインできるようになるので、PC のパスワードは推測されにくいものにします。使わなくなったら `sudo apt remove openssh-server` で止めます。

## よくあるエラー

| エラー | 意味と対処 |
| --- | --- |
| `Permission denied (publickey).` | GitHub（や PC）が鍵を受け付けない。① `ls ~/.ssh` で鍵があるか ② GitHub の SSH keys に、その機械の `.pub` の中身が登録されているか ③ `ssh-add -l` で鍵が入っているか、を確かめる。`ssh -vT git@github.com` で、どの鍵を試したかが出る |
| `Host key verification failed.` | 相手（github.com や PC）を確かめられなかった。初めてのときに `yes` と打たなかったなど。`ssh -T git@github.com` を打って、`yes` と答え直す |
| `WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!` | 前につないだときと、相手の鍵が変わった。ラズパイの OS を入れ直したときに出る。自分で入れ直したとわかっているなら `ssh-keygen -R raspberrypi.local` で古い記録を消す。心当たりがなければ、つながない |
| `ssh: connect to host … port 22: Connection refused` | 相手で ssh のサーバーが動いていない。PC なら `sudo apt install openssh-server` |
| `remote: Support for password authentication was removed` | HTTPS の URL で、GitHub のパスワードを打った。`gh auth login` でログインするか、SSH の URL に変える（`git remote set-url`） |
| `ERROR: Repository not found.` | URL のつづりがちがうか、その鍵（アカウント）では見られないリポジトリ。デプロイキーなら、あだ名とリポジトリの組み合わせを確かめる |
| `fatal: not a git repository` | git のリポジトリではないフォルダにいる。`cd ~/apps/collar` のように移る |
| `Author identity unknown` | 名前とメールアドレスが登録されていない。「最初に1回だけする設定」をする |
| `error: src refspec main does not match any` | まだ1回もコミットしていない。または、ブランチの名前が `master` になっている（`git branch` で確かめ、`git branch -m master main` で変える） |
| `! [rejected] main -> main (fetch first)` | GitHub に、手元にないコミットがある（別の PC でプッシュした）。`git pull` してから `git push` |
| `fatal: Need to specify how to reconcile divergent branches.` | 両方で変えていて、まとめ方が決まっていない。`git config --global pull.rebase false` を打って、もう一度 `git pull` |
| `CONFLICT (content): Merge conflict in …` | 同じ所を両方で変えていた。上の「両方で変えていたとき」 |
| `fatal: refusing to merge unrelated histories` | README などを付けて GitHub で作ったリポジトリに、手元のものをつなごうとした。`git pull origin main --allow-unrelated-histories` でまとめてから `git push` |
| `fatal: remote origin already exists.` | origin がもう登録されている。`git remote set-url origin URL` で URL を変える |
| `error: Your local changes to the following files would be overwritten` | コミットしていない変更があって、pull やブランチの切り替えができない。コミットするか、`git stash` でよける |
| `refusing to update checked out branch` | PC の作業フォルダに、直接プッシュした。上の「ラズパイからも送りたいとき」の bare リポジトリを使う |
| `this exceeds GitHub's file size limit of 100.00 MB` | 大きすぎるファイルをコミットした。直前のコミットなら `git rm --cached ファイル名` → `.gitignore` に書く → `git commit --amend --no-edit` → `git push` |
| 画面の下に `:` や `(END)` が出て止まった | `git log`・`git diff` の表示の途中。`q` で終わる |
| 見慣れない画面（エディタ）が開いた | コミットやマージの説明を書く画面。nano なら Ctrl + O → Enter → Ctrl + X。vim なら `:wq` と打って Enter |

## コマンドの一覧

| やること | コマンド |
| --- | --- |
| 名前とメールアドレスを登録する（最初だけ） | `git config --global user.name "名前"`、`git config --global user.email "アドレス"` |
| SSH キーを作る（機械ごとに最初だけ） | `ssh-keygen -t ed25519 -C "機械の名前"` |
| 公開鍵を表示する | `cat ~/.ssh/id_ed25519.pub` |
| GitHub につながるか確かめる | `ssh -T git@github.com` |
| gh でログインする | `gh auth login` |
| 今のフォルダをリポジトリにする | `git init` |
| GitHub に作って送る | `gh repo create 名前 --private --source=. --push` |
| GitHub の置き場とつなぐ | `git remote add origin git@github.com:ユーザー名/名前.git` → `git push -u origin main` |
| つないでいる先を見る・変える | `git remote -v`、`git remote set-url origin URL` |
| クローンする | `git clone git@github.com:ユーザー名/名前.git` |
| 状態を見る | `git status` |
| 変更を見る | `git diff`、`git diff --staged` |
| 記録する | `git add .` → `git commit -m "説明"` |
| 送る・取り込む | `git push`、`git pull` |
| 歴史を見る | `git log --oneline`、`git show コミットの番号` |
| 変更を捨てる | `git restore ファイル名` |
| 取り消すコミットを作る | `git revert コミットの番号` |
| 一時的によける・戻す | `git stash`、`git stash pop` |
| ブランチを作る・移る・取り込む | `git switch -c 名前`、`git switch 名前`、`git merge 名前` |
| 印を付ける（17章） | `git tag v1.0.0` → `git push --tags` |

## まとめ

- git は PC の中で記録をとるソフト、GitHub はその置き場。`add` → `commit` → `push` で送り、別の機械では `clone` → `pull` で取ってくる
- 最初に、名前・メールアドレス・`main` を設定する
- SSH キーは機械ごとに1組。秘密鍵は渡さず、公開鍵（`.pub`）を GitHub に登録する。`ssh -T git@github.com` で確かめる
- 新しいリポジトリは、`git init` → 最初のコミット → `gh repo create`（または GitHub の画面で作って `git remote add`）→ `git push -u origin main`
- ラズパイ・Jetson で取ってくるだけなら、読むだけのデプロイキー。GitHub を通さないなら、PC に ssh でつないでクローンする
- パスワードと `build/` は上げない。迷ったら `git status`
