# 1sLLM-backend

<p style="text-align: center;">
    <a href="https://github.com/XingYuSSS"><img src="https://img.shields.io/badge/Github-XingYuSSS-blue?logo=github" /></a>
    <a href="https://github.com/yulinlp"><img src="https://img.shields.io/badge/Github-yulinlp-blue?logo=github" /></a>
    <a href="https://github.com/XingYuSSS/1sLLM-backend/tree/v0.1.0"><img src="https://img.shields.io/badge/version-0.1.0-brown.svg" alt="version"></a>
    <a href="https://github.com/XingYuSSS/1sLLM-frontend"><img src="https://img.shields.io/badge/link-frontend-green?logo=github" /></a>
    <a href="https://github.com/XingYuSSS/1sLLM-backend"><img src="https://img.shields.io/badge/link-backend-purple?logo=github" /></a>
    <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT License"></a>
</p>

这是1sLLM的后端，使用Flask框架编写。

仓库地址：https://github.com/XingYuSSS/1sLLM-backend

前端地址：https://github.com/XingYuSSS/1sLLM-frontend

## 简介

> 更多介绍请参考[前端](https://github.com/XingYuSSS/1sLLM-frontend)

一站式大模型访问：可以快捷简便的与多个大模型同时交互，比较生成内容，并随时切换。通过用户提供的API接口，将用户的提问同时发送给多个LLMs处理，然后将不同的回答整理后反馈给用户，提升访问效率和用户体验效果。

目标用户：同时使用多个大模型，需要频繁与模型交互，并希望以简便的方式获得最佳答案的人。

### 核心功能：

* 对比对话并列呈现
* ApiKey与历史会话管理
* 舒适的网页界面

## 运行方式

安装依赖：

```shell
pip install -r requirements.txt
```

运行：

```shell
python main.py
```

~~待补充~~

## License: MIT

该项目使用[MIT许可证](LICENSE)。
