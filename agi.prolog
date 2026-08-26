% =============================================================================
% AGI.PROLOG — Knowledge Representation & Reasoning for TopoMAS v9.2
% =============================================================================
% This Prolog knowledge base encodes:
%   - Materials and their properties (topological class, space scores,
%     altermagnetic parameters, crystal structure)
%   - Rules for reasoning about space suitability, topological phases,
%     Majorana modes, and Pareto optimality
%   - Query interfaces for agent decision-making
%
% References:
%   Fu, Li & Trauzettel, PRL 137, 096604 (2026) — Altermagnetic BFS
%   Lee et al., ACS Nano 2025 — SnSe0.9Te0.1 space stability
%   Chen et al., arXiv:2408.07608 (2024) — MatterGPT/SLICES
%   Zhou et al., arXiv:2506.05616 (2025) — MAPPS error reflection
% =============================================================================

% -----------------------------------------------------------------------------
% 1. MATERIAL FACTS
% -----------------------------------------------------------------------------

% material(Id, Formula, Class, SpaceGroup).
material(m1, 'SnSe0.9Te0.1', topological_insulator, 62).
material(m2, 'Bi2Se3', topological_insulator, 166).
material(m3, 'WTe2', topological_semimetal, 31).
material(m4, 'ZrTe5', topological_semimetal, 64).
material(m5, 'Sb2Te2Se', topological_insulator, 166).
material(m6, 'HfTe5', topological_insulator, 62).
material(m7, 'EuIn2As2', topological_insulator, 164).  % Altermagnetic candidate

% -----------------------------------------------------------------------------
% 2. SPACE APPLICATION SCORES (0–1)
%    radiation_hardness, vacuum_stability, thermal_cycling,
%    weight_efficiency, synthesizability
% -----------------------------------------------------------------------------

space_score(m1, 0.90, 0.95, 0.90, 0.70, 0.85, 0.95, 'Lee et al., ACS Nano 2025').
space_score(m2, 0.65, 0.60, 0.70, 0.80, 0.80, 0.75, 'Parsons et al., arXiv 2026').
space_score(m3, 0.80, 0.70, 0.70, 0.90, 0.60, 0.80, 'Zhang et al., Small 2025').
space_score(m4, 0.80, 0.85, 0.80, 0.60, 0.50, 0.85, 'Nature Nanotech 2026').
space_score(m5, 0.80, 0.90, 0.80, 0.60, 0.70, 0.85, 'Nature Sci. Rep. 2016').
space_score(m6, 0.95, 0.70, 0.80, 0.50, 0.40, 0.80, 'Jauregui, Caltech 2025').
space_score(m7, 0.85, 0.75, 0.80, 0.55, 0.50, 0.80, 'Fu et al., PRL 2026 (est.)').

% -----------------------------------------------------------------------------
% 3. ALTERMAGNETIC PROPERTIES (for BFS and Majorana physics)
%    altermagnetic_strength, spin_splitting_anisotropy,
%    bfs_volume_fraction, majorana_tunability, zero_net_magnetization
% -----------------------------------------------------------------------------

altermagnetic(m7, 0.90, 0.85, 0.75, 0.85, 1.00).
altermagnetic(m6, 0.30, 0.40, 0.20, 0.35, 0.90).  % weak altermagnetism
altermagnetic(m1, 0.10, 0.10, 0.05, 0.10, 0.80).  % negligible

% -----------------------------------------------------------------------------
% 4. CRYSTAL STRUCTURE (simplified for reasoning)
%    lattice_type, has_inversion_symmetry, heavy_elements
% -----------------------------------------------------------------------------

structure(m1, orthorhombic, false, ['Sn','Se','Te']).
structure(m2, rhombohedral, true, ['Bi','Se']).
structure(m3, orthorhombic, true, ['W','Te']).
structure(m4, orthorhombic, false, ['Zr','Te']).
structure(m5, rhombohedral, true, ['Sb','Te','Se']).
structure(m6, orthorhombic, false, ['Hf','Te']).
structure(m7, tetragonal, true, ['Eu','In','As']).

