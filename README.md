# SpeedDic — 摸鱼时学英语，老板还以为你在干活

> 透明桌面单词卡 · AI 场景化生词 · SM-2 间隔复习 · 全程鼠标穿透不影响操作

---

## 🌟 它能干什么？

上班摸鱼刷词汇。

SpeedDic 把 AI 生成的单词卡以**透明浮层**的形式贴在你的 Windows 桌面壁纸上。默认状态下鼠标可以穿透它点击桌面图标，看起来和正常工作毫无区别。想复习时按一下快捷键，按钮出现，打个分，再按一下，消失——整套流程 **3 秒内完成**。

你只需要告诉它你的"当前场景"，比如：

- `互联网架构` → 学 microservice、idempotent、circuit breaker
- `西餐礼仪` → 学 amuse-bouche、sommelier、mise en place
- `健身房` → 学 hypertrophy、compound lift、progressive overload
- `投资银行` → 学 underwriting、due diligence、covenant

AI 会按场景定制词条，SM-2 算法决定今天该复习哪些——**你只管上班，单词自己跑进脑子里**。

---

## 📦 核心特性

- **透明桌面嵌入**：单词卡置于桌面图标之上，默认鼠标穿透，完全不影响正常操作
- **AI 场景化生成**：输入任意场景，DeepSeek / OpenAI / Kimi / Qwen / GLM 等 OpenAI 兼容模型均可驱动
- **SM-2 间隔重复**：科学安排复习周期；"已掌握 / 模糊 / 不清楚"三档评分，自动调整下次出现时间
- **全局热键 `Ctrl+Alt+S`**：一键切换交互 / 穿透模式，3 秒完成一轮复习
- **本地优先**：学习记录与 API Key 均存于本地 SQLite，无数据上传，离线照常显示已有词库

---

## 🛠️ 技术栈

| 模块 | 技术 |
|---|---|
| 核心语言 | Python 3.9+ |
| 图形界面 | PyQt6 |
| 数据库 | SQLite3 |
| AI 协议 | OpenAI Compatible API |
| 热键监听 | pynput |
| 数据校验 | Pydantic |

---

## 🚀 快速上手（Windows）

### 1. 安装依赖

确保已安装 Python 3.9+（安装时勾选 **Add Python to PATH**）：

```powershell
pip install -r requirements.txt
```

### 2. 启动

建议以**管理员身份**打开 PowerShell / CMD，在项目根目录执行：

```powershell
python src/main.py
```

### 3. 配置场景

1. 右键系统托盘图标 → **"设置"**
2. 填入 API Key 与 Base URL（如 DeepSeek：`https://api.deepseek.com`）
3. 在"当前场景"填写你想学的领域
4. 点击"保存设置并生成新词" → 后台异步生成，完成后桌面自动展示

### 4. 日常使用

| 操作 | 效果 |
|---|---|
| 什么都不做 | 单词卡静静显示在壁纸上，鼠标穿透，正常办公 |
| `Ctrl+Alt+S` | 激活交互模式，标题栏变绿，按钮可点击 |
| 点击评分按钮 | SM-2 记录本次复习，自动安排下次出现时间 |
| 再按 `Ctrl+Alt+S` | 恢复穿透，回到摸鱼状态 |

---

## 注意事项

- **管理员权限**：若前台有以管理员身份运行的程序（任务管理器、某些游戏），SpeedDic 也需要管理员权限才能捕获 `Ctrl+Alt+S`
- **高分屏模糊**：如界面模糊，请在系统显示设置中调整缩放比例

