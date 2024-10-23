# FSD_Python_Ver

> FSD 作业的 75% 实现，目前 CLI 完全可用，GUI 还有一点小问题，在 Debug阶段

## 架构说明

- MCV 架构

  - Model - CLI & GUI 共用

  - Controller - CLI & GUI 共用

  - View - CLI

             - GUI -> Flet UI 框架

## 环境需求

- IDE：Pycharm（>=2024.2）
- Python：3.11.9

## PR 须知

遵守 [gitmoji](https://gitmoji.dev/) 提交规范，简述为 Emoji + 描述。

## 使用须知

需安装依赖：`pip install -r requirements.txt`（请在 Pycharm 虚拟环境内安装）

运行入口函数`cli_main.py`（CLI）和`flet_main.py`（GUI）其一即可