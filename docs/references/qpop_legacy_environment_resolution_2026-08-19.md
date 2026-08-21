# Q-POP CPC v1 旧版运行环境决议

- 日期：2026-08-19
- 研究范围：仅解析冻结 CPC v1 `Q-POP-IMT` 快照在 Ubuntu 20.04 上的可执行环境；未安装依赖，未启动或修改 Q-POP，未产生数值结果。
- 证据状态：`PRIMARY_SOURCE_AUDIT_COMPLETE`
- 环境路线裁决：`MANUAL_SOURCE_STACK_ON_UBUNTU_20_04`
- 关键限定：上游只冻结了依赖“主干”，没有提供完整的传递依赖锁、容器 digest 或可重建镜像。因此本文件给出的是“上游明确测试的主干 + 在首次构建前冻结的项目解析层”，不能称为作者官方完整环境。

## 1. 决策摘要

G2 应采用专用 Ubuntu 20.04 WSL2 发行版，在同一 GNU-9/OpenMPI-3.1.6 ABI 下从源码构建 PETSc-3.15.1、petsc4py 和 DOLFIN-2019.1.0.post0，再运行冻结的 CPC v1 Python 程序。这个组合逐项对应 Q-POP 官方环境页明确写出的“recommended / necessary / all testing was done with”版本：[Q-POP Environment Setup](https://q-pop.pages.dev/prepare)。

不选择以下捷径：

- `apt install fenics`：Ubuntu 20.04 官方仓库确有 FEniCS 2019.1.0，但其 OpenMPI 是 4.0.3；这不等于 Q-POP 明确测试的 OpenMPI 3.1.6 组合。[Ubuntu Focal FEniCS](https://launchpad.net/ubuntu/+source/fenics/1%3A2019.1.0.3)；[Ubuntu Focal OpenMPI](https://launchpad.net/ubuntu/focal/amd64/openmpi-bin/4.0.3-0ubuntu1)
- FEniCS PPA：Focal 的 PPA 内容已继续演进，不能作为 2019.1.0.post0 的不可变来源。[FEniCS PPA](https://launchpad.net/~fenics-packages/+archive/ubuntu/fenics)
- Conda：FEniCS 官方旧版安装页将 Conda 标为 experimental；其二进制能力尤其是稀疏直接求解器和 I/O 并非完整保证。Q-POP 也没有提供 conda 锁文件。[FEniCS legacy download](https://fenicsproject.org/download/archive/)；[FEniCS installation](https://fenics.readthedocs.io/en/latest/installation.html)
- Docker：Q-POP CPC v1 包内没有 Dockerfile、OCI digest 或镜像引用。FEniCS 官方页面提供的是通用且会变化的镜像路线，不证明其 OpenMPI/PETSc/MUMPS 与 Q-POP 测试栈一致。[FEniCS legacy download](https://fenicsproject.org/download/archive/)

结论不是“其他路线一定不能运行”，而是它们不能满足本项目 G2 对来源唯一、环境可解释和 MUMPS 可验证的要求。

## 2. 上游真正冻结了什么

| 层 | 上游证据 | 可登记状态 | 未冻结项 |
| --- | --- | --- | --- |
| OS | Q-POP 推荐 Ubuntu 20.04，以获得较少摩擦的安装路径。 | `UPSTREAM_RECOMMENDED` | Ubuntu 镜像 digest、apt snapshot、内核、WSL 版本 |
| 编译器 | Q-POP 写明必须使用 GNU Compiler Collection 9，并列出 `gcc-9/g++-9/gfortran-9`。 | `UPSTREAM_REQUIRED_MAJOR` | GCC 9 的 patch/build 号及编译 flags |
| MPI | 所有测试使用 OpenMPI 3.1.6；Q-POP 要求从官方源码安装到用户目录。Open MPI 官方发布页登记 3.1.6、2020-03-18 tarball，`openmpi-3.1.6.tar.gz` SHA1 为 `5c220f8f0c5070cbb43bc8af6200b91339cdccd5`。 | `UPSTREAM_TESTED_EXACT_VERSION` | configure flags、最终二进制 hash；Q-POP 未给 SHA256 |
| Boost | 所有测试使用 Boost 1.71.0；Q-POP 指定 Ubuntu 20.04 的 `libboost-dev`。Ubuntu Focal 的元包版本为 `1.71.0.0ubuntu2`。 | `UPSTREAM_TESTED_EXACT_UPSTREAM_VERSION` | Ubuntu 安全更新后的二进制 hash；仅 `libboost-dev` 不覆盖 DOLFIN 列出的全部编译库 |
| PETSc | 所有测试使用 PETSc 3.15.1；Q-POP 给出 METIS、ParMETIS、PT-Scotch、SuiteSparse、MUMPS、ScaLAPACK、Hypre、指定 MPI 和 petsc4py 的配置集合。PETSc 官方 tag `v3.15.1` 指向 `09da24df01e50defd94bc4f7396f866a808ecea5`。 | `UPSTREAM_TESTED_EXACT_VERSION_AND_FEATURE_SET` | BLAS/LAPACK 来源、debug/optimization、标量与索引默认值、各 `--download-*` 包的最终 tarball hash |
| DOLFIN | Q-POP 指定 `2019.1.0.post0` tag，并要求同时构建 C++ 与 Python 接口。Read the Docs 仍登记该确切版本；FEniCS 将 2019.1.0 称为 legacy stable release。 | `UPSTREAM_REQUIRED_EXACT_TAG` | tag commit/hash 未写入 Q-POP 文档、CMake build type、完整 Python 依赖锁 |
| FFC 及 Python FEniCS 组件 | Q-POP 调用 `pip3 install fenics-ffc --upgrade`；在 legacy 稳定系列中，最终 FFC 为 2019.1.0.post0，依赖系列为 FIAT/UFL/dijitso 2019.1.0。 | `SERIES_IDENTIFIED_BUT_QPOP_COMMAND_UNPINNED` | pip resolver、NumPy、PLY、setuptools 等实际版本 |
| Python | FEniCS 官方文档只要求 Python 3；Ubuntu 20.04 默认 Python 3 系列是 3.8，当前 Focal 更新为 3.8.10。 | `DISTRO_DERIVED_NOT_QPOP_PINNED` | Q-POP 作者测试的 Python minor/patch |
| MUMPS | CPC canonical input 明确选择 `mumps`；Q-POP PETSc 配置也明确 `--download-mumps`。PETSc 官方文档确认 MUMPS 需要 Fortran，并通过 PETSc 外部包配置启用。 | `CASE_REQUIRED_CAPABILITY` | MUMPS 的确切上游版本和 hash，须从 PETSc-3.15.1 的配置产物中锁定 |

主来源：[Q-POP Environment Setup](https://q-pop.pages.dev/prepare)、[Q-POP Build and Run](https://q-pop.pages.dev/run)、[Open MPI 3.1 releases](https://www.open-mpi.org/software/ompi/v3.1/)、[PETSc v3.15.1 tag](https://gitlab.com/petsc/petsc/-/tags/v3.15.1)、[PETSc configuration](https://petsc.org/release/install/install/)、[DOLFIN 2019.1.0.post0](https://app.readthedocs.org/projects/fenics-dolfin/)、[FEniCS legacy installation](https://fenics.readthedocs.io/en/latest/installation.html)。

### 2.1 版本关系的正确解释

- Q-POP 要求的是 legacy `DOLFIN/FEniCS 2019.1.0.post0` API，不是 DOLFINx/FEniCSx。`qpop-imt.py` 的 `from fenics import *`、`MPI.comm_world`、`PETScOptions` 和 `NonlinearVariationalSolver` 都属于旧接口。
- `FEniCS 2019.1.0` 是组件系列名；DOLFIN 和 FFC 使用修订 tag `2019.1.0.post0`，而 FIAT、UFL、dijitso 的 PyPI 版本是 `2019.1.0`。这不是版本冲突。[FFC 2019.1.0.post0](https://pypi.org/project/fenics-ffc/2019.1.0.post0/)；[FIAT 2019.1.0](https://pypi.org/project/fenics-fiat/2019.1.0/)；[UFL 2019.1.0](https://pypi.org/project/fenics-ufl/2019.1.0/)；[dijitso 2019.1.0](https://pypi.org/project/fenics-dijitso/2019.1.0/)
- Python 3.8 是 Ubuntu 20.04 的自然解析结果，而不是论文或 Q-POP 文档明确给出的作者 Python 版本。Ubuntu 自身曾成功发布 FEniCS 2019.1.0 和 DOLFIN 2019.1.0，这只支持“Python 3.8 路线可成立”的工程判断，不证明与作者机器逐字节等价。[Ubuntu Focal Python 3.8](https://launchpad.net/ubuntu/focal/+package/python3.8)；[Ubuntu DOLFIN package history](https://launchpad.net/ubuntu/+source/dolfin)

## 3. 为什么不能直接使用 apt、Docker 或 Conda

### 3.1 Ubuntu apt

Ubuntu Focal 发布了 `fenics 1:2019.1.0.3` 和 `dolfin 2019.1.0-10build2`，所以 apt 是一个真实存在的 legacy FEniCS 路线，并非假想方案。但是 Focal 的 `openmpi-bin` 是 4.0.3，而 Q-POP 明确称全部测试基于 OpenMPI 3.1.6，并警告更新版本可能不工作。混合 apt DOLFIN/OpenMPI4 与用户目录 OpenMPI3 还会引入双 MPI ABI 风险。因此 apt 只能用于编译工具和无 ABI 冲突的系统库，不能提供本次 DOLFIN/PETSc/MPI 核心。

### 3.2 Docker

FEniCS 官方旧文档曾推荐 `quay.io/fenicsproject/stable:current`，当前归档页又展示了不同的通用镜像。`current` 是可变 tag；两条路线都没有 Q-POP 所需的 OpenMPI-3.1.6、PETSc-3.15.1、MUMPS 和 Q-POP CPC v1 源码组合证明。CPC 程序包中也没有作者 Docker recipe。因此本项目现在自行选择任意 FEniCS 镜像，会把环境来源从 `VERIFIED` 降为 `AMBIGUOUS`。

### 3.3 Conda

FEniCS 官方确实记录 `conda install -c conda-forge fenics`，但同时将该支持标为 experimental；归档下载页还专门警告二进制包的稀疏直接求解器和 I/O 功能并不完整。canonical case 必须有 MUMPS，且 Q-POP 没有 environment.yml 或 build string，所以不能把一个由当前 solver 动态解析出的 conda 环境称为 CPC v1 环境。

## 4. 决策就绪的最小构建路线

以下是供 G2 执行器实现的构建蓝图，不是已经执行的命令记录。路径应限于专用 WSL 发行版中的单一前缀，例如 `$HOME/qpop-cpc-v1-env`；不得把 Windows Python、Windows MPI 或项目 Python 3.11 venv 混入该栈。

### 4.1 系统层

使用 Ubuntu 20.04 官方仓库安装最小构建依赖：

```sh
sudo apt-get update
sudo apt-get install --no-install-recommends \
  ca-certificates git wget tar make cmake pkg-config \
  gcc-9 g++-9 gfortran-9 \
  python3 python3-dev python3-pip python3-venv python3-distutils \
  libeigen3-dev zlib1g-dev \
  libboost-dev libboost-filesystem-dev libboost-iostreams-dev \
  libboost-program-options-dev libboost-timer-dev
```

补列四个 Boost 编译库来自 DOLFIN 官方依赖表；Q-POP 只写 `libboost-dev`，而 Ubuntu 将它描述为主要提供 headers 的元包，所以单独使用它不足以建立完整 DOLFIN 依赖。[DOLFIN dependencies](https://fenics.readthedocs.io/projects/dolfin/en/2017.2.0/installation.html)；[Ubuntu Focal libboost-dev](https://launchpad.net/ubuntu/focal/+package/libboost-dev)

不要安装 `openmpi-bin`、`libopenmpi-dev`、`fenics`、`python3-mpi4py` 或 PPA FEniCS；它们会把 OpenMPI4 或另一个 PETSc/DOLFIN ABI 带入核心栈。

GNU-9 可用显式环境变量限定在当前构建会话，而不修改整台发行版的 alternatives：

```sh
export CC=/usr/bin/gcc-9
export CXX=/usr/bin/g++-9
export FC=/usr/bin/gfortran-9
```

这是对 Q-POP“GNU-9 必须为默认编译器”要求的作用域化等价实现；其正确性必须由最终 `ompi_info`、PETSc configure log 和 DOLFIN CMake cache 验证。

### 4.2 Python 解析层

建立专用 Python 3.8 venv。Q-POP 没有冻结 NumPy、mpi4py、pybind11、Cython、pip 或 setuptools，因此不得把下述解析候选冒充上游版本：

```sh
python3 -m venv "$HOME/qpop-cpc-v1-env/py38"
. "$HOME/qpop-cpc-v1-env/py38/bin/activate"
python -m pip install --upgrade pip wheel setuptools
python -m pip install \
  'numpy<1.24' 'Cython<3' 'pybind11==2.2.3' 'ply==3.11' pkgconfig
```

- `pybind11==2.2.3` 来自 FEniCS 官方 legacy 源码安装说明。
- `numpy<1.24`、`Cython<3` 是避免旧代码与现代重大版本不兼容的项目候选约束，不是作者 freeze；首次成功解析后必须把确切版本与文件 SHA256 写入环境锁。
- 若必须更改这些候选才能构建，只能进行计划允许的一次纯基础设施修正，并保留原失败记录；不能修改 Q-POP 方程或案例。

FEniCS Python 组件应明确锁为：

| 包 | 版本 | PyPI wheel SHA256 |
| --- | --- | --- |
| `fenics-ffc` | `2019.1.0.post0` | `54d7529ca6306f32e15e8e4a26f32a3d2ec68902262191148b32c92657a6851f` |
| `fenics-fiat` | `2019.1.0` | `6bf99374ed320017f853a573a21fe31763cba14b9c0459f4000edb12f83731ba` |
| `fenics-ufl` | `2019.1.0` | `a7de887a71c1643494ab84af67d837f8e0210f64fcf7ef7fc7309c25a0990d9c` |
| `fenics-dijitso` | `2019.1.0` | `ddb2c54e3e567b2639f492943c5457bf391c49eccda7343edf7d9414b10841a5` |

这些 hash 来自各包的 PyPI 文件元数据，PyPI maintainer 均登记为 `fenicsproject`；执行时应先下载到源缓存并以 hash 安装，不执行无界 `--upgrade`。

### 4.3 OpenMPI 3.1.6

严格使用 Q-POP 指向的 Open MPI 官方 release tarball，安装到独立前缀：

```sh
export QPOP_ENV="$HOME/qpop-cpc-v1-env"
export MPI_DIR="$QPOP_ENV/openmpi-3.1.6"

# 下载后先核对官方 SHA1；同时计算并写入项目环境锁的 SHA256。
# openmpi-3.1.6.tar.gz SHA1:
# 5c220f8f0c5070cbb43bc8af6200b91339cdccd5

CC=/usr/bin/gcc-9 CXX=/usr/bin/g++-9 FC=/usr/bin/gfortran-9 \
  ./configure --prefix="$MPI_DIR"
make all
make install
export PATH="$MPI_DIR/bin:$PATH"
export LD_LIBRARY_PATH="$MPI_DIR/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
```

Open MPI 官方说明 release tarball 可用传统 `configure && make && make install` 构建，并警告不要用 GitHub 自动生成的不完整 tarball。[Open MPI source-build guide](https://docs.open-mpi.org/en/main/installing-open-mpi/quickstart.html)

`mpi4py` 必须在这个 MPI 已进入 `PATH/LD_LIBRARY_PATH` 后从源码构建，不能复用 apt wheel 或旧 cache。Q-POP 本身没有 pin；首选可审计候选是 `mpi4py==3.0.3` 源码包，因为其发布元数据覆盖 CPython 3.8，且 SHA256 为 `012d716c8b9ed1e513fcc4b18e5af16a8791f51e6d1716baccf988ad355c5a1f`：[mpi4py 3.0.3](https://pypi.org/project/mpi4py/3.0.3/)。

```sh
MPICC="$MPI_DIR/bin/mpicc" \
  python -m pip install --no-cache-dir --no-binary=mpi4py 'mpi4py==3.0.3'
```

该 3.0.3 pin 是项目的最小兼容候选，不是 Q-POP 作者声明；只有后续 ABI 检查和 G2 nonlinear-step smoke 才能把它提升为本项目已验证环境的一部分。

### 4.4 PETSc 3.15.1、MUMPS 与 petsc4py

从 PETSc 官方 GitLab tag `v3.15.1` 获取源码，并在构建前核对完整 commit `09da24df01e50defd94bc4f7396f866a808ecea5`。使用 Q-POP 明列的外部包集合和同一个 `MPI_DIR`：

```sh
export PETSC_DIR="$QPOP_ENV/src/petsc"
export PETSC_ARCH=arch-linux-qpop-opt

python "$PETSC_DIR/configure" \
  --with-mpi-dir="$MPI_DIR" \
  --with-debugging=0 \
  --download-fblaslapack \
  --download-metis \
  --download-parmetis \
  --download-ptscotch \
  --download-suitesparse \
  --download-mumps \
  --download-scalapack \
  --download-hypre \
  --with-petsc4py
make PETSC_DIR="$PETSC_DIR" PETSC_ARCH="$PETSC_ARCH" all
make PETSC_DIR="$PETSC_DIR" PETSC_ARCH="$PETSC_ARCH" check
```

`--download-fblaslapack` 和 `--with-debugging=0` 是为裸 Ubuntu 构建完整数值栈和可用吞吐而作的项目解析，不在 Q-POP 原始配置片段中；必须在环境合同中标为 `PROJECT_RESOLUTION`。PETSc 官方说明 `--download-*` 是推荐的外部包耦合方式、MUMPS 需要 Fortran、`--with-mpi-dir` 会选择该前缀的 MPI wrappers，并且 OpenMPI shared libraries 需要正确的 `LD_LIBRARY_PATH`。[PETSc configuration](https://petsc.org/release/install/install/)；[PETSc quick start](https://petsc.org/release/install/install_tutorial/)

PETSc configure 完成后，必须保存：

- tag、commit、PETSc 源码 SHA256；
- 完整 configure 命令、`configure.log` 和 reconfigure script；
- 每个自动下载外部包的实际 URL、版本和 SHA256；
- `PETSC_ARCH`、scalar type、precision、index size、debug/optimization 和编译器身份；
- `petsc4py` 实际版本。若改为 PyPI sdist，其 3.15.1 官方 SHA256 为 `4ec8f42081e4d6a61157b32869b352dcb18c69077f2d1e4160f3837efd9e150f`：[petsc4py 3.15.1](https://pypi.org/project/petsc4py/3.15.1/)。

### 4.5 DOLFIN/FEniCS 2019.1.0.post0

先安装上表四个固定 Python 组件，再从 FEniCS 官方 Bitbucket tag 获取 DOLFIN。构建和 Python 安装必须在同一个 venv、OpenMPI 和 PETSc 环境内完成：

```sh
python -m pip install \
  'fenics-fiat==2019.1.0' \
  'fenics-ufl==2019.1.0' \
  'fenics-dijitso==2019.1.0' \
  'fenics-ffc==2019.1.0.post0'

git clone --branch=2019.1.0.post0 \
  https://bitbucket.org/fenics-project/dolfin.git \
  "$QPOP_ENV/src/dolfin"

cmake -S "$QPOP_ENV/src/dolfin" -B "$QPOP_ENV/src/dolfin/build" \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX="$QPOP_ENV/fenics/dolfin"
cmake --build "$QPOP_ENV/src/dolfin/build"
cmake --install "$QPOP_ENV/src/dolfin/build"
python -m pip install "$QPOP_ENV/src/dolfin/python"
. "$QPOP_ENV/fenics/dolfin/share/dolfin/dolfin.conf"
```

首次 clone 后、编译前必须登记 tag 对应的完整 commit 和工作树 hash；若 tag 已不能唯一解析，则停止，而不是切换到 `master`、FEniCSx 或 Ubuntu 的 2019.2 legacy snapshot。`CMAKE_BUILD_TYPE=Release` 是项目解析项；Q-POP 文档没有冻结 build type。

## 5. 在运行 Q-POP 前必须通过的环境验收

这些检查只验证 ABI/功能，不是科学结果：

1. `lsb_release`/`/etc/os-release` 显示 Ubuntu 20.04；所有编译器为 GNU 9。
2. `which mpirun/mpicc` 均位于 `$MPI_DIR`，`ompi_info` 报告 3.1.6。
3. Python、mpi4py、PETSc/petsc4py、DOLFIN 加载的是同一 `libmpi`；不得同时链接 `/usr/lib/.../openmpi` 和 `$MPI_DIR/lib`。
4. `PETSc.Sys.getVersion()` 为 `(3, 15, 1)`；PETSc configure summary 同时列出 MUMPS、ParMETIS、PT-Scotch、ScaLAPACK 和 Hypre。
5. DOLFIN 为 legacy 2019.1.0 系列；`has_lu_solver_method("mumps")` 为真，mesh partitioner 列表包含 ParMETIS。
6. 两个 MPI rank 能在同一个 venv 中导入 `fenics`、`mpi4py`、`petsc4py` 并完成 communicator barrier。
7. 保存 `dpkg-query`、`pip freeze --all`、source/hash lock、`ompi_info --all`、PETSc configure log、DOLFIN CMake cache 和共享库解析结果；之后禁止无记录升级。

只有以上全部通过，才允许按 G2 规则把 canonical input 的唯一改动限制为缩短 `endtime`，启动至少一个有效 nonlinear step。环境导入成功本身不能标记 `G2_PASS`。

## 6. 停止条件

出现任一情况，应把环境/source subroute 判为 `BLOCKED` 或把实际运行判为计划规定的 `ENGINEERING_BLOCKED`，不得以换物理、换案例或换现代 solver 救援：

- DOLFIN `2019.1.0.post0` tag、PETSc `v3.15.1` tag或 OpenMPI 3.1.6 官方 tarball无法唯一获取和 hash；
- 需要修改 Q-POP 方程、canonical 参数、网格、边界或 solver 语义才能导入/前进；
- `mpirun`、mpi4py、PETSc、petsc4py、DOLFIN 混用了 OpenMPI3 和 OpenMPI4 ABI；
- PETSc 或 DOLFIN 未暴露 MUMPS、ParMETIS，或 canonical `directsolver=mumps` 被静默替换；
- Python 解析只能通过未固定的当前 FEniCSx/NumPy/Cython 大版本完成；
- 首次失败后，一次有明确因果的纯基础设施修正仍不能贯通最短链路；
- 选择 apt/Conda/Docker 替代路线，却不能给出与 Q-POP 测试主干逐项一致的版本、feature 和 digest 证据。

## 7. 最终证据边界

- `VERIFIED`：Q-POP 官方文档确实指定 Ubuntu 20.04、GNU 9、OpenMPI 3.1.6、Boost 1.71.0、PETSc 3.15.1、DOLFIN 2019.1.0.post0，并要求 PETSc 包含 MUMPS 等列出的外部求解能力。
- `VERIFIED`：Ubuntu、Open MPI、PETSc、FEniCS 和 PyPI 的一手元数据证明这些版本/标签/包存在；Ubuntu apt 的 OpenMPI4 与 Q-POP tested stack 不同。
- `SUPPORTED_INTERPRETATION`：Ubuntu 20.04 + Python 3.8 + 手工源码栈是当前最短且来源最清楚的复现路线。
- `UNKNOWN`：作者实际 Python patch、NumPy/mpi4py/Cython/pybind11、PETSc transitive tarballs、compiler flags、debug/build type 和硬件；它们只能由本项目首次成功构建后的环境锁固定。
- `NOT_VERIFIED`：该环境已经成功编译、Q-POP 已启动、canonical case 已复现、守恒或物理有效性已通过。以上均须由后续 G2/G3 运行 manifest 和 qualification evidence 建立。
