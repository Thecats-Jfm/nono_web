# 环境说明

## Python 解释器

这个仓库后端统一使用下面这个 Python 解释器：

```bash
/opt/miniconda/envs/py312/bin/python
```

不要默认使用系统里的：

```bash
python3
```

因为当前机器上的 `python3` 指向的是另一个环境，容易出现这些问题：

- `pytest` 找不到
- `fastapi` 或其他依赖找不到
- 同一个仓库在不同命令下跑到不同环境里

## 后端常用命令

在仓库根目录下执行：

```bash
cd /home/thecats/CUTECODE/nono_web/backend
```

运行测试：

```bash
/opt/miniconda/envs/py312/bin/python -m pytest -q
```

启动开发服务：

```bash
/opt/miniconda/envs/py312/bin/python -m uvicorn app:app --reload
```

临时运行脚本：

```bash
/opt/miniconda/envs/py312/bin/python some_script.py
```

## 约定

以后这个仓库里只要涉及后端 Python：

- 默认使用 `/opt/miniconda/envs/py312/bin/python`
- 不再使用裸 `python3`

如果后面我们补 `README`，这段也可以再同步进去。
