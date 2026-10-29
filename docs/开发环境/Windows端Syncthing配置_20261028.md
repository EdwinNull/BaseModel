# Windows 端 Syncthing 配置与双机使用守则（2026-10-28）

目的：BaseModel 和 CRF 两个文件夹在家里的 Windows 和随身的 Mac 之间实时同步，改了一边，另一边几秒内跟着变，不再靠 git + U 盘搬文件。

同步方式是 Syncthing 点对点：只在这两台机器之间加密传输，不经过任何网盘或第三方存储。`.git` 一起同步，所以提交、分支两边也一致。

## Mac 端已完成（10-28）

| 项 | 状态 |
|---|---|
| Syncthing | 已安装（Homebrew `syncthing-app`，v2.1.6），设备名 `Mac` |
| Mac 设备 ID | `SW3S4TV-WIC5GI7-OVWWGXW-JUZ427Q-C77RAZ3-K74FUBU-JO7SM5H-YBEASQ2` |
| 文件夹 | `basemodel`（BaseModel，约 550 MB、3,000 多个文件）、`crf`（CRF，约 9 MB）；双向收发，开了 30 天的分级版本控制 |
| 忽略规则 | 写在各仓库根目录的 `.stglobalignore`（入库，两边共用）；每台机器的 `.stignore` 只有一行 `#include .stglobalignore` |
| 不同步的内容 | 只排除会弄坏另一台机器环境的东西：`.venv`、`node_modules`、`__pycache__`、`.DS_Store` 等平台相关文件和系统临时文件，git 锁文件，Claude Code 的 `.claude/worktrees`，CRF `.deploy` 下的日志和 pid。10-29 起，`data/`、`flucase/var/`、`models/` 和 CRF 的数据库备份（`*.sql`、`*.db`、`*.dump`）**也同步**（研究者定：两台都是本人设备） |
| 换行符 | 两个仓库加了 `.gitattributes`（文本一律 LF）；BaseModel、`BaseModel/flucase`、CRF 三个仓库的本地配置都设了 `core.autocrlf=false`、`core.filemode=false`。`.git/config` 会同步过来，Windows 用的也是这套设置 |

> Mac 上的 CRF 有一批还没提交的修改（`crf-backend/`、`crf-system/` 下几十个文件）。这批修改会原样同步到 Windows。

## 第 0 步：在旧文件夹里收尾

下面的命令都在 PowerShell 里执行。先把 CRF 在 Windows 上的路径填进 `$crf`：

```powershell
$base = 'G:\BaseModel'
$crf  = 'C:\crf'          # 改成 Windows 上 CRF 仓库的实际路径
git -C $base status --short
git -C $base\flucase status --short
git -C $crf status --short
```

1. 三个仓库里只要有没提交的修改，先提交并推送。CRF 要特别注意：Mac 上已经有一批未提交的修改，Windows 上的修改不要直接提交到 `main`，先放到一个分支上：
   ```powershell
   git -C $crf switch -c windows-wip
   git -C $crf add -A
   git -C $crf commit -m "Windows 上未提交的修改（同步前暂存）"
   git -C $crf push -u origin windows-wip
   ```
   之后在 Mac 上再和那批修改合并。
2. 三个仓库都拉到最新：
   ```powershell
   git -C $base pull
   git -C $base\flucase pull
   git -C $crf pull
   ```
   拉完以后，旧文件夹里会有 `.stglobalignore` 和本文档。如果 `git status` 里冒出一大批只是换行符变化的"已修改"，不用管，这个文件夹马上就要改名作备份。
3. **CRF 如果同时是 Windows 上正在运行的部署**（按 `.deploy/README-windows.md` 装过、用 `crf-service.ps1` 注册了开机自启），先在 `.deploy` 目录查一下状态：
   ```powershell
   .\crf-service.ps1 status
   ```
   如果它还在运行，**不要**让 Syncthing 直接改这个目录：要么先 `.\crf-service.ps1 uninstall` 停掉，要么开发用的 CRF 另建一个文件夹（例如 `C:\dev\CRF`），部署目录保持原样。
