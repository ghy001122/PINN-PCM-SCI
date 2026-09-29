"""Verbatim accepted_lbfgs from phk_v23_lf11_coverage; Torch BSD-3-Clause.

No separate project-wide distribution license is asserted here. The executed
source copy, including its earlier header, is retained in the run archive.
"""
import copy
import torch

def accepted_lbfgs(parameters, objective, remaining, *, optimizer_state=None,
                   report=None, charge=None, resource_check=None):
    """Historical continued_lbfgs recipe plus durable accepted-state hooks.

    The strong-Wolfe recipe and acceptance checks are unchanged. All exceptions
    restore parameters AND optimizer history before returning control to caller.
    PyTorch LBFGS is BSD-3-Clause; the wrapper derives from phk_v23_lf11_v_continue.
    """
    parameters = list(parameters)
    opt = torch.optim.LBFGS(parameters, lr=1., max_iter=1, max_eval=32,
        tolerance_grad=1e-10, tolerance_change=1e-14, history_size=50, line_search_fn='strong_wolfe')
    if optimizer_state is not None: opt.load_state_dict(copy.deepcopy(optimizer_state))
    used = accepted = 0
    terminal = 'EVALUATION_BUDGET_EXHAUSTED'
    last_loss = initial_loss = None
    def flat(items): return torch.cat([p.detach().reshape(-1) for p in items])
    class Limit(Exception): pass
    while used < remaining:
        if resource_check: resource_check()
        snapshot = [p.detach().clone() for p in parameters]
        old_opt = copy.deepcopy(opt.state_dict())
        evaluations = []
        def closure():
            nonlocal used, initial_loss
            if used >= remaining: raise Limit()
            if resource_check: resource_check()
            used += 1
            if charge: charge()
            opt.zero_grad(set_to_none=True)
            loss = objective()
            gradient = flat([p.grad if p.grad is not None else torch.zeros_like(p) for p in parameters])
            if not torch.isfinite(loss) or not torch.isfinite(gradient).all():
                raise FloatingPointError('nonfinite complete objective or gradient')
            if initial_loss is None: initial_loss=float(loss.detach())
            evaluations.append((flat(parameters).clone(),float(loss.detach()),gradient.clone()))
            return loss
        def restore():
            with torch.no_grad():
                for p, old in zip(parameters,snapshot): p.copy_(old)
            opt.load_state_dict(old_opt)
            opt.zero_grad(set_to_none=True)
        try:
            opt.step(closure)
        except Limit:
            restore(); terminal='EVALUATION_BUDGET_EXHAUSTED_TRIAL_ROLLED_BACK'; break
        except BaseException:
            restore()
            if report: report(dict(event='interrupted',evaluations=used,accepted_steps=accepted), opt)
            raise
        current=flat(parameters)
        matches=[x for x in evaluations if torch.equal(x[0],current)]
        if not matches:
            restore(); raise RuntimeError('accepted parameters lack evaluated objective')
        _,new_loss,gradient=matches[-1]
        start,start_loss,start_grad=evaluations[0]
        state=opt.state[parameters[0]]
        if torch.equal(start,current):
            terminal='GRADIENT_CONVERGED' if float(gradient.abs().max())<=1e-10 else 'NO_ACCEPTED_PROGRESS'
            last_loss=new_loss; break
        direction,step=state['d'],float(state['t']);gtd=float(start_grad@direction)
        if not (new_loss<=start_loss+1e-4*step*gtd+1e-15 and abs(float(gradient@direction))<=-.9*gtd+1e-15):
            restore(); terminal='LINE_SEARCH_FAILED_WOLFE_TRIAL_ROLLED_BACK'; break
        accepted+=1;last_loss=new_loss
        if report: report(dict(event='accepted',evaluations=used,accepted_steps=accepted,
                              loss=new_loss,gradient_max=float(gradient.abs().max()),wolfe_verified=True),opt)
        if float(gradient.abs().max())<=1e-10:
            terminal='GRADIENT_CONVERGED';break
    return dict(evaluations=used,accepted_steps=accepted,termination=terminal,
                last_accepted_loss=last_loss if last_loss is not None else initial_loss),opt
