# Neuro-Spectral Architectures for Causal Physics-Informed Networks

paper_id: arxiv:2509.04966v2
tier: H
source_used: html_arxiv
warning: none

## Intro

The introduction of Physics-Informed Neural Networks (PINNs)
[
50
]
has sparked interest in using neural networks to solve partial differential equations (PDEs)
[
31
,
67
,
73
]
.
PINNs enable data-efficient modeling of complex systems by embedding physical laws directly into the loss landscape. This approach has opened new possibilities in scientific computing, with applications spanning a wide range of subjects, including fluid dynamics and climate modeling
[
21
,
38
]
, biomedical simulations
[
11
,
26
]
, material science
[
53
,
72
,
74
]
, and others
[
18
,
25
,
37
,
45
,
51
]
.
We consider the following initial-boundary value problem for
t
∈
[
0
,
T
]
t\in[0,T]
and
𝐱
∈
Ω
⊂
ℝ
d
\mathbf{x}\in\Omega\subset\mathbb{R}^{d}
:
d
d
​
t
𝐮
(
t
,
𝐱
)
=
𝐅
(
t
,
𝐱
,
𝐮
,
∇
𝐮
,
∇
∇
𝐮
)
,
𝐮
(
0
,
𝐱
)
=
𝐮
0
(
𝐱
)
\frac{d}{dt}\mathbf{u}(t,\mathbf{x})=\mathbf{F}\left(t,\mathbf{x},\mathbf{u},\nabla\mathbf{u},\nabla\nabla\mathbf{u}\right)\,,\quad\mathbf{u}(0,\mathbf{x})=\mathbf{u}_{0}(\mathbf{x})\,
(1)
where
𝐮
:
[
0
,
T
]
×
Ω
→
ℝ
n
\mathbf{u}:[0,T]\times\Omega\to\mathbb{R}^{n}
denotes the (vector-valued) solution,
∇
𝐮
\nabla\mathbf{u}
and
∇
∇
𝐮
\nabla\nabla\mathbf{u}
denote its first- and second-order spatial derivatives, and
𝐅
\mathbf{F}
is a smooth function.
𝐮
0
​
(
𝐱
)
\mathbf{u}_{0}(\mathbf{x})
is the initial condition (Cauchy data), and we assume some boundary conditions are imposed on
∂
Ω
\partial\Omega
.
PINNs consist of
θ
\theta
-parametrized coordinate networks
𝐮
θ
:
[
0
,
T
]
×
Ω
↦
ℝ
n
\mathbf{u}_{\theta}:[0,T]\times\Omega\mapsto\mathbb{R}^{n}
, trained to approximate the solution
𝐮
\mathbf{u}
by minimizing a composite
physics-informed
loss function
ℒ
⁡
(
θ
)
\mathcal{L}(\theta)
. This loss typically includes terms for the PDE as well as for the initial/boundary data, e.g.,
ℒ
PDE
(
θ
)
=
‖
d
d
​
t
𝐮
θ
(
t
,
𝐱
)
−
𝐅
(
t
,
𝐱
,
𝐮
θ
,
∇
𝐮
θ
,
∇
∇
𝐮
θ
)
‖
2
2
,
ℒ
IC
(
θ
)
=
λ
IC
‖
𝐮
θ
(
0
,
𝐱
)
−
𝐮
0
(
𝐱
)
‖
2
2
,
\mathcal{L}_{\text{PDE}}(\theta)\!=\!\left\lVert\frac{d}{dt}\mathbf{u}_{\theta}(t,\mathbf{x})\!-\!\mathbf{F}\left(t,\mathbf{x},\mathbf{u}_{\theta},\nabla\mathbf{u}_{\theta},\nabla\nabla\mathbf{u}_{\theta}\right)\right\rVert_{2}^{2}\,,\;\;\mathcal{L}_{\text{IC}}(\theta)\!=\!\lambda_{\text{IC}}\left\|\mathbf{u}_{\theta}(0,\mathbf{x})\!-\!\mathbf{u}_{0}(\mathbf{x})\right\|_{2}^{2}\,,
(2)
where
∥
⋅
∥
2
\|\cdot\|_{2}
denotes the regular norm in
L
2
​
(
[
0
,
T
]
×
Ω
)
L^{2}([0,T]\times\Omega)
, and
λ
IC
\lambda_{\text{IC}}
is the weight for the associated residue term (a term
ℒ
BC
\mathcal{L}_{\text{BC}}
representing boundary conditions could be also included).
PINNs thus provide a flexible,
data-driven
, and
meshless
framework for approximating PDE solutions using neural networks.
Data-Driven
. As neural networks, PINNs are particularly suited for handling heterogeneous, noisy, or incomplete measurement data, which can be efficiently combined with physical priors via physics-informed losses
[
37
,
45
,
62
,
70
,
71
]
.
Mesh-Independence
. As coordinate networks, PINNs represent continuous interpolations of the underlying solutions and may be evaluated at arbitrary spatial or temporal coordinates. In higher-dimensional problems, this property can be combined with random sampling strategies to substantially reduce the number of samples needed to approximate the solution
[
66
,
67
]
.
Figure 1
:
We present
NeuSA
, a theoretically grounded Physics-informed neural architecture.
On the left, we compare various models on a wave propagation problem. The dashed lines represent the discontinuities of a stratified heterogeneous medium.
NeuSA
achieves the lowest relative error (rMSE) and most accurately preserves sharp wavefronts and reflections. On the right, we show the evolution of the relative L2 error during training.
NeuSA
converges more rapidly and consistently.
However, standard PINNs often struggle to enforce fundamental structural aspects of the underlying solutions. In most cases, they rely on general-purpose feed-forward architectures, such as the standard Multi-Layer Perceptron (MLP)
[
17
]
, or on specialized MLP-based variants that enhance expressivity through activation-function modifications, including QRes
[
10
]
, FLS
[
65
]
.
This generic structure design often leads to issues related to
spectral bias
,
causality
and limited
generalization capacity
:
Spectral Bias
. Regular coordinate networks based on sigmoid or rectifier activations often struggle to represent high-frequency components,
leading to issues with representing detailed and/or multi-scale solutions
[
64
,
69
]
.
This effect is often mitigated with Fourier-Feature (FF) layers, sinusoidal encoder layers designed to inject high-frequency representations into a network’s architecture
[
57
]
. Still, FF layers require fine-tuning to avoid overfitting and noise.
Causality
. PINNs are notorious for violating causality and temporal consistency due to their simultaneous training over the entire time domain
[
62
]
. These issues may manifest in the form of incorrect initial conditions or non-physical convergence to trivial solutions. Attempts have also been made to minimize these effects with modified losses
[
62
,
71
]
.
Generalization Capacity
. MLP-based PINNs may struggle with extrapolation beyond their training domain
[
68
,
75
]
, which has been tackled with alternative training strategies
[
29
]
.
Due to these issues, PINNs often fail to converge to the true solution when solving complex time-dependent problems. Instead, they may overfit and converge to trivial equilibrium solutions. Such shortcomings are common when solving problems with strong time dependence, as evidenced by their relative lack of success when applied to linear and nonlinear wave equations
[
18
,
20
,
39
]
. This stands in stark contrast to PINNs’ capacity for solving parabolic and elliptic equations
[
56
]
.
We propose
NeuSA
a new family of
Neu
ro-
S
pectral
A
rchitectures designed for solving space-inhomogeneous and/or nonlinear time-dependent PDEs.
NeuSA
uses the spectral decomposition to obtain a method-of-lines
[
32
,
54
]
discretization of a PDE into a large system of ODEs, which is then modeled using a Neural ODE (NODE)
[
14
]
(see
Figure 2
).
Figure 1
showcases
NeuSA
’s results on a 2D wave propagation task, demonstrating significant improvements over prior methods in accuracy, speed, and temporal consistency. Our contributions may be summarized as follows.
•
Causality.
NeuSA
is a spectral-method-based architecture for neural PDEs, such as
[
22
]
. Consequently, it inherits the causal structure of classical methods, including exact initial conditions and uniqueness, while retaining a data-friendly, mesh-less representation.
•
Spectral fidelity.
The choice of global spectral bases allows
NeuSA
to overcome the spectral bias commonly attributed to MLP-PINNs, offering a theoretically-motivated alternative to Fourier-Feature Networks.
•
Analytical initialization.
The interpretable structure of
NeuSA
as a neural extension of spectral methods enables specialized initialization schemes in which networks are initialized as the solution of closely related linear homogeneous problems, at no training cost.
•
Time-extrapolation.
Due to its causal formulation,
NeuSA
displays strong time-extrapolating performance, enabling simulation beyond training intervals.
Figure 2
:
Neuro-Spectral Architecture. Above: The spectral coefficients for the initial conditions
𝐮
^
​
(
0
)
\hat{\mathbf{u}}(0)
, flowing according to a NODE. Below: The spatial input
𝐱
\mathbf{x}
being encoded into the spectral basis functions
𝐛
⁡
(
𝐱
)
\mathbf{b}(\mathbf{x})
. Coefficients and bases are then combined to yield the final result.
1.1
Related work
Several works have explored designs for physics-informed neural machine learning, including a large body of literature on operator learning
[
15
,
75
]
. Multiple recent works on Physics-Informed Networks propose alternative architectures for representing solutions, enhancing their expressiveness, spectral representation, or temporal coherence.
Quadratic Residual networks (
QRes
)
[
10
]
introduce a class of parameter-efficient neural networks by incorporating a quadratic term into the weighted sum of inputs before applying the activation functions at each layer of the network.
This modification enables QRes to approximate polynomials using shallower networks, resulting in compact yet expressive models.
First-Layer Sine (
FLS
)
[
65
]
, also referred to as sf-PINN, introduces sinusoidal encoding layers within the PINN framework. FLS nets utilize sinusoidal encoding layers, in an approach closely analogous to that of Fourier-feature networks, to mitigate spectral bias and enhance input gradient distribution.
PINNsFormer
[
73
]
adapts the transformer architecture to the PINN setting, leveraging attention mechanisms to model temporal dependencies among state tokens, with the goal of achieving enhanced temporal consistency.
Neural Ordinary Differential Equations (
NODEs
)
[
14
]
are a class of ‘continuous-depth’ residual networks that model inference as the integration of a continuous-time process, effectively solving an ODE whose dynamics are parameterized by a neural network.
NODEs have proven powerful for modeling continuous-time dynamics and have been applied to physics-informed learning, generative modeling, time-series forecasting, and morphing
[
7
,
34
,
35
,
41
,
59
,
5
]
. However, their highly sequential numerical structure makes them equivalent to ultra-deep residual networks, which can significantly slow down training. As a result, their application to PDEs remains relatively underexplored
[
60
]
.

