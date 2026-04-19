# Other Solver Experiment

这个目录是用来复现 `othe_solver.md` 里描述的那套生成与唯一解验证逻辑。

目的：

- 不影响当前主项目代码
- 单独验证那套生成器和 solver 的行为
- 方便和当前 `backend/nonogram` 做对比实验

建议运行方式：

```bash
cd /home/thecats/CUTECODE/nono_web
/opt/miniconda/envs/py312/bin/python experiments/other_solver/run_experiment.py
```

如果想改样本量或密度范围，可以直接修改 `run_experiment.py` 里的参数。
