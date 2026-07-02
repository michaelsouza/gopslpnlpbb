#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  3 11:07:46 2020

@author: Sophie Demassey, Gratien Bonvin
"""

import gurobipy as gp
from gurobipy import GRB
import outerapproximation as oa
from instance import Instance
import datetime as dt
from activation import (
    ActivationConfig,
    public_gops_start_limit_config,
)


# !!! check round values
# noinspection PyArgumentList
def build_model(inst: Instance, epsilon: float, pumpvals=None, activation_config: ActivationConfig | None = None):
    """Build the convex relaxation gurobi model."""

    activation_config = activation_config or public_gops_start_limit_config()
    milp = gp.Model('Pumping_Scheduling')

    qvar = {}  # arc flow
    svar = {}  # pump/valve activity status
    ivar = {}  # pump ignition status
    stopvar = {}  # pump stop status
    hvar = {}  # node head

    nperiods = inst.nperiods()
    horizon = inst.horizon()

    for t in horizon:
        for (i, j), pipe in inst.pipes.items():
            qvar[(i, j), t] = milp.addVar(lb=pipe.qmin, ub=pipe.qmax, name=f'qp({i},{j},{t})')

        for (i, j), valve in inst.valves.items():
            qvar[(i, j), t] = milp.addVar(lb=valve.qmin, ub=valve.qmax, name=f'qv({i},{j},{t})')
            svar[(i, j), t] = milp.addVar(vtype=GRB.BINARY, name=f'xv({i},{j},{t})')

        for (i, j), pump in inst.pumps.items():
            ivar[(i, j), t] = milp.addVar(vtype=GRB.BINARY, name=f'ik({i},{j},{t})')
            drawcost = 3.6 * inst.tsinhours() * inst.reservoirs[i].drawcost if i in inst.reservoirs else 0
            qvar[(i, j), t] = milp.addVar(lb=0, ub=pump.qmax, obj=drawcost + inst.eleccost(t) * pump.power[1],
                                          name=f'qk({i},{j},{t})')
            svar[(i, j), t] = milp.addVar(obj=inst.eleccost(t) * pump.power[0], vtype=GRB.BINARY,
                                          name=f'xk({i},{j},{t})')

        for j in inst.junctions:
            hvar[j, t] = milp.addVar(name=f'hj({j},{t})')

        for j, res in inst.reservoirs.items():
            hvar[j, t] = milp.addVar(lb=res.head(t), ub=res.head(t), name=f'hr({j},{t})')

        for j, tank in inst.tanks.items():
            hvar[j, t] = milp.addVar(lb=tank.head(tank.vmin), ub=tank.head(tank.vmax), name=f'ht({j},{t})')

    for j, tank in inst.tanks.items():
        hvar[j, nperiods] = milp.addVar(lb=tank.head(tank.vinit), ub=tank.head(tank.vmax), name=f'ht({j},T)')
        hvar[j, 0].lb = tank.head(tank.vinit)
        hvar[j, 0].ub = tank.head(tank.vinit)
    milp.update()

    # FLOW CONSERVATION (JUNCTIONS)
    for j, junc in inst.junctions.items():
        for t in horizon:
            # !!! original code: round(demand,2)
            milp.addConstr(gp.quicksum(qvar[a, t] for a in inst.inarcs(j))
                           - gp.quicksum(qvar[a, t] for a in inst.outarcs(j)) == junc.demand(t), name=f'fc({j},{t})')

    # FLOW CONSERVATION (TANKS)
    for j, tank in inst.tanks.items():
        for t in horizon:
            milp.addConstr(hvar[j, t + 1] - hvar[j, t] == 3.6 * inst.tsinhours() / tank.surface *
                           (gp.quicksum(qvar[a, t] for a in inst.inarcs(j))
                            - gp.quicksum(qvar[a, t] for a in inst.outarcs(j))), name=f'fc({j},{t})')

    # MAX WITHDRAWAL AT RESERVOIRS
    for j, res in inst.reservoirs.items():
        if res.drawmax:
            milp.addConstr(3.6 * inst.tsinhours()
                           * gp.quicksum(qvar[a, t] for a in inst.outarcs(j) for t in horizon)
                           <= res.drawmax, name=f'w({j})')

    # VALVES
    for (i, j), valve in inst.valves.items():
        if valve.type == 'GV' or valve.type == 'PRV':
            for t in horizon:
                x = svar[(i, j), t] if (valve.type == 'GV') else (1 - svar[(i, j), t])
                milp.addConstr(qvar[(i, j), t] <= valve.qmax * svar[(i, j), t], name=f'vu({i},{j},{t})')
                milp.addConstr(qvar[(i, j), t] >= valve.qmin * x, name=f'vl({i},{j},{t})')
                milp.addConstr(hvar[i, t] - hvar[j, t] >= valve.hlossmin * (1 - svar[(i, j), t]),
                               name=f'hvl({i},{j},{t})')
                milp.addConstr(hvar[i, t] - hvar[j, t] <= valve.hlossmax * (1 - x), name=f'hvu({i},{j},{t})')

    # CONVEXIFICATION OF HEAD-FLOW (PIPES)
    for (i, j), pipe in inst.pipes.items():
        coeff = [pipe.hloss[2], pipe.hloss[1]]
        cutbelow, cutabove = oa.pipecuts(pipe.qmin, pipe.qmax, coeff, (i, j), epsilon, drawgraph=False)
        # print(f'{pipe}: {len(cutbelow)} cutbelow, {len(cutabove)} cutabove')
        for t in horizon:
            for n, c in enumerate(cutbelow):
                milp.addConstr(hvar[i, t] - hvar[j, t] >= c[1] * qvar[(i, j), t] + c[0], name=f'hpl{n}({i},{j},{t})')
            for n, c in enumerate(cutabove):
                milp.addConstr(hvar[i, t] - hvar[j, t] <= c[1] * qvar[(i, j), t] + c[0], name=f'hpu{n}({i},{j},{t})')

    # ACTIVITY (PUMPS)
    for a, pump in inst.pumps.items():
        for t in horizon:
            # !!! original code: integer round ???
            milp.addConstr(qvar[a, t] >= svar[a, t] * pump.qmin)
            milp.addConstr(qvar[a, t] <= svar[a, t] * pump.qmax)

    # CONVEXIFICATION OF HEAD-FLOW (PUMPS)
    for (i, j), pump in inst.pumps.items():
        cutbelow, cutabove = oa.pumpcuts(pump.qmin, pump.qmax, pump.hgain, '(i, j)', epsilon)
        for t in horizon:
            for n, c in enumerate(cutbelow):
                milp.addConstr(hvar[j, t] - hvar[i, t] >= c[1] * qvar[(i, j), t]
                               + (c[0] - pump.offdhmin) * svar[(i, j), t] + pump.offdhmin, name=f'hkl{n}({i},{j},{t})')
            for n, c in enumerate(cutabove):
                # !!! original code: gapabove = 0 if pump.offdhmax == 1000 else pump.offdhmax - c[1] ???
                milp.addConstr(hvar[j, t] - hvar[i, t] <= c[1] * qvar[(i, j), t]
                               + (c[0] - pump.offdhmax) * svar[(i, j), t] + pump.offdhmax, name=f'hku{n}({i},{j},{t})')

    _add_pump_switching_constraints(milp, inst, svar, ivar, stopvar, nperiods, activation_config)

    # PUMP DEPENDENCIES
    sympumps = inst.symmetries
    if sympumps and activation_config.enforce_symmetric_ordering:
        for t in horizon:
            for i, pump in enumerate(sympumps[:-1]):
                milp.addConstr(ivar[pump, t] >= ivar[sympumps[i + 1], t])
                milp.addConstr(svar[pump, t] >= svar[sympumps[i + 1], t])

    if inst.dependencies:
        for t in horizon:
            for s in inst.dependencies['p1 => p0']:
                milp.addConstr(svar[s[0], t] >= svar[s[1], t])
            for s in inst.dependencies['p0 or p1']:
                milp.addConstr(svar[s[0], t] + svar[s[1], t] >= 1)
            for s in inst.dependencies['p0 <=> p1 xor p2']:
                milp.addConstr(svar[s[0], t] == svar[s[1], t] + svar[s[2], t])
            for s in inst.dependencies['p1 => not p0']:
                milp.addConstr(svar[s[0], t] + svar[s[1], t] <= 1)

    if pumpvals:
        for pump in inst.pumps:
            for t in horizon:
                v = pumpvals.get((pump, t))
                if v == 1:
                    svar[pump, t].lb = 1
                elif v == 0:
                    svar[pump, t].ub = 0

    milp.ModelSense = GRB.MINIMIZE
    milp.update()

    milp._svar = svar
    milp._ivar = ivar
    milp._stopvar = stopvar
    milp._qvar = qvar
    milp._hvar = hvar
    milp._obj = milp.getObjective()
    milp._activation_config = activation_config

    return milp


def _add_pump_switching_constraints(milp, inst, svar, ivar, stopvar, nperiods, activation_config):
    if activation_config.uses_separate_stop_budget:
        _add_epanet_bb_switching_constraints(milp, inst, svar, ivar, stopvar, nperiods, activation_config)
    else:
        _add_public_gops_switching_constraints(milp, inst, svar, ivar, nperiods, activation_config)


def _add_public_gops_switching_constraints(milp, inst, svar, ivar, nperiods, activation_config):
    sympumps = inst.symmetries
    uniquepumps = inst.pumps_without_sym()
    print('symmetries:', uniquepumps)

    def getv(vdict, pump, t):
        return gp.quicksum(vdict[a, t] for a in sympumps) if pump == 'sym' else vdict[pump, t]

    # Public GOPS/Bonvin path: hardcoded start limit, including initial status.
    for a in uniquepumps:
        rhs = activation_config.public_start_limit * len(sympumps) if a == 'sym' \
            else activation_config.public_start_limit - svar[a, 0]
        milp.addConstr(gp.quicksum(getv(ivar, a, t) for t in range(1, nperiods)) <= rhs)
        for t in range(1, nperiods):
            milp.addConstr(getv(ivar, a, t) >= getv(svar, a, t) - getv(svar, a, t - 1))
            if inst.tsduration == dt.timedelta(minutes=30) and t < inst.nperiods() - 1:
                # minimum 1 hour activity
                milp.addConstr(getv(svar, a, t + 1) + getv(svar, a, t - 1) >= getv(svar, a, t))


def _add_epanet_bb_switching_constraints(milp, inst, svar, ivar, stopvar, nperiods, activation_config):
    if activation_config.na_max not in (1, 2, 3):
        raise ValueError(f"EPANET-BB activation config requires NA_max 1, 2, or 3, got {activation_config.na_max}")

    print('activation semantics:', activation_config.semantics, 'NA_max:', activation_config.na_max)

    for a in inst.pumps:
        i, j = a
        start_terms = []
        stop_terms = []
        if not activation_config.exclude_initial_transition:
            start_terms.append(svar[a, 0])
        for t in range(1, nperiods):
            stopvar[a, t] = milp.addVar(vtype=GRB.BINARY, name=f'ok({i},{j},{t})')
            milp.addConstr(ivar[a, t] >= svar[a, t] - svar[a, t - 1], name=f'epbb_start({i},{j},{t})')
            milp.addConstr(stopvar[a, t] >= svar[a, t - 1] - svar[a, t], name=f'epbb_stop({i},{j},{t})')
            start_terms.append(ivar[a, t])
            stop_terms.append(stopvar[a, t])
        milp.addConstr(gp.quicksum(start_terms) <= activation_config.na_max, name=f'epbb_start_budget({i},{j})')
        milp.addConstr(gp.quicksum(stop_terms) <= activation_config.na_max, name=f'epbb_stop_budget({i},{j})')