## Method

Neuro-Spectral architectures are defined as models that employ spectral decomposition to reduce a PDE defined over an infinite-dimensional space to an ODE system in finite dimensions, subsequently training a NODE to approximate the latter using a physics-informed loss.
This formulation interprets (
1
) as an abstract Cauchy problem over the Hilbert space
L
2
​
(
Ω
)
n
L^{2}(\Omega)^{n}
, treating the solution
𝐮
⁡
(
t
,
⋅
)
\mathbf{u}(t,\cdot)
as a time-parametrized family
𝐮
:
ℝ
→
L
2
​
(
Ω
)
n
\mathbf{u}:\mathbb{R}\to L^{2}(\Omega)^{n}
. The spectral decomposition
[
8
,
13
,
58
]
consists of approximating
𝐮
⁡
(
𝐱
,
t
)
\mathbf{u}(\mathbf{x},t)
by its projection onto the subspace spanned by a finite subset
𝐛
⁡
(
𝐱
)
\mathbf{b}(\mathbf{x})
of an orthonormal basis of
L
2
​
(
Ω
)
n
L^{2}(\Omega)^{n}
.
Given a truncated spectral representation with harmonics
c
1
,
c
2
,
…
,
c
d
c_{1},c_{2},\dots,c_{d}
, the solution
𝐮
\mathbf{u}
can be expressed in terms of an expansion over elements of the basis tensor
𝐛
⁡
(
𝐱
)
:
Ω
→
ℂ
c
1
×
⋯
×
c
d
\mathbf{b}(\mathbf{x}):\Omega\to\mathbb{C}^{c_{1}\times\dots\times c_{d}}
, whose coefficients form a tensor
𝐮
^
​
(
t
)
:
[
0
,
T
]
→
ℂ
c
1
×
⋯
×
c
d
×
n
\hat{\mathbf{u}}(t):[0,T]\to\mathbb{C}^{c_{1}\times\dots\times c_{d}\times n}
, leading to
𝐮
⁡
(
t
,
𝐱
)
=
∑
k
𝐮
^
k
​
(
t
)
​
𝐛
k
​
(
𝐱
)
,
𝐮
^
k
​
(
t
)
=
∫
Ω
𝐮
⁡
(
t
,
𝐱
)
​
𝐛
k
​
(
𝐱
)
​
𝑑
𝐱
.
\mathbf{u}(t,\mathbf{x})=\sum_{k}\hat{\mathbf{u}}_{k}(t)\mathbf{b}_{k}(\mathbf{x}),\quad\hat{\mathbf{u}}_{k}(t)=\int_{\Omega}\mathbf{u}(t,\mathbf{x})\mathbf{b}_{k}(\mathbf{x})d\mathbf{x}.
(3)
Where
k
k
denotes a
d
d
-dimensional multi-index,
𝐮
^
k
​
(
t
)
:
[
0
,
T
]
→
ℝ
n
\hat{\mathbf{u}}_{k}(t):[0,T]\to\mathbb{R}^{n}
and
𝐛
k
​
(
𝐱
)
:
Ω
→
ℝ
\mathbf{b}_{k}(\mathbf{x}):\Omega\to\mathbb{R}
represent the
k
−
k-
th indexed element in
𝐮
^
\hat{\mathbf{u}}
and
𝐛
\mathbf{b}
, respectively.
Substituting (
3
) into (
1
) leads to a method-of-lines
[
32
,
54
]
discretization, resulting in an
ordinary
differential equation for the coefficients:
d
d
​
t
​
𝐮
^
=
𝐅
^
​
(
𝐮
^
)
,
\frac{d}{dt}\hat{\mathbf{u}}=\hat{\mathbf{F}}(\hat{\mathbf{u}}),
(4)
where
𝐅
^
:
ℂ
c
1
×
⋯
×
c
d
×
n
→
ℂ
c
1
×
⋯
×
c
d
×
n
\hat{\mathbf{F}}:\mathbb{C}^{c_{1}\times\dots\times c_{d}\times n}\to\mathbb{C}^{c_{1}\times\dots\times c_{d}\times n}
usually does not admit a simple closed-form expression for a general basis
𝐛
\mathbf{b}
.
Instead of deriving it explicitly, we learn
𝐅
^
\hat{\mathbf{F}}
as a parameterized network
𝐅
^
θ
\widehat{\mathbf{F}}_{\theta}
.
Inference in a Neuro-Spectral model then proceeds as follows (see
Figure 3
and
[
4
]
):
1. Project the initial conditions onto an orthonormal basis.
Sample the initial conditions
𝐮
⁡
(
0
,
𝐱
)
\mathbf{u}(0,\mathbf{x})
densely and extract their spectral representation
𝐮
^
\hat{\mathbf{u}}
in terms of the basis
𝐛
\mathbf{b}
:
𝐮
⁡
(
0
,
𝐱
)
=
∑
k
𝐮
^
k
​
(
0
)
​
𝐛
k
​
(
𝐱
)
.
\mathbf{u}(0,\mathbf{x})=\sum_{k}\hat{\mathbf{u}}_{k}(0)\mathbf{b}_{k}(\mathbf{x}).
2. Integrate coefficients in time according to a NODE.
Use the coefficients tensor
𝐮
^
\hat{\mathbf{u}}
as input to a NODE with vector field
𝐅
^
θ
\hat{\mathbf{F}}_{\theta}
and integrate it with a high-order method:
𝐮
^
θ
​
(
t
)
=
𝐮
^
​
(
0
)
+
∫
0
t
𝐅
^
θ
​
(
𝐮
^
​
(
τ
)
)
​
𝑑
τ
.
\hat{\mathbf{u}}_{\theta}(t)\!=\!\hat{\mathbf{u}}(0)\!+\!\int_{0}^{t}\hat{\mathbf{F}}_{\theta}\big(\hat{\mathbf{u}}(\tau)\big)d\tau.
3. Reconstruct the solution and perform training.
Multiply the obtained coefficients
𝐮
^
θ
,
k
​
(
t
)
\hat{\mathbf{u}}_{\theta,k}(t)
by their corresponding basis functions
𝐛
k
​
(
𝐱
)
\mathbf{b}_{k}(\mathbf{x})
to obtain
𝐮
⁡
(
t
,
𝐱
)
\mathbf{u}(t,\mathbf{x})
. This representation can be differentiated analytically to compute physics-informed losses:
𝐮
θ
​
(
t
,
𝐱
)
=
∑
k
𝐮
^
θ
,
k
​
(
t
)
​
𝐛
k
​
(
𝐱
)
.
\mathbf{u}_{\theta}(t,\mathbf{x})=\sum_{k}\hat{\mathbf{u}}_{\theta,k}(t)\mathbf{b}_{k}(\mathbf{x}).
Figure 3
:
Inference in a Neuro-Spectral model. The initial conditions are decomposed into their spectral coefficients, which are propagated in time via a NODE. The time-iterated coefficients are then reconstructed into the solution at later times.
2.1
Spectral decomposition and initialization
The choice of the basis
𝐛
\mathbf{b}
can enforce specific properties of the solution, as well as ensure the fulfillment of the given boundary conditions.
In this work, we initialize
𝐛
\mathbf{b}
as the Fourier basis and its odd and even extensions in terms of the sine and cosine functions.
This choice enables the representation of homogeneous periodic, Dirichlet, and Neumann boundary conditions for rectangular domains.
The spectral projection
𝐮
^
\hat{\mathbf{u}}
can then be computed in several ways, depending on how the spatial domain is sampled (see
Appendix B
).
We adopt the Fourier basis for two main reasons: first, to overcome spectral bias, inspired by the success of Fourier-Feature layers; and second, to allow for the simple and accurate representation of linear translation-invariant (LTI) differential operators as scalar multipliers
[
23
]
.
We use the latter to implement an improved initialization scheme for the NODE, described as follows.
1. Linearize the PDE.
Extract a linear translation-invariant approximation for
𝐅
\mathbf{F}
:
d
d
​
t
𝐮
≈
𝐅
linear
(
𝐮
,
∇
𝐮
,
∇
∇
𝐮
,
…
)
:=
a
0
𝐮
+
∑
i
a
1
​
i
d
d
​
𝐱
i
𝐮
+
∑
i
,
j
a
2
​
i
​
j
d
2
d
​
𝐱
i
​
d
​
𝐱
j
𝐮
+
⋯
.
\frac{d}{dt}\mathbf{u}\approx\mathbf{F}_{\text{linear}}(\mathbf{u},\nabla\mathbf{u},\nabla\nabla\mathbf{u},\dots):=a_{0}\mathbf{u}+\sum_{i}a_{1i}\frac{d}{d\mathbf{x}_{i}}\mathbf{u}+\sum_{i,j}a_{2ij}\frac{d^{2}}{d\mathbf{x}_{i}d\mathbf{x}_{j}}\mathbf{u}+\cdots\,.
(5)
2. Fourier multiplier.
Derive the associated Fourier multiplier
M
∈
ℂ
c
1
×
c
2
×
⋯
×
c
d
×
n
M\in\mathbb{C}^{c_{1}\times c_{2}\times\dots\times c_{d}\times n}
, defined as an element-wise polynomial on the
k
k
-th Fourier frequency corresponding to the
k
k
-th harmonic:
d
d
​
t
​
𝐮
≈
𝐅
linear
⟹
d
d
​
t
​
𝐮
^
≈
M
⊙
𝐮
^
,
\frac{d}{dt}\mathbf{u}\approx\mathbf{F}_{\text{linear}}\implies\frac{d}{dt}\hat{\mathbf{u}}\approx M\odot\hat{\mathbf{u}}\,,
(6)
where
⊙
\odot
stands for the Hadamard (element-wise) product.
3. Initialize the vector field
𝐅
^
θ
\hat{\mathbf{F}}_{\theta}
.
Initialize NODE near this approximate linear solution by augmenting the learned vector field with the analytical multiplier:
𝐅
^
θ
​
(
𝐮
^
)
=
(
M
⊙
𝐮
^
)
+
ϵ
​
ℱ
θ
​
(
𝐮
^
)
,
\hat{\mathbf{F}}_{\theta}(\hat{\mathbf{u}})=(M\odot\hat{\mathbf{u}})+\epsilon\mathcal{F}_{\theta}(\hat{\mathbf{u}})\,,
(7)
where
ℱ
θ
​
(
𝐮
^
)
\mathcal{F}_{\theta}(\hat{\mathbf{u}})
is a neural network initialized with mean zero and unit variance, and
ϵ
\epsilon
is a small parameter.
In this way, the network starts close to the solution of the associated LTI problem, serving as a strong prior for training. During optimization,
ℱ
θ
\mathcal{F}_{\theta}
learns a compact representation for the non-linear and/or non-translation-invariant dynamics, effectively leading to a neural generalization of the classical spectral method. See Section
3
for explicit examples, and Appendix
B.2
for the detailed architecture of
ℱ
θ
\mathcal{F}_{\theta}
.
2.2
Neural ODE, time integration and causality
As discussed, neuro-spectral models rely on a NODE to propagate the spectral coefficients forward in time. The vector field to be integrated over as part of inference is composed of the near-analytical initialization discussed above along with a multilayer perceptron
ℱ
θ
\mathcal{F}_{\theta}
:
d
d
​
t
​
𝐮
^
=
𝐅
^
θ
​
(
𝐮
^
)
=
M
⊙
𝐮
^
+
ϵ
​
ℱ
θ
​
(
𝐮
^
)
.
\displaystyle\frac{d}{dt}\hat{\mathbf{u}}=\hat{\mathbf{F}}_{\theta}(\hat{\mathbf{u}})=M\odot\hat{\mathbf{u}}+\epsilon\mathcal{F}_{\theta}(\hat{\mathbf{u}}).
(8)
The NODE receives as input a tensor of size
1
×
c
1
×
c
2
×
⋯
×
c
d
×
n
1\times c_{1}\times c_{2}\times\dots\times c_{d}\times n
, corresponding to the first time-slice of the solution, and outputs
t
samples
t_{\text{samples}}
slices in the form of a tensor of shape
t
samples
×
c
1
×
c
2
×
⋯
×
c
d
×
n
t_{\text{samples}}\times c_{1}\times c_{2}\times\dots\times c_{d}\times n
.
This special treatment of the time dimension, characterized by the sequential nature of integration, is what equips NeuSA with causal structure. In fact, it is possible to prove NeuSAs are
flows
[
6
,
61
]
, as summarized in the following theorem:
Theorem 1
.
For band-limited initial conditions
𝐮
0
\mathbf{u}_{0}
and globally Lipschitz neural vector fields
𝐅
^
θ
\hat{\mathbf{F}}_{\theta}
, the orbits created by
NeuSA
satisfy the initial conditions and uniqueness:
1.
fulfillment of initial conditions:
𝐮
θ
​
(
0
,
𝐱
)
=
𝐮
⁡
(
0
,
𝐱
)
;
\mathbf{u}_{\theta}(0,\mathbf{x})=\mathbf{u}(0,\mathbf{x});
2.
uniqueness:
𝐮
θ
1
​
(
0
,
⋅
)
≠
𝐮
θ
2
​
(
0
,
⋅
)
⟹
𝐮
θ
1
​
(
t
,
⋅
)
≠
𝐮
θ
2
​
(
t
,
⋅
)
∀
t
∈
[
0
,
T
]
.
\mathbf{u}^{1}_{\theta}(0,\cdot)\neq\mathbf{u}^{2}_{\theta}(0,\cdot)\implies\mathbf{u}^{1}_{\theta}(t,\cdot)\neq\mathbf{u}^{2}_{\theta}(t,\cdot)\quad\forall t\in[0,T].
A more detailed exposition of this theorem as well as its proof may be found in
Appendix A
.
It is, in essence, a result of the properties of flow operators for ODEs combined with the uniqueness of the spectral decomposition for band-limited functions. This holds
by construction
, regardless of training.
2.3
Losses and training
Training
NeuSA
is similar to training a common MLP-PINN. The main difference is that we can no longer differentiate directly with respect to time, as it is no longer an input coordinate; it is instead implicitly encoded as the time-steps for the NODE iteration. Nevertheless, time and space derivatives may be calculated in a straightforward manner:
d
d
​
t
​
𝐮
θ
​
(
t
,
𝐱
)
=
∑
k
𝐅
^
θ
​
(
𝐮
^
θ
)
k
​
(
t
)
​
𝐛
k
​
(
𝐱
)
,
d
d
​
𝐱
i
​
𝐮
θ
​
(
t
,
𝐱
)
=
∑
k
𝐮
^
θ
,
k
​
(
t
)
​
d
d
​
𝐱
i
​
𝐛
k
​
(
𝐱
)
,
\frac{d}{dt}\mathbf{u}_{\theta}(t,\mathbf{x})=\sum_{k}\hat{\mathbf{F}}_{\theta}(\hat{\mathbf{u}}_{\theta})_{k}(t)\mathbf{b}_{k}(\mathbf{x}),\quad\frac{d}{d\mathbf{x}_{i}}\mathbf{u}_{\theta}(t,\mathbf{x})=\sum_{k}\hat{\mathbf{u}}_{\theta,k}(t)\frac{d}{d\mathbf{x}_{i}}{\mathbf{b}}_{k}(\mathbf{x})\,,
(9)
where by construction
𝐅
^
θ
​
(
𝐮
^
θ
)
k
​
(
t
)
=
d
d
​
t
​
𝐮
^
θ
,
k
​
(
t
)
\hat{\mathbf{F}}_{\theta}(\hat{\mathbf{u}}_{\theta})_{k}(t)=\frac{d}{dt}\hat{\mathbf{u}}_{\theta,k}(t)
.
Note that the cost of calculating derivatives does not increase meaningfully for higher-order spatial derivatives, as opposed to the exponential increase in computational cost incurred by naively stacking derivatives with autograd
[
43
]
.
We may then sample the domain
Ω
\Omega
and evaluate the associated Physics-Informed residue with
ℒ
PDE
​
(
θ
)
\displaystyle\mathcal{L}_{\text{PDE}}(\theta)
=
∑
t
i
∈
[
0
,
T
]
∑
𝐱
j
∈
Ω
‖
d
d
​
t
𝐮
θ
(
t
i
,
𝐱
j
)
−
𝐅
(
t
i
,
𝐱
j
,
𝐮
θ
,
∇
𝐮
θ
,
∇
∇
𝐮
θ
)
‖
2
2
,
\displaystyle=\sum_{t_{i}\in[0,T]}\sum_{\mathbf{x}_{j}\in\Omega}\left\lVert\frac{d}{dt}\mathbf{u}_{\theta}(t_{i},\mathbf{x}_{j})-\mathbf{F}(t_{i},\mathbf{x}_{j},\mathbf{u}_{\theta},\nabla\mathbf{u}_{\theta},\nabla\nabla\mathbf{u}_{\theta})\right\rVert_{2}^{2}\,,
(10)
where
t
i
t_{i}
denotes the
i
i
-th integration time step for the NODE and
𝐱
j
\mathbf{x}_{j}
denotes the coordinates at the
j
j
-th spatial sample point. Note that NeuSA automatically complies with initial and boundary conditions and therefore does not require loss terms for them.
Note that neither time nor space samples need to be uniformly distributed; nevertheless, space samples must remain constant across all times for each pass, as opposed to conventional PINNs. This comes at the advantage that a
single
forward pass is necessary to evaluate the loss over all samples, as opposed to the multiple passes needed for common PINNs. This will allow NeuSA architectures to achieve training speeds comparable to those of purely neural approaches, despite their reliance on computationally intensive NODE integration.
