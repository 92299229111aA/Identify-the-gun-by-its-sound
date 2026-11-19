# 听声辨枪 · Tarkov

匹配排队时玩的小游戏：听一段塔科夫枪声，在四个选项里选出是哪把枪。

## 怎么玩

双击 `game.html`，用 Chrome / Edge 打开即可。不需要联网、不需要装任何东西。

| 操作 | 说明 |
|---|---|
| `空格` | 重放当前题目（答题后为下一题） |
| `1` – `4` | 选择答案 |
| `Enter` | 下一题 |
| 鼠标 | 点圆按钮播放，点选项作答 |

变体用「保底抽签」而不是纯随机：每 10 题固定 5 标准 / 3 消音 / 2 连发，洗牌后依次发，所以不会连续十几题听不到连发。

开始时先选枪族：**全部 57 把** / 步枪 24 / 冲锋枪 11 / 手枪 9 / 霰弹枪 7 / 狙击 6。每道题的变体随机：

- **标准**：室外近距离、未消音单发
- **消音**：带消音器的近距单发
- **连发**：按真实射速拼的点射 + 游戏原版尾音（仅限 31 把能全自动的枪；手枪、栓动、泵动不出连发）

答完展示四个选项的档案：口径、类型、射速，以及从音频算出来的音色特征（偏亮/偏闷、尾音长短、低频厚薄）。正确率和最佳连击存在浏览器本地。

## 命名

每把枪显示两层：**中文社区叫法为主**，官方型号为辅（选项卡片里型号是第二行小字）。

例如 `波波沙 / PPSh-41`、`闪光喷 / KS-23`、`沙鹰 / Desert Eagle`、`维克托 / Vector .45`、`勇士冲锋枪 / PP-19-01`、`短喷 / MTs-255`、`斯捷奇金 / APS`、`雪松 / PP-91 Kedr`。外号与型号相同时（如 `AKS-74U`、`Mk47 Mutant`）只显示一行。

同一把枪的 `nick` 在整个枪池里唯一（构建时会校验），避免四个选项里出现能混淆的简称。表在 `tools/build_game.py` 的 `NICK` / `FULL` 里，改完重新构建即可。

## 界面