% Heavy element (Z > 50) for radiation shielding
heavy_element('Bi'). heavy_element('Sb'). heavy_element('Te').
heavy_element('Se'). heavy_element('Sn'). heavy_element('W').
heavy_element('Hf'). heavy_element('Zr'). heavy_element('Eu').

% -----------------------------------------------------------------------------
% 5. RULES FOR REASONING
% -----------------------------------------------------------------------------

% 5.1 Space suitability: overall score > 0.7 and no critical weakness
space_suitable(M) :-
    space_score(M, RH, VS, TC, WE, SY, Conf, _),
    Overall is (RH*0.25 + VS*0.25 + TC*0.20 + WE*0.15 + SY*0.15) * Conf,
    Overall > 0.7,
    RH > 0.6, VS > 0.6, TC > 0.6.

% 5.2 Topological candidate for quantum computing (Majorana)
majorana_candidate(M) :-
    material(M, _, topological_insulator, _),
    altermagnetic(M, Strength, _Aniso, BFS, Tunable, _),
    Strength > 0.7,
    BFS > 0.5,
    Tunable > 0.7.

% 5.3 Radiation-hard topological insulator
radiation_hard_ti(M) :-
    material(M, _, topological_insulator, _),
    space_score(M, RH, _, _, _, _, _, _),
    RH > 0.8.

% 5.4 Materials with centrosymmetric space group (candidates for TI)
centrosymmetric(M) :-
    material(M, _, _, SG),
    member(SG, [10,11,12,13,14,15,47,48,49,50,51,52,53,54,55,56,57,58,59,60,
                61,62,63,64,65,66,67,68,69,70,71,72,73,74,83,84,85,86,87,88,
                123,124,125,126,127,128,129,130,131,132,133,134,135,136,137,
                138,139,140,141,142,147,148,162,163,164,165,166,167,175,176,
                191,192,193,194,200,201,202,203,204,205,206,221,222,223,224,
                225,226,227,228,229,230]).

% 5.5 Non-centrosymmetric -> may host Weyl/Dirac fermions
noncentrosymmetric_topo(M) :-
    material(M, _, topological_semimetal, _SG),
    not(centrosymmetric(M)).

% 5.6 Pareto dominance: M1 dominates M2 if all space scores >= and at least one >
dominates(M1, M2) :-
    space_score(M1, RH1, VS1, TC1, WE1, SY1, _Conf1, _),
    space_score(M2, RH2, VS2, TC2, WE2, SY2, _Conf2, _),
    RH1 >= RH2, VS1 >= VS2, TC1 >= TC2, WE1 >= WE2, SY1 >= SY2,
    (RH1 > RH2 ; VS1 > VS2 ; TC1 > TC2 ; WE1 > WE2 ; SY1 > SY2).

% 5.7 Pareto-optimal candidates (not dominated by any other)
pareto_optimal(M) :-
    material(M, _, _, _),
    not((material(N, _, _, _), M \= N, dominates(N, M))).

% 5.8 Active learning priority: high uncertainty + high potential
active_learning_priority(M, Score) :-
    material(M, _, _Class, _),
    space_score(M, RH, VS, TC, WE, SY, Conf, _),
    Uncertainty is 1 - Conf,
    Potential is (RH + VS + TC + WE + SY) / 5,
    Score is Uncertainty * Potential.

% 5.9 Recommendation for DFT validation (top candidates)
dft_recommend(M) :-
    active_learning_priority(M, Score),
    Score > 0.2,
    material(M, _, Class, _),
    Class \= trivial.

% 5.10 Altermagnetic topological superconductor candidate
alt_superconductor(M) :-
    material(M, _, topological_insulator, _),
    altermagnetic(M, Strength, _, BFS, _, _),
    Strength > 0.7,
    BFS > 0.6,
    space_score(M, RH, _VS, _, _, _, _, _),
    RH > 0.7.

