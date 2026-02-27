# SpeedDic - 桌面 AI 场景化语言学习助手

SpeedDic 是一款专为碎片化学习设计的桌面端工具。它将 AI 生成的场景化单词以“透明便利贴”的形式融入 Windows 桌面壁纸中，结合 SM-2 间隔重复算法，让你在日常使用电脑的间隙实现无感、高效的词汇积累。

## 🌟 核心特性

-   **AI 场景化生成**：支持 DeepSeek, OpenAI, Kimi, Qwen, GLM 等多种大模型。只需输入场景（如“互联网架构”、“西餐礼仪”），AI 即可为你定制词汇。
-   **桌面透明嵌入**：看板以透明层形式置于桌面图标之上。支持“鼠标穿透”模式，平时不干扰正常操作，仅在需要时通过快捷键激活交互。
-   **SM-2 记忆算法**：科学计算复习周期。提供“已掌握”、“模糊”、“不清楚”三个维度，自动安排每日待复习词汇。
-   **全局热键唤醒**：通过 `Ctrl + Alt + S` 一键切换交互模式，操作简单快捷。
-   **本地优先**：所有学习记录和 API Key 均存储在本地 SQLite 数据库，保护隐私，离线可用（生成新词需联网）。

## 🛠️ 技术栈

-   **核心语言**: Python 3.9+
-   **图形界面**: PyQt6
-   **数据库**: SQLite3
-   **AI 协议**: OpenAI Compatible API
-   **热键监听**: pynput
-   **数据校验**: Pydantic

## 🚀 Windows 使用指南

### 1. 环境准备
确保你的系统中已安装 Python 3.9 或更高版本。
- [Python 下载地址](https://www.python.org/downloads/windows/)（安装时请勾选 **Add Python to PATH**）。

### 2. 快速启动
1.  **下载项目**：将本项目文件夹拷贝至本地。
2.  **安装依赖**：
    在项目根目录打开 PowerShell 或 CMD，执行：
    ```powershell
    pip install -r requirements.txt
    ```
3.  **运行程序**：
    ```powershell
    python src/main.py
    ```

### 3. 配置与使用
1.  **设置 API**：右键点击右下角系统托盘图标 -> 选择 **“设置”**。
    - 填入你的 API Key。
    - 设置 Base URL（例如 DeepSeek 为 `https://api.deepseek.com`）。
    - 输入你感兴趣的 **“当前场景”**。
2.  **生成单词**：点击“保存设置并生成新词”，程序将自动从 AI 获取单词并展示在桌面。
3.  **交互模式**：
    - **锁定态（默认）**：看板透明穿透，你可以正常点击桌面的图标和文件。
    - **交互态**：按下 `Ctrl + Alt + S` 激活看板，此时可以点击单词下方的操作按钮。

## 📦 打包为独立程序 (.exe)
如果你希望在没有 Python 环境的电脑上运行，可以将其打包：
```powershell
pip install pyinstaller
pyinstaller --noconsole --onefile --add-data "src;src" --name "SpeedDic" src/main.py
```
打包后的程序将出现在 `dist` 文件夹中。

## 📝 快捷键说明
-   `Ctrl + Alt + S`：切换桌面看板的交互/穿透状态。

## ⚠️ 注意事项
-   **管理员权限**：如果你的某些应用以管理员身份运行，SpeedDic 也需要以管理员身份启动才能捕获热键。
-   **高分屏模糊**：如果遇到界面模糊，请在系统设置中调整缩放，或在程序启动逻辑中开启高 DPI 适配。