4. 关掉 VS Code、Cursor，以及所有停在这几个目录里的终端和程序（比如 flucase 后端）。否则下一步改名会失败。

## 第 1 步：安装 Syncthing

1. 打开 <https://syncthing.net/downloads/>，在 Windows 一栏下载 **Syncthing Windows Setup**（社区维护的安装器），安装时选登录后自动启动。
2. 第一次运行时如果 Windows 防火墙弹窗，勾选"专用网络"并允许。
3. 浏览器打开 <http://127.0.0.1:8384>：
   - 弹出"是否允许匿名使用报告"，选**否**；
   - 操作 → 设置 → 常规：设备名改成 `Windows`；
   - 页面提示"没有设置图形界面密码"时，可以在 设置 → 图形界面 里设一个。界面只监听本机 127.0.0.1，不设也可以。
4. 打开 Windows 设置 → 系统 → 电源，把"接通电源时进入睡眠"改成**从不**。Mac 在外面的时候，Windows 必须开着才能同步。

## 第 2 步：准备新文件夹

旧文件夹改名留作备份，再建同名的空文件夹，并先放好两个忽略文件。必须在共享之前放好：Syncthing 找不到 `#include` 引用的文件会报错，然后整个文件夹停住不动。

```powershell
$crfOld = "$crf" + '_old'
Rename-Item $base 'BaseModel_old'
Rename-Item $crf (Split-Path $crfOld -Leaf)

foreach ($pair in @(@('G:\BaseModel_old', $base), @($crfOld, $crf))) {
    $old, $new = $pair
    New-Item -ItemType Directory $new | Out-Null
    Copy-Item "$old\.stglobalignore" $new
    Set-Content -Path "$new\.stignore" -Value '#include .stglobalignore' -Encoding ascii
}
Get-ChildItem -Force $base, $crf      # 每个新文件夹里应该只有 .stglobalignore 和 .stignore
```

如果第 0 步第 3 条决定把开发用的 CRF 放到新位置，把 `$crf` 改成新位置，`$crfOld` 改成原来的部署目录，并跳过对它的 `Rename-Item`。

## 第 3 步：和 Mac 配对，接收两个文件夹

1. **Windows**：操作 → 显示 ID，复制 Windows 的设备 ID。
2. **Windows**：右下角"添加远程设备"，设备 ID 填上面表里 Mac 的 ID，名称填 `Mac`，保存。
3. **Mac**：打开 <http://127.0.0.1:8384>（或菜单栏 Syncthing 图标 → Open），会出现"设备 Windows 想要连接"，点添加。然后分别编辑 BaseModel、CRF 两个文件夹 → 共享 → 勾选 `Windows` → 保存。
   也可以把 Windows 的设备 ID 发给 Claude，让它在 Mac 上代办这一步。
4. **Windows**：会出现"Mac 想要共享文件夹 BaseModel / CRF"，分别点添加：
   - 文件夹路径：BaseModel 填 `G:\BaseModel`，CRF 填 `$crf` 对应的路径；
   - 文件夹 ID 会自动填成 `basemodel` / `crf`，**不要改**；
   - 文件版本控制：选 **Staggered**（分级版本），最长保留天数填 30；
   - "忽略模式"一栏会显示 `#include .stglobalignore`，保持不变；
   - 保存。
5. 等两个文件夹都变成**最新**（Up to Date）。BaseModel 约 550 MB，在家里局域网里几分钟就好。
6. 在 Windows 的"远程设备 → Mac"里看"连接类型"：显示 TCP 或 QUIC 是直连，显示 Relay 是走公共中继（加密但慢）。

## 第 4 步：把 Windows 独有的东西补回来

两个文件夹都显示"最新"以后再执行。下面的命令只复制新文件夹里**还没有**的文件，已有的一律不覆盖：

```powershell
robocopy G:\BaseModel_old $base /E /XC /XN /XO /XD .git
robocopy $crfOld $crf /E /XC /XN /XO /XD .git
```