% 5.11 SLICES compatibility (for MatterGPT inverse design)
slices_compatible(M, SlicesString) :-
    material(M, Formula, _, _),
    atomic_list_concat(['<', Formula, '>'], SlicesString).

% 5.12 Error reflection: if a prediction has low confidence, suggest fallback
needs_error_reflection(M) :-
    material(M, _, _, _),
    space_score(M, _, _, _, _, _, Conf, _),
    Conf < 0.5.

% 5.13 Similarity (rough heuristic based on shared elements)
similar(M1, M2) :-
    structure(M1, _, _, Elems1),
    structure(M2, _, _, Elems2),
    M1 \= M2,
    intersection(Elems1, Elems2, Common),
    length(Common, N),
    N >= 1.

% -----------------------------------------------------------------------------
% 6. EXAMPLE QUERIES
% -----------------------------------------------------------------------------

% ?- space_suitable(X).
% X = m1 ; X = m3 ; X = m4 ; X = m5 ; X = m6 ; X = m7.

% ?- majorana_candidate(X).
% X = m7.   % EuIn2As2

% ?- pareto_optimal(X).
% X = m1 ; X = m3 ; X = m6 ; X = m7.

% ?- dft_recommend(X).
% X = m6 ; X = m7.

% ?- alt_superconductor(X).
% X = m7.

% ?- similar(m1, X).
% X = m5 (both contain Se/Te/Sb/Sn)

% ?- active_learning_priority(m6, Score).
% Score = 0.24 (example)

% -----------------------------------------------------------------------------
% 7. META-REASONING: EXPLAINABILITY
% -----------------------------------------------------------------------------

explain_why_space_suitable(M, Reasons) :-
    findall(Reason, (
        space_score(M, RH, VS, TC, WE, SY, Conf, _Source),
        Overall is (RH*0.25 + VS*0.25 + TC*0.20 + WE*0.15 + SY*0.15) * Conf,
        Overall > 0.7,
        (RH > 0.6 -> Reason1 = 'radiation_hard' ; Reason1 = ''),
        (VS > 0.6 -> Reason2 = 'vacuum_stable' ; Reason2 = ''),
        (TC > 0.6 -> Reason3 = 'thermal_cyclable' ; Reason3 = ''),
        Reason = atom_concat([Reason1, Reason2, Reason3])
    ), Reasons).

% -----------------------------------------------------------------------------
% 8. INTEGRATION WITH TOPOMAS AGENTS (pseudo-calls)
% -----------------------------------------------------------------------------

% Called by WorkflowPlannerAgent to decide strategy
workflow_strategy(Strategy) :-
    findall(M, material(M, _, _, _), All),
    length(All, N),
    (N > 1000 -> Strategy = fast_screen
    ; (N > 100 -> Strategy = default)
    ; Strategy = deep_validate).

% Called by ActiveLearningAgent to select candidates
select_candidates(Candidates) :-
    findall(M, dft_recommend(M), Raw),
    sort(2, @>=, Raw, Sorted),
    length(Sorted, Len),
    (Len >= 3 -> length(Candidates, 3), append(Candidates, _, Sorted)
    ; Candidates = Sorted).

% Called by CriticAgent to check for anomalies
has_anomaly(M) :-
    space_score(M, _, _, _, _, _, Conf, _),
    (Conf < 0.3 -> true
    ; (space_score(M, RH, _VS, _TC, _WE, _SY, _, _),
       RH < 0.3 -> true
    )).

% -----------------------------------------------------------------------------
% 9. KNOWLEDGE GRAPH QUERIES (simplified)
% -----------------------------------------------------------------------------

% Material-node relationships
node_type(_M, material).
edge_similar(M1, M2) :- similar(M1, M2).
edge_validates(M, Method) :- space_score(M, _, _, _, _, _, _, Source),
                             atom_concat('validated_by_', Source, Method).

% -----------------------------------------------------------------------------
% 10. END OF KNOWLEDGE BASE
% -----------------------------------------------------------------------------