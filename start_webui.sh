#!/bin/bash
# A股自选股智能分析系统 - 启动脚本
# 自动使用项目虚拟环境启动 Web UI，确保依赖库正确加载

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python3"
MAIN_PY="$SCRIPT_DIR/main.py"

if [ -f "$VENV_PYTHON" ]; then
    echo "✅ 使用虚拟环境: $VENV_PYTHON"
    "$VENV_PYTHON" "$MAIN_PY" --serve-only "$@"
else
    echo "❌ 错误: 找不到虚拟环境 $VENV_PYTHON"
    echo "请确认是否已安装依赖：pip install -r requirements.txt"
    exit 1
fi