参考 [design-systems](https://ruiqichenbiec.github.io/design-systems/) 的两套语言重做：

- **点阵 Lattice**：原生 WebGL2 粒子场（9000 点，无 three.js）。开火时冲击波扩散，答对时粒子聚成枪名。
- **序曲 Overture**：黑底 + 米白、衬线大字、细线框、沉底 HUD、光圈开场。

细节：

- 中文大字用**内嵌的思源宋体子集**（`fonts/subset.woff2`，约 61 KB，只含页面用到的 163 个字符），离线也不会退化成发虚的系统宋体
- 标题 `clamp(40px, 7.6vw, 104px)`；选项沉底四列（≤980 两列、≤640 单列）
- 配色：黑 `#050505` + 米白 `#ece6d8`，对错只用状态色（`#9db183` / `#c25b4e`），不与强调色冲突
- 系统开启「减少动态效果」时自动降级：不做粒子形变、光圈直接显示
- 无 WebGL2 时粒子层静默关闭，其余功能不受影响

## 枪池

57 把，覆盖六个枪族：

| 类别 | 数量 | 例子 |
|---|---|---|
| 步枪 | 24 | AK-74M / AKM / AK-101 / M4A1 / HK 416A5 / SA-58 / SCAR-H / AUG / Mk47 / RPK-16 |
| 冲锋枪 | 11 | MP5 / MP7 / MPX / MP9 / P90 / Vector / PP-19-01 / PP-91 / UMP / PPSh-41 / STM-9 |
| 手枪 | 9 | Glock 18 / M9A3 / M1911A1 / Desert Eagle / Five-seveN / PL-15 / APS / Rhino / RSh-12 |
| 霰弹枪 | 7 | M870 / Mossberg 500 / Benelli M3 / KS-23 / MTs-255 / TOZ-106 / UTS-15 |
| 狙击 | 6 | SVD-S / Mosin / M700 / T-5000M / VPO-215 / VSS |
| 机枪 | 1 | RPK-16（并入步枪族） |

游戏里 80 多把枪，但**只有 57 套独立枪声**：同族武器共用录音（比如 Glock 17 与 18、AK-12 与 AK-15 都没有独立单发采样），所以按「一套声音一把代表枪」收敛到 57。AK-12、PKM、RPD、SR-3M 只有 loop 没有单发，未纳入。

## 成就

15 枚徽章，永久存在 `localStorage`（key `tarkovQuizAchV1`）：

| 类别 | 徽章 |
|---|---|
| 里程碑 | 首次接触（答对 1 题）、新兵（25）、老兵（100） |
| 连击 | 五连（5）、十连（10）、二十连（20） |
| 枪族 | 步兵（步枪 20）、近战（冲锋枪 10）、副武器（手枪 8）、一击必中（霰弹+狙击 10） |
| 变体 | 静默行动（消音答对 10）、全自动（连发答对 10） |
| 彩蛋 | 闪光弹（听出 KS-23）、波波沙（听出 PPSh-41） |
| 收集 | 图鉴（57 把各答对一次） |

顶栏的 `◈ n/15` 是入口，点开是成就面板（未解锁项显示进度、已解锁显示 done）。解锁瞬间右上角弹一条 + 粒子轻微震动，不打断答题。

面板底部「重置进度」会同时清空成就与最佳连击。

## 目录结构

```
game.html               游戏本体（自包含，只引用 sounds/）
audition.html           试听页（57 把，全部变体可听）
sounds/                 音频（OGG，440 条，27 MB）
  manifest.json         枪械元数据与音频索引
  <枪名>/
    standard/           标准单发
    suppressed/         消音单发
    auto/               连发
tools/                  构建与导出脚本
fonts/                  思源宋体源文件与子集（subset.woff2 / subset.b64）
docs/                   预览截图
.venv/                  项目专用 Python 环境（UnityPy / soundfile / ffmpeg）
```

## 音频怎么来的

> 仓库**不包含** `sounds/` 下的音频文件（`.gitignore` 已排除，版权归 Battlestate Games）。克隆后需要本机装有游戏，按「重新构建」里的步骤重新提取；`sounds/manifest.json` 元数据保留在仓库里。

从本机正版《逃离塔科夫》安装目录**只读**提取，不修改游戏文件。两个来源：

- `EscapeFromTarkov_Data\StreamingAssets\Windows\assets\content\audio\banks\<枪名>.bundle` — 每把枪一个音频包
- `EscapeFromTarkov_Data\sharedassets*.assets` — 部分枪声（SVD、SKS、Mosin 等）只在这里

命名在各版本间不统一（`ak74m_outdoor_close_oneshot_01`、`akm_close_indoor_01`、`m4a1_indoor_close_onseshot_01` 这类拼写错误都有），脚本按「枪名前缀 + 下划线」跨包与跨文件匹配，避免 `ak74` 误吸 `ak74m` 的采样。

## 重新构建

```powershell
# 盘点两个来源里的全部枪声前缀
.venv\Scripts\python.exe tools\inventory.py

# 导出全枪池（标准 / 消音 / 连发）+ manifest.json
.venv\Scripts\python.exe tools\export_all.py

# 从音频算音色特征（谱质心 / 尾音 / 低频占比 → 三分位标签）
.venv\Scripts\python.exe tools\hints.py

# 生成试听页
.venv\Scripts\python.exe tools\build_pages.py

# 生成游戏页（两遍：先出页面，再按页面用到的字重做字体子集）
.venv\Scripts\python.exe tools\build_game.py
.venv\Scripts\python.exe tools\make_font.py game.html
.venv\Scripts\python.exe tools\build_game.py
```

字体源文件放在 `fonts/NotoSerifSC-SemiBold.otf`（11 MB，从 Google Fonts 的 noto-cjk 仓库取），构建时会被子集化成 61 KB 的 woff2 内嵌进页面。

`tools/bank_names.py`、`tools/scan_audio.py` 是摸底用的索引（分别列出各 bank 与各 `.assets` 里的 clip 名），日常重建不需要重跑。

## 授权与致谢

- **字体**：Noto Serif SC（SIL Open Font License 1.1），子集化后内嵌于 `game.html`，许可全文见 `fonts/OFL.txt`
- **游戏音频**：版权归 Battlestate Games，不在本仓库内，提取物仅供自己玩，不要分发
- 仓库代码本身未声明开源许可
