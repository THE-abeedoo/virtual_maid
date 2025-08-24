# 虚拟女仆系统 (Virtual Maid 2025)

一个基于Python的智能虚拟女仆系统，支持语音合成、代码执行、智能对话等功能。

## 🌟 功能特性

- **智能对话**: 基于AI的智能对话系统
- **语音合成**: 支持多种语调的语音输出
- **代码执行**: 自动生成和执行Python代码
- **动画系统**: 丰富的动画效果和表情
- **配置管理**: 可视化的设置界面
- **快捷键支持**: Alt+D快速打开输入对话框

## 📋 系统要求

- **操作系统**: Windows 10/11, macOS, Linux
- **Python版本**: Python 3.11(其余未测试)
- **内存**: 至少 4GB RAM
- **存储空间**: 至少 2GB 可用空间
- **网络**: 需要网络连接以使用AI服务

## 🚀 安装指南

### 🎯 快速开始（推荐）

如果您使用的是 **Windows 系统**，我们提供了便捷的自动化安装和运行脚本：

1. **自动安装依赖**
   - 双击运行 `setup.bat` 文件
   - 脚本会自动检测Python环境并安装所有依赖包
   - 如果网络较慢，会自动尝试使用国内镜像源

2. **一键启动程序**
   - 双击运行 `run.bat` 文件
   - 脚本会自动检查环境并启动 VirtualMaid 2025
   - 无需手动输入命令

> 💡 **提示**: 首次使用请先运行 `setup.bat`，之后每次使用只需运行 `run.bat` 即可

> ⚠️ **注意**: `setup.bat` 和 `run.bat` 脚本仅适用于 Windows 系统。如果您使用 macOS 或 Linux，请参考下方的手动安装指南。

---

### 手动安装（适用于所有系统）

#### Windows用户：