- 会补回来的有：`data\`、`models\`、`flucase\var\`、`.venv`、`node_modules`、CRF 的 `.deploy\crf-data-backup.sql`，以及其他只在 Windows 上有的文件。
- robocopy 的退出码 0–7 都算成功，8 及以上才是出错。
- 补回来的文件中，`.venv`、`node_modules` 只留在 Windows，其余的会再同步到 Mac（10-29 起也包括数据和 `models`）。
- 新文件夹的路径和原来一样，所以补回来的 `.venv` 可以直接用。

## 第 5 步：核对

```powershell
git -C $base status --short            # 应为空
git -C $base\flucase status --short    # 应为空
git -C $crf status --short             # 只有 Mac 上那批未提交的修改
git -C $base config core.autocrlf      # 应为 false
G:\BaseModel\flucase\backend\.venv\Scripts\python --version
```

再试一次实时同步：

```powershell
Set-Content "$base\tmp\sync_test.txt" "from Windows $(Get-Date)"
```

几秒后 Mac 上的 `Basemodel/tmp/sync_test.txt` 应该就出现了。在 Mac 上删掉它，Windows 上也会跟着消失。

正常用一周、确认没少东西后，再删掉 `G:\BaseModel_old` 和 CRF 的旧文件夹。

## 日常使用守则

1. **同一时间只在一台机器上干活。** 换机器前，看托盘或菜单栏的 Syncthing 图标（或 8384 网页），两边都是"最新"再开始。
2. **不用的那台关掉编辑器的自动 fetch**（VS Code / Cursor 设置里搜 `git.autofetch`，关掉），或者干脆关掉编辑器。两边同时写 `.git` 会产生冲突文件。换机器后第一次 `git status` 会慢一点，是在重建索引，属于正常。
3. **出现 `*.sync-conflict-*` 文件**，说明两边改了同一个文件。工作区里的：对比两个版本，留下对的，删掉冲突文件。`.git` 里的：先 `git status`、`git log` 看仓库是否正常，拿不准就交给 Claude 处理，不要随手删。
4. **照常提交并推送到 GitHub。** Syncthing 不是备份：误删、改坏也会同步到另一边。误删的文件可以在文件夹的 `.stversions` 里找回（30 天内）。
5. **要改同步范围，只改 `.stglobalignore`**（它会同步到两边，也入库）。`.stignore` 不要动。
6. **真实数据也同步（10-29 起）**：`data/`、`flucase/var/`、`models/`、CRF 的 `.sql/.db` 备份两边保持一致。数据只在这两台机器之间加密传输，不经第三方存储；不要放进任何网盘。
   flucase 正式部署在阿里云 ECS 上，那里的病例库不在这两台机器上，不受同步影响。只有在本机启动 flucase 后端时才需要注意。本机的病例库是 SQLite，开了 WAL，`app.db` 旁边还有 `-wal`、`-shm` 两个文件；开发模式默认放在 `flucase/var/`，第一轮测试时用 `FLUCASE_DATA_DIR` 指到 `data/` 下。所以本机的 flucase **同一时间只在一台机器上运行**：换机器前先停掉后端，等 Syncthing 显示"最新"，再在另一台上启动。只读 Excel 的脚本（`scripts/crf_wide`、`scripts/flucase_raw_scan` 等）不碰病例库，两边都可以随时跑。
7. **Mac 在外面时 Windows 要开着。** Windows 关机或睡眠期间不会同步；两台再次都在线时，会自动补齐。

## 出了问题

| 现象 | 处理 |
|---|---|
| 文件夹报错，提示找不到 `.stglobalignore` | 第 2 步的两个文件没放进去或放错了位置，补上后在网页上点"重新扫描" |
| Mac 在外面时连不上，或一直显示 Relay、速度很慢 | 两台都装 Tailscale（组一个虚拟局域网），然后在 Syncthing 里编辑对方设备 → 高级 → 地址，填 `tcp://<对方的 Tailscale IP>:22000, dynamic` |
| `git status` 出现一大批"已修改"，`git diff` 却只有换行符变化 | 看 `git config core.autocrlf` 是不是 `false`；不是的话执行 `git config core.autocrlf false`，然后交给 Claude 检查 |
| 防火墙拦截、两台在同一个局域网里也连不上 | 在 Windows 防火墙里允许 Syncthing（TCP/UDP 22000、UDP 21027） |
