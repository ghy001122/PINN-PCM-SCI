# Gradient Scaling Effects in Adaptive Spectral PINNs for Stiff Nonlinear ODEs

paper_id: arxiv:2605.04502v1
tier: T3
source_used: html_arxiv
warning: none

## Intro

Physics-Informed Neural Networks (PINNs) provide a flexible, mesh-free framework
for solving differential equations by embedding known physics into the training
objective. Despite their conceptual appeal, PINNs often struggle in stiff and
highly oscillatory regimes, where optimization becomes unstable or converges to
inaccurate solutions even when the governing equations are enforced exactly.
A central contributor to this behavior is spectral bias: standard neural
networks tend to learn low-frequency components of a target function much more
rapidly than high-frequency components. As stiffness increases and multiple time
scales emerge, the directions in function space corresponding to fast
oscillations become increasingly poorly conditioned under gradient-based
optimization. This phenomenon has been analyzed through optimization and kernel
perspectives, including Neural Tangent Kernel (NTK) analyses showing severe
eigenvalue imbalance and effective rank collapse in physics-informed settings
(
Jacot et al. 2018
;
Wang et al. 2021
)
.
Representation-level remedies have therefore received significant attention.
Fourier feature networks reshape the effective kernel spectrum seen by gradient
descent and accelerate the learning of oscillatory components
(
Wang et al. 2020
)
, while more recent Separated-Variable Spectral Neural
Networks (SV-SNN) introduce explicit spectral structure to improve conditioning
and prevent rank collapse in high-frequency PDEs
(
Xiong et al. 2025
)
. These
approaches demonstrate that representation choice plays a critical role in
stabilizing optimization in stiff regimes.
In this work, we adopt a complementary optimization-driven perspective and
identify an additional, often underemphasized design choice that strongly
influences training dynamics: the parameterization used to enforce initial
conditions. The use of output transformations to enforce initial or boundary
conditions dates back to
Lagaris et al. 1998
and is widely used in PINNs
(e.g.,
Babni et al. 2025
). While typically viewed as representationally
neutral, we make explicit that IC gating induces time-dependent Jacobian scaling.
Under linearization, gradient descent dynamics are governed by Jacobian inner
products (NTK), and the IC gate rescales these Jacobians
across the physical ODE trajectory
t
t
, thereby modifying optimization conditioning
without changing the underlying function class defined by the IC constraint.
Using a nonlinear stiff spring–pendulum ODE as a controlled benchmark, we
systematically compare exponential and linear IC gates in combination with fixed
and adaptive Fourier spectral trunks. We observe stiffness-dependent changes in
relative dominance: exponential gating performs better at moderate stiffness,
whereas linear gating becomes preferable at higher stiffness levels, with
additional reversals observed at larger
k
k
. Our study is intentionally diagnostic:
by isolating IC gating under fixed optimization settings, we expose how this
architectural choice reshapes conditioning in stiff regimes.

## Method