1. **访问Python官网**
   - 打开浏览器，访问 [https://www.python.org/downloads/](https://www.python.org/downloads/)
   - 点击"Download Python 3.x.x"按钮

2. **下载安装程序**
   - 选择Windows installer (64-bit)
   - 下载完成后，双击运行安装程序

3. **安装Python**
   - **重要**: 勾选"Add Python to PATH"选项
   - 选择"Install Now"（推荐）或"Customize installation"
   - 等待安装完成

4. **验证安装**
   - 按`Win + R`，输入`cmd`打开命令提示符
   - 输入以下命令验证Python安装：
   ```cmd
   python --version
   ```
   - 应该显示类似`Python 3.x.x`的版本信息

#### macOS用户：

1. **使用Homebrew安装（推荐）**
   ```bash
   # 安装Homebrew（如果还没有安装）
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   
   # 安装Python
   brew install python
   ```

2. **或从官网下载**
   - 访问 [https://www.python.org/downloads/](https://www.python.org/downloads/)
   - 下载macOS安装包并运行

3. **验证安装**
   ```bash
   python3 --version
   ```

#### Linux用户：

1. **Ubuntu/Debian**
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip
   ```

2. **CentOS/RHEL**
   ```bash
   sudo yum install python3 python3-pip
   ```

3. **验证安装**
   ```bash
   python3 --version
   ```

### 第二步：下载项目文件

1. **克隆仓库（推荐）**
   ```bash
   git clone https://github.com/yourusername/virtualMaid_2025.git
   cd virtualMaid_2025
   ```

2. **或下载ZIP文件**
   - 点击仓库页面的"Code"按钮
   - 选择"Download ZIP"
   - 解压到本地目录

### 第三步：安装依赖包

1. **打开命令行**
   - Windows: 按`Win + R`，输入`cmd`，按回车
   - macOS/Linux: 打开终端

2. **进入项目目录**
   ```bash
   cd 项目路径/virtualMaid_2025
   ```

3. **安装依赖包**
   ```bash
   # 使用pip安装
   pip install -r requirements.txt
   
   # 如果上面的命令失败，尝试：
   pip3 install -r requirements.txt
   
   # 或者逐个安装主要依赖：
   pip install flask PyQt5 pynput openai
   ```

4. **验证安装**
   ```bash
   python -c "import flask, PyQt5, pynput; print('所有依赖安装成功！')"
   ```

### 第四步：配置API密钥

1. **获取OpenAI API密钥**
   - 访问 [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
   - 登录或注册账户
   - 创建新的API密钥

2. **配置API密钥**
   - 打开项目目录下的`maid_settings.json`文件
   - 找到`api_config`部分
   - 将您的API密钥填入`api_key`字段

### 第五步：运行程序

1. **启动设置界面**
   ```bash
   python app.py
   ```
   - 程序将在浏览器中打开设置界面
   - 默认地址: http://localhost:5000

2. **启动主程序**
   ```bash
   python main.py
   ```
   - 主程序将在后台运行
   - 按`Alt + D`打开输入对话框

## 🎮 使用方法

### 基本操作

1. **打开输入对话框**
   - 按快捷键 `Alt + D`
   - 或通过设置界面操作

2. **与女仆对话**
   - 输入自然语言描述您的需求
   - 女仆会智能分析并执行相应操作

3. **特殊命令**
   - `history`: 查看聊天历史
   - `clear_history`: 清空聊天记录
   - `quit`: 退出程序

### 设置界面

1. **访问设置界面**
   - 在浏览器中打开 http://localhost:5000
   - 或运行 `python app.py`

2. **配置选项**
   - 用户设置：设置您的称呼
   - 背景故事：自定义女仆的性格和背景
   - 动画设置：调整各种场景的动画效果
   - API配置：设置AI服务参数

3. **重置设置**
   - 点击"重置默认"按钮恢复出厂设置
   - 所有设置将重置为默认值

## 🔧 故障排除

### 🚀 Bat脚本相关问题

1. **setup.bat 运行失败**
   - 确保以管理员身份运行（右键 → 以管理员身份运行）
   - 检查是否有杀毒软件阻止脚本执行
   - 确保Python已正确安装并添加到PATH环境变量

2. **run.bat 无法启动程序**
   - 先运行 `setup.bat` 安装依赖
   - 检查 `main.py` 文件是否存在
   - 确保所有依赖包已正确安装

3. **批处理文件显示乱码**
   - 确保Windows系统支持UTF-8编码
   - 尝试在命令提示符中运行：`chcp 65001`

### 常见问题

1. **Python未找到**
   ```bash
   # 检查Python是否在PATH中
   python --version
   
   # 如果失败，尝试：
   python3 --version
   ```

2. **依赖包安装失败**
   ```bash
   # 升级pip
   python -m pip install --upgrade pip
   
   # 使用国内镜像源
   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
   ```

3. **端口被占用**
   ```bash
   # Windows查看端口占用
   netstat -ano | findstr :5000
   
   # 终止占用进程
   taskkill /PID 进程ID /F
   ```

4. **权限问题**
   ```bash
   # Windows以管理员身份运行命令提示符
   # macOS/Linux使用sudo
   sudo pip install -r requirements.txt
   ```

### 日志查看

- 程序运行时会显示详细的日志信息
- 错误信息会显示在控制台中
- 可以查看`chat_history.json`了解对话历史

## 📁 项目结构

```
virtualMaid_2025/
├── main.py                 # 主程序入口
├── app.py                  # Flask Web服务器
├── config_loader.py        # 配置加载器
├── call_ai.py             # AI调用模块
├── pr_image_processor.py   # 图像处理器
├── chat_history.py        # 聊天历史管理
├── input_dialog.py        # 输入对话框
├── prompt.py              # 提示词模板
├── requirements.txt        # 依赖包列表
├── maid_settings.json      # 配置文件
├── setup.bat              # 🚀 Windows自动安装脚本
├── run.bat                # 🎮 Windows一键启动脚本
├── static/                 # 静态文件
│   ├── css/               # 样式文件
│   └── js/                # JavaScript文件
├── templates/              # HTML模板
├── pr/                     # 动画资源
└── audio_cache/            # 音频缓存
```

## 🎨 自定义配置

### 动画设置

- 修改`maid_settings.json`中的`animation_settings`
- 每个场景可以设置：
  - `folder`: 动画文件夹名称
  - `scale_factor`: 缩放因子
  - `play_speed`: 播放速度
  - `loop`: 是否循环播放

### 背景故事

- 在设置界面中修改背景故事
- 影响AI的行为和对话风格
- 支持中文和英文

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用许可证 - 查看 [LICENSE](LICENSE) 文件了解详情


- 开发者: [高级qKen](https://space.bilibili.com/3493108973046446)

## 🔄 更新日志

### v1.0.0 (2025-08-19)
- 初始版本发布
- 支持基本的AI对话功能
- 集成语音合成
- 可视化设置界面
- 动画系统支持

---

**享受与您的虚拟女仆的互动时光！** 🎭✨