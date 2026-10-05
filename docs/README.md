# LMCache 内部说明文档

当前 P6 使用本仓文档，不套用上游 CUDA/四包插件安装方式。

- [基线一致的安装部署与验证](source/getting_started/baseline_validation.rst)：两仓成对安装，沿用 native-layout 的指令和启动配置。
- [原生目录与继承关系](source/getting_started/native_layout.rst)：目录职责、固定材料及 ABI 边界。
- [正式验收和回退](source/getting_started/release_operations.rst)：wheel/镜像证据和成对恢复要求。

`docs/design/` 的旧阶段记录保留为历史依据，旧插件路径及部署例子不是当前操作入口。
Sphinx 仅收录 `docs/source/index.rst` 列出的当前页面。使用已有文档工具在源码主机运行：

```bash
DOCS_OUTPUT=$(mktemp -d /tmp/lmcache-docs.XXXXXXXX)
sphinx-build -E -W -b html docs/source "$DOCS_OUTPUT"
```

命令从仓根执行；输出应无警告。打开 `$DOCS_OUTPUT/index.html` 检查页面和导航。
文档构建不需要安装 torch/CANN，也不证明内网编译或模型验证通过。