We study the planar spring–pendulum system in polar coordinates
𝒖
⁡
(
t
)
=
[
r
⁡
(
t
)
,
θ
⁡
(
t
)
]
⊤
{\bm{u}}(t)=[r(t),\theta(t)]^{\top}
, governed by the second-order ODE
r
¨
\displaystyle\ddot{r}
=
r
θ
˙
2
−
k
m
(
r
−
L
0
)
+
g
cos
θ
−
c
r
m
r
˙
,
\displaystyle=\;r\dot{\theta}^{2}-\frac{k}{m}(r-L_{0})+g\cos\theta-\frac{c_{r}}{m}\dot{r},\qquad
θ
¨
\displaystyle\ddot{\theta}
=
−
2
​
r
˙
​
θ
˙
r
−
g
r
​
sin
⁡
θ
−
c
θ
​
θ
˙
.
\displaystyle=\;-\frac{2\dot{r}\dot{\theta}}{r}-\frac{g}{r}\sin\theta-c_{\theta}\dot{\theta}.
(1)
The spring constant
k
k
controls the stiffness of the system.
All experiments are conducted over a fixed time horizon
T
=
10
T=10
, with
physical parameters
g
=
9.81
g=9.81
,
m
=
1.0
m=1.0
,
L
0
=
1.0
L_{0}=1.0
,
c
r
=
c
θ
=
0
c_{r}=c_{\theta}=0
,
and
r
min
=
10
−
4
r_{\min}=10^{-4}
.
High-accuracy reference solutions are generated using
solve_ivp
with the
DOP853
integrator and strict
tolerances.
Initial positions are enforced exactly by construction using:
𝒖
^
​
(
t
)
=
𝒖
0
+
g
⁡
(
t
)
​
𝒖
~
​
(
t
)
\hat{{\bm{u}}}(t)={\bm{u}}_{0}+g(t)\,\tilde{{\bm{u}}}(t)
where
g
⁡
(
0
)
=
0
g(0)=0
and
𝒖
~
​
(
t
)
=
[
ρ
⁡
(
t
)
~
,
θ
⁡
(
t
)
~
]
⊤
\tilde{{\bm{u}}}(t)=[\tilde{\rho(t)},\tilde{\theta(t)}]^{\top}
is the unconstrained network output. Differentiation shows that the latent output at
t
=
0
t=0
determines the initial velocity:
for the angular component,
θ
~
​
(
0
)
\tilde{\theta}(0)
equals
θ
˙
​
(
0
)
\dot{\theta}(0)
, while for the
radial component the velocity is proportional to
ρ
~
​
(
0
)
\tilde{\rho}(0)
, scaled by the
constant factor
σ
⁡
(
ρ
0
)
\sigma(\rho_{0})
arising from the softplus derivative.
Initial velocity is not enforced exactly but is instead penalized during training.
We compare two common gating functions:
an exponential gate
g
⁡
(
t
)
=
1
−
e
−
t
g(t)=1-e^{-t}
and a linear gate
g
⁡
(
t
)
=
t
g(t)=t
.
Both gating functions satisfy the admissibility conditions of
Babni et al. 2025
,
i.e.,
g
⁡
(
0
)
=
0
g(0)=0
,
g
′
​
(
0
)
≠
0
g^{\prime}(0)\neq 0
, and no additional zeros on
(
0
,
T
]
(0,T]
.
To ensure positivity of the radial coordinate, after the gate, we apply
r
⁡
(
t
)
=
r
min
+
ζ
⁡
(
ρ
⁡
(
t
)
^
)
,
r
min
>
0
.
r(t)=r_{\min}+\zeta(\hat{\rho(t)}),\qquad r_{\min}>0.
Here
ζ
⁡
(
x
)
=
log
⁡
(
1
+
e
x
)
\zeta(x)=\log(1+e^{x})
is the smooth softplus function, ensuring
positivity of
r
⁡
(
t
)
r(t)
while differentiable.
As a baseline, we use a standard fully connected PINN in which
𝒖
~
​
(
t
)
\tilde{{\bm{u}}}(t)
is parameterized by a three-layer MLP with 128 hidden
units per layer and
tanh
\tanh
activations
(33,538 trainable parameters).
Spectral models replace the MLP with a Fourier feature map
𝚽
⁡
(
t
)
∈
ℝ
D
{\bm{\Phi}}(t)\in\mathbb{R}^{D}
followed by a linear head,
while keeping the same IC embedding and training objective:
𝒖
~
​
(
t
)
=
𝑾
​
𝚽
​
(
t
)
+
𝒃
,
𝑾
∈
ℝ
2
×
D
,
𝒃
∈
ℝ
2
.
\tilde{{\bm{u}}}(t)={\bm{W}}{\bm{\Phi}}(t)+{\bm{b}},\qquad{\bm{W}}\in\mathbb{R}^{2\times D},\ {\bm{b}}\in\mathbb{R}^{2}.
For both the fixed-frequency and adaptive-frequency Fourier models, we use
32 log-spaced frequencies (two bands: 16 in
[
0.5
,
5.0
]
[0.5,5.0]
and 16 in
[
5.0
,
15.0
]
[5.0,15.0]
), producing
D
=
64
D=64
Fourier features, since each frequency contributes both a
sin
⁡
(
ω
i
​
t
)
\sin(\omega_{i}t)
and a
cos
⁡
(
ω
i
​
t
)
\cos(\omega_{i}t)
term. The fixed Fourier spectral model contains 130 parameters, while the
adaptive Fourier spectral model contains 162 parameters, reflecting the
inclusion of learnable frequency parameters.
2.1
Gradient scaling induced by IC gating
Although the choice of
g
⁡
(
t
)
g(t)
does not change the underlying function class
satisfying the IC constraint, it directly affects optimization through
time-dependent Jacobian scaling. Under IC embedding with
g
⁡
(
t
)
g(t)
independent of
θ
\theta
,
𝒖
^
​
(
t
)
=
𝒖
0
+
g
⁡
(
t
)
​
𝒖
~
​
(
t
)
,
∂
𝒖
^
​
(
t
)
∂
θ
=
g
⁡
(
t
)
​
∂
𝒖
~
​
(
t
)
∂
θ
.
\hat{{\bm{u}}}(t)={\bm{u}}_{0}+g(t)\,\tilde{{\bm{u}}}(t),\qquad\frac{\partial\hat{{\bm{u}}}(t)}{\partial\theta}=g(t)\,\frac{\partial\tilde{{\bm{u}}}(t)}{\partial\theta}.
Thus, parameter sensitivities are scaled pointwise in physical time by
g
⁡
(
t
)
g(t)
,
inducing an implicit temporal reweighting of gradient propagation.
This effect can be formalized through the Neural Tangent Kernel (NTK)
framework applied to the physics residual loss. Let
R
θ
​
(
t
)
R_{\theta}(t)
denote the
residual vector and consider the squared residual objective
ℒ
phys
​
(
θ
)
=
1
2
​
∑
i
‖
R
θ
​
(
t
i
)
‖
2
.
\mathcal{L}_{\mathrm{phys}}(\theta)=\frac{1}{2}\sum_{i}\|R_{\theta}(t_{i})\|^{2}.
Define
e
i
:=
R
θ
​
(
t
i
)
e_{i}:=R_{\theta}(t_{i})
and linearize around initialization
θ
0
\theta_{0}
:
R
θ
​
(
t
)
≈
R
θ
0
​
(
t
)
+
J
R
​
(
t
)
​
(
θ
−
θ
0
)
,
J
R
​
(
t
)
=
∂
R
θ
​
(
t
)
∂
θ
|
θ
0
.
R_{\theta}(t)\approx R_{\theta_{0}}(t)+J_{R}(t)(\theta-\theta_{0}),\qquad J_{R}(t)=\left.\frac{\partial R_{\theta}(t)}{\partial\theta}\right|_{\theta_{0}}.
Under continuous-time gradient descent
d
​
θ
d
​
τ
=
−
∇
θ
ℒ
phys
,
\frac{d\theta}{d\tau}=-\nabla_{\theta}\mathcal{L}_{\mathrm{phys}},
we obtain, to first order,
∇
θ
ℒ
phys
≈
∑
i
J
R
(
t
i
)
⊤
e
i
,
d
​
e
i
d
​
τ
≈
J
R
(
t
i
)
d
​
θ
d
​
τ
=
−
∑
j
J
R
(
t
i
)
J
R
(
t
j
)
⊤
e
j
.
\nabla_{\theta}\mathcal{L}_{\mathrm{phys}}\approx\sum_{i}J_{R}(t_{i})^{\top}e_{i},\qquad\frac{de_{i}}{d\tau}\approx J_{R}(t_{i})\frac{d\theta}{d\tau}=-\sum_{j}J_{R}(t_{i})J_{R}(t_{j})^{\top}e_{j}.
Thus, the residual errors evolve under an NTK matrix
K
i
​
j
=
J
R
​
(
t
i
)
​
J
R
​
(
t
j
)
⊤
.
K_{ij}=J_{R}(t_{i})J_{R}(t_{j})^{\top}.
Because the residual depends on
𝒖
^
​
(
t
)
\hat{{\bm{u}}}(t)
and its time derivatives,
the residual Jacobian
J
R
​
(
t
)
J_{R}(t)
inherits multiplicative factors of
g
⁡
(
t
)
g(t)
(and, for derivative terms, also
g
′
​
(
t
)
g^{\prime}(t)
and
g
′′
​
(
t
)
g^{\prime\prime}(t)
).
A linear gate
g
⁡
(
t
)
=
t
g(t)=t
yields Jacobians that increase with time, emphasizing
later-time residuals. In contrast, the exponential gate
g
⁡
(
t
)
=
1
−
e
−
t
g(t)=1-e^{-t}
quickly saturates, producing a more uniform temporal weighting.
Consequently, the effective kernel is reweighted in a time-dependent manner,
altering how gradient descent distributes emphasis across the physical trajectory.
2.2
Training and Evaluation
The training objective combines the physics residual loss with a soft
initial-velocity penalty,
ℒ
=
λ
phys
​
ℒ
phys
+
λ
IC
​
ℒ
IC
,
vel
,
\mathcal{L}=\lambda_{\mathrm{phys}}\,\mathcal{L}_{\mathrm{phys}}+\lambda_{\mathrm{IC}}\,\mathcal{L}_{\mathrm{IC,vel}},
where
ℒ
phys
\mathcal{L}_{\mathrm{phys}}
is the mean-squared ODE residual at
collocation points and
ℒ
IC
,
vel
\mathcal{L}_{\mathrm{IC,vel}}
penalizes the induced
initial velocity. We set
λ
phys
=
1
\lambda_{\mathrm{phys}}=1
and vary
λ
IC
∈
{
0
,
50
}
\lambda_{\mathrm{IC}}\in\{0,50\}
.
All models are trained with Adam for 5,000 updates using a constant learning
rate of
10
−
3
10^{-3}
and no weight decay. Collocation points are resampled uniformly
at each iteration with
N
coll
=
2000
N_{\mathrm{coll}}=2000
interior points and
N
IC
=
20
N_{\mathrm{IC}}=20
initial-condition points.
Errors are evaluated on a fixed grid of
N
eval
=
2000
N_{\mathrm{eval}}=2000
points over
t
∈
[
0
,
T
]
t\in[0,T]
.
Performance is evaluated using the relative
L
2
L^{2}
error
(ReL2E) and the maximum absolute error (MaxAE).
Reference solutions are computed using
solve_ivp
(DOP853).
Let the wrapped angular difference and the instantaneous state error be defined as
Δ
​
θ
​
(
t
)
=
atan2
⁡
(
sin
⁡
(
θ
⁡
(
t
)
−
θ
ref
​
(
t
)
)
,
cos
⁡
(
θ
⁡
(
t
)
−
θ
ref
​
(
t
)
)
)
,
𝐞
⁡
(
t
)
=
[
r
​
(
t
)
−
r
ref
​
(
t
)
Δ
​
θ
​
(
t
)
]
.
\Delta\theta(t)=\operatorname{atan2}\!\big(\sin(\theta(t)-\theta_{\mathrm{ref}}(t)),\cos(\theta(t)-\theta_{\mathrm{ref}}(t))\big),\qquad\mathbf{e}(t)=\begin{bmatrix}r(t)-r_{\mathrm{ref}}(t)\\
\Delta\theta(t)\end{bmatrix}.
The relative
L
2
L^{2}
error over the trajectory and maximum absolute error are defined as
ReL2E
u
=
‖
𝐞
‖
L
2
‖
𝐮
ref
‖
L
2
,
‖
𝐞
‖
L
2
=
(
∫
0
T
‖
𝐞
⁡
(
t
)
‖
2
2
​
𝑑
t
)
1
/
2
,
MaxAE
u
=
max
t
∈
[
0
,
T
]
⁡
‖
𝐞
⁡
(
t
)
‖
2
.
\mathrm{ReL2E}_{u}=\frac{\|\mathbf{e}\|_{L^{2}}}{\|\mathbf{u}_{\mathrm{ref}}\|_{L^{2}}},\qquad\|\mathbf{e}\|_{L^{2}}=\left(\int_{0}^{T}\|\mathbf{e}(t)\|_{2}^{2}\,dt\right)^{1/2},\mathrm{MaxAE}_{u}=\max_{t\in[0,T]}\|\mathbf{e}(t)\|_{2}.
where
∥
⋅
∥
2
\|\cdot\|_{2}
denotes the Euclidean norm over state components and
∥
⋅
∥
L
2
\|\cdot\|_{L^{2}}
denotes the
L
2
L^{2}
norm over time.
Here the denominator normalizes by the
L
2
L^{2}
norm of the full reference trajectory
𝐮
ref
​
(
t
)
=
[
r
ref
​
(
t
)
,
θ
ref
​
(
t
)
]
⊤
\mathbf{u}_{\mathrm{ref}}(t)=[r_{\mathrm{ref}}(t),\theta_{\mathrm{ref}}(t)]^{\top}
.
As specified in figure captions, some runs use
20
20
seeds, with seeds in
[
0
,
19
]
[0,19]
. For 10 random seeds, seeds are in
[
0
,
9
]
[0,9]
. For
k
=
20
k=20
and
k
=
60
k=60
adaptive
20
20
seed runs, paired Wilcoxon signed-rank tests compare gates for each
(
k
,
metric
)
(k,\text{metric})
using shared random seeds. Holm–Bonferroni correction is applied to control family-wise error across tests. Error bars show mean
±
\pm
95% confidence intervals.
